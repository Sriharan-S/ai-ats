from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone

import pdfplumber
from docx import Document as DocxDocument
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

# ML pipeline
from ml.feature_engineering import build_feature_vector, extract_skills_from_text
from ml.pipeline import MODEL_PATH, load_pipeline, read_meta
from ml.recommender import generate_recommendations
from services.platforms import (
    get_codeforces_data,
    get_github_data,
    get_leetcode_data,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIST = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend", "dist"))

app = Flask(__name__, static_folder=None)

load_dotenv()

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("UPLOAD_MAX_MB", "10")) * 1024 * 1024
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

logging.basicConfig(level=logging.INFO)

# Load ML pipeline + metadata at startup
ats_pipeline = None
model_meta: dict = {}
try:
    if os.path.exists(MODEL_PATH):
        ats_pipeline = load_pipeline()
        model_meta = read_meta()
        app.logger.info(
            "ML pipeline loaded (model_version=%s, feature_version=%s).",
            model_meta.get("model_version"),
            model_meta.get("feature_version"),
        )
    else:
        app.logger.warning("Model not found. Run 'python -m ml.train_model' first.")
except Exception as exc:  # noqa: BLE001 — surface but don't crash the API server
    app.logger.warning("Failed to load ML pipeline: %s", exc)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _structured_error(code: str, message: str, *, details: dict | None = None, status: int = 400):
    payload = {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        }
    }
    return jsonify(payload), status


def _http_status_for_fetch(status: str) -> int:
    if status == "success":
        return 200
    if status == "not_found":
        return 404
    if status in ("rate_limited", "timeout"):
        return 503
    if status == "unauthorized":
        return 401
    return 200  # silent partial success — the body still contains fetch_status


def extract_resume_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        try:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip()
        except Exception as exc:  # noqa: BLE001
            app.logger.info("PDF extraction error: %s", exc)
            return ""
    if ext == ".docx":
        try:
            doc = DocxDocument(file_path)
            return "\n".join(p.text for p in doc.paragraphs).strip()
        except Exception as exc:  # noqa: BLE001
            app.logger.info("DOCX extraction error: %s", exc)
            return ""
    return ""


def is_allowed_resume(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in {".pdf", ".docx"}


def save_temp_resume(file_storage) -> str:
    original_name = secure_filename(file_storage.filename or "")
    ext = os.path.splitext(original_name)[1].lower()
    temp_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], temp_name)
    file_storage.save(file_path)
    return file_path


def load_roadmap_data(topic: str = "") -> dict:
    roadmap_path = os.path.join(BASE_DIR, "roadmap-content", f"{topic}.json")
    with open(roadmap_path, "r", encoding="utf-8") as fp:
        return json.load(fp)


# ------------------------------------------------------------------
# CORS
# ------------------------------------------------------------------


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = os.getenv(
        "CORS_ALLOWED_ORIGIN", "http://localhost:5173"
    )
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


# ------------------------------------------------------------------
# Health
# ------------------------------------------------------------------


@app.route("/api/health")
def api_health():
    return jsonify(
        {
            "status": "ok",
            "model_loaded": ats_pipeline is not None,
            "model_version": model_meta.get("model_version"),
            "feature_version": model_meta.get("feature_version"),
            "dataset_version": model_meta.get("dataset_version"),
            "feature_count": model_meta.get("feature_count"),
            "trained_at": model_meta.get("trained_at"),
        }
    )


# ------------------------------------------------------------------
# Roadmaps
# ------------------------------------------------------------------


@app.route("/api/roadmaps")
def api_roadmaps():
    roadmap_dir = os.path.join(BASE_DIR, "roadmap-content")
    role_keywords = {
        "frontend", "backend", "devops", "full-stack", "data-analyst",
        "android", "ios", "blockchain", "qa", "software-architect",
        "cyber-security", "ux-design", "game-developer", "mlops",
        "ai-engineer", "ai-data-scientist", "engineering-manager",
        "product-manager", "technical-writer", "devrel",
    }
    roadmaps = []

    for filename in sorted(os.listdir(roadmap_dir)):
        if not filename.endswith(".json"):
            continue
        slug = filename[:-5]
        try:
            data = load_roadmap_data(slug)
        except Exception as exc:  # noqa: BLE001
            app.logger.info("Skipping unreadable roadmap %s: %s", slug, exc)
            data = {}

        topics = data.get("nodes") or data.get("topics") or data.get("items")
        if topics is None and isinstance(data, dict):
            topics = data
        if topics is None:
            topics = []
        topic_count = len(topics) if isinstance(topics, (list, dict)) else 0

        roadmaps.append(
            {
                "slug": slug,
                "name": slug.replace("-", " ").title(),
                "category": "Role Based" if slug in role_keywords else "Skill Based",
                "topicsCount": topic_count,
                "description": f"Curated learning roadmap for {slug.replace('-', ' ')}.",
            }
        )
    return jsonify(roadmaps)


@app.route("/api/roadmaps/<path:slug>")
def api_roadmap_detail(slug):
    try:
        data = load_roadmap_data(slug)
    except FileNotFoundError:
        return _structured_error("ROADMAP_NOT_FOUND", "Roadmap not found.", status=404)

    raw_topics = data.get("nodes") or data.get("topics") or data.get("items")
    if raw_topics is None and isinstance(data, dict):
        raw_topics = data
    if raw_topics is None:
        raw_topics = []

    if isinstance(raw_topics, dict):
        iterable = raw_topics.values()
    elif isinstance(raw_topics, list):
        iterable = raw_topics
    else:
        iterable = []

    topics = []
    for index, item in enumerate(iterable, start=1):
        if not isinstance(item, dict):
            continue
        title = item.get("title") or item.get("label") or item.get("name") or f"Topic {index}"
        description = item.get("description") or item.get("content") or ""
        links = item.get("links") or item.get("resources") or []
        resources = []
        if isinstance(links, list):
            for link in links:
                if isinstance(link, dict):
                    resources.append(
                        {
                            "title": link.get("title")
                            or link.get("label")
                            or link.get("url")
                            or "Resource",
                            "url": link.get("url") or link.get("href") or "#",
                            "type": link.get("type") or "resource",
                        }
                    )
        topics.append(
            {
                "id": index,
                "title": title,
                "status": "not-started",
                "description": description,
                "resources": resources,
            }
        )

    return jsonify(
        {
            "slug": slug,
            "title": slug.replace("-", " ").title(),
            "summary": f"A curated learning path for {slug.replace('-', ' ')}.",
            "topics": topics,
        }
    )


# ------------------------------------------------------------------
# Track endpoints
# ------------------------------------------------------------------


@app.route("/api/track/github/<username>")
def api_track_github(username):
    data = get_github_data(username)
    return jsonify(data), _http_status_for_fetch(data.get("fetch_status", "error"))


@app.route("/api/track/leetcode/<username>")
def api_track_leetcode(username):
    data = get_leetcode_data(username)
    return jsonify(data), _http_status_for_fetch(data.get("fetch_status", "error"))


@app.route("/api/track/codeforces/<username>")
def api_track_codeforces(username):
    data = get_codeforces_data(username)
    return jsonify(data), _http_status_for_fetch(data.get("fetch_status", "error"))


@app.route("/api/profile", methods=["POST"])
def api_profile():
    data = request.json or {}
    out: dict = {}
    status_map: dict = {}

    if data.get("github"):
        github_data = get_github_data(data["github"])
        out["github"] = github_data
        status_map["github"] = github_data.get("fetch_status", "error")
    else:
        status_map["github"] = "not_requested"

    if data.get("leetcode"):
        leetcode_data = get_leetcode_data(data["leetcode"])
        out["leetcode"] = leetcode_data
        status_map["leetcode"] = leetcode_data.get("fetch_status", "error")
    else:
        status_map["leetcode"] = "not_requested"

    if data.get("codeforces"):
        cf_data = get_codeforces_data(data["codeforces"])
        out["codeforces"] = cf_data
        status_map["codeforces"] = cf_data.get("fetch_status", "error")
    else:
        status_map["codeforces"] = "not_requested"

    return jsonify({"data": out, "status": status_map, "fetched_at": _now_iso()})


@app.route("/api/track/github/<username>", methods=["OPTIONS"])
@app.route("/api/track/leetcode/<username>", methods=["OPTIONS"])
@app.route("/api/track/codeforces/<username>", methods=["OPTIONS"])
@app.route("/api/profile", methods=["OPTIONS"])
@app.route("/api/ats-analyze", methods=["OPTIONS"])
@app.route("/api/roadmaps", methods=["OPTIONS"])
@app.route("/api/roadmaps/<path:slug>", methods=["OPTIONS"])
def api_options(**_kwargs):
    return ("", 204)


# ------------------------------------------------------------------
# ATS analysis
# ------------------------------------------------------------------


def _empty_platform_payload(platform: str) -> dict:
    if platform == "github":
        return {"total_commits": 0, "total_pull_requests": 0, "total_repos": 0,
                "total_languages": 0, "languages": [], "language_stats": {},
                "commit_timestamps": [], "repos": []}
    if platform == "leetcode":
        return {"solved": 0, "easy": 0, "medium": 0, "hard": 0,
                "ranking": 0, "total_languages": 0, "recent_submissions": []}
    return {"rating": 0, "max_rating": 0, "rank": "unrated", "max_rank": "unrated",
            "contests": 0, "contest_history": [], "recent_submissions": [],
            "avg_problem_rating": 0.0}


@app.route("/api/ats-analyze", methods=["POST"])
def api_ats_analyze():
    if ats_pipeline is None:
        return _structured_error(
            "MODEL_NOT_LOADED",
            "ML model not loaded. Train the model first with `python -m ml.train_model`.",
            status=503,
        )

    if "resume" not in request.files:
        return _structured_error("RESUME_REQUIRED", "No resume file provided.", status=400)

    file = request.files["resume"]
    job_description = request.form.get("job_description", "").strip()
    github_user = request.form.get("github_username", "").strip()
    leetcode_user = request.form.get("leetcode_username", "").strip()
    codeforces_user = request.form.get("codeforces_username", "").strip()

    if not file or file.filename == "":
        return _structured_error("RESUME_FILE_EMPTY", "No file selected.", status=400)
    if not job_description:
        return _structured_error(
            "JOB_DESCRIPTION_REQUIRED", "Job description cannot be empty.", status=400
        )
    if not is_allowed_resume(file.filename):
        return _structured_error(
            "RESUME_FORMAT_UNSUPPORTED",
            "Unsupported file format. Please upload a PDF or DOCX.",
            status=415,
        )

    file_path = None
    analysis_id = uuid.uuid4().hex
    try:
        file_path = save_temp_resume(file)
        resume_text = extract_resume_text(file_path)
        if not resume_text:
            return _structured_error(
                "RESUME_PARSE_FAILED",
                "Could not extract readable text from this resume.",
                status=400,
            )

        # Platform fetches: real fetch_status flows through to features.
        platform_status = {
            "github": "not_requested",
            "leetcode": "not_requested",
            "codeforces": "not_requested",
        }

        if github_user:
            github_data = get_github_data(github_user)
            platform_status["github"] = github_data.get("fetch_status", "error")
        else:
            github_data = _empty_platform_payload("github")

        if leetcode_user:
            leetcode_data = get_leetcode_data(leetcode_user)
            platform_status["leetcode"] = leetcode_data.get("fetch_status", "error")
        else:
            leetcode_data = _empty_platform_payload("leetcode")

        if codeforces_user:
            codeforces_data = get_codeforces_data(codeforces_user)
            platform_status["codeforces"] = codeforces_data.get("fetch_status", "error")
        else:
            codeforces_data = _empty_platform_payload("codeforces")

        features = build_feature_vector(
            resume_text,
            job_description,
            github_data,
            leetcode_data,
            codeforces_data,
            fetch_status=platform_status,
        )

        explanation = ats_pipeline.explain(features)

        resume_skills = set(extract_skills_from_text(resume_text))
        jd_skills = set(extract_skills_from_text(job_description))
        missing_keywords = sorted(jd_skills - resume_skills)

        recommendations = generate_recommendations(explanation, missing_keywords)

        return jsonify(
            {
                "analysis_id": analysis_id,
                "model_version": model_meta.get("model_version"),
                "feature_version": model_meta.get("feature_version"),
                "score": explanation["score"],
                "shap_values": explanation["shap_values"],
                "top_positive": explanation["top_positive"],
                "top_negative": explanation["top_negative"],
                "missing_keywords": missing_keywords,
                "recommendations": recommendations,
                "platform_status": platform_status,
                "platform_data": {
                    "github": {
                        "total_commits": github_data.get("total_commits", 0),
                        "total_repos": github_data.get("total_repos", 0),
                        "languages": github_data.get("languages", []),
                        "fetch_status": platform_status["github"],
                    },
                    "leetcode": {
                        "solved": leetcode_data.get("solved", 0),
                        "ranking": leetcode_data.get("ranking", 0),
                        "fetch_status": platform_status["leetcode"],
                    },
                    "codeforces": {
                        "rating": codeforces_data.get("rating", 0),
                        "avg_problem_rating": codeforces_data.get("avg_problem_rating", 0),
                        "fetch_status": platform_status["codeforces"],
                    },
                },
            }
        )

    except Exception as exc:  # noqa: BLE001
        app.logger.exception("ATS analysis failed: %s", exc)
        return _structured_error(
            "ATS_ANALYSIS_FAILED",
            f"Analysis failed: {exc}",
            details={"analysis_id": analysis_id},
            status=500,
        )
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as exc:
                app.logger.warning("Failed to delete temporary resume %s: %s", file_path, exc)


# ------------------------------------------------------------------
# Frontend
# ------------------------------------------------------------------


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path.startswith("api/"):
        return _structured_error("API_NOT_FOUND", "API route not found.", status=404)

    if path and os.path.exists(os.path.join(FRONTEND_DIST, path)):
        return send_from_directory(FRONTEND_DIST, path)

    index_path = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.exists(index_path):
        return send_from_directory(FRONTEND_DIST, "index.html")

    return jsonify(
        {
            "status": "frontend_not_built",
            "message": "Run the TypeScript frontend with `npm run dev` or build it with `npm run build`.",
        }
    ), 404


if __name__ == "__main__":
    debug_enabled = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(
        debug=debug_enabled,
        port=int(os.getenv("PORT", "5001")),
        host=os.getenv("HOST", "0.0.0.0"),
    )
