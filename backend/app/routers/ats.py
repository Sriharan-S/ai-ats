from __future__ import annotations

import logging
import os
import uuid
from io import BytesIO

import pdfplumber
from docx import Document as DocxDocument
from fastapi import APIRouter, File, Form, UploadFile

from ml.feature_engineering import build_feature_vector, extract_skills_from_text
from ml.recommender import generate_recommendations
from services.platforms import (
    get_codeforces_data,
    get_github_data,
    get_leetcode_data,
)

from ..errors import structured_error

router = APIRouter()
logger = logging.getLogger("aiats.ats")

_pipeline = None
_meta: dict = {}
_UPLOAD_MAX_BYTES = int(os.getenv("UPLOAD_MAX_MB", "10")) * 1024 * 1024


def _get_pipeline():
    global _pipeline, _meta
    if _pipeline is None:
        from ml.pipeline import MODEL_PATH, load_pipeline, read_meta
        if not os.path.exists(MODEL_PATH):
            return None, {}
        _pipeline = load_pipeline()
        _meta = read_meta()
        logger.info(
            "ML pipeline loaded (model_version=%s, feature_version=%s).",
            _meta.get("model_version"),
            _meta.get("feature_version"),
        )
    return _pipeline, _meta


def extract_resume_text(data: bytes, ext: str) -> str:
    buf = BytesIO(data)
    if ext == ".pdf":
        try:
            text = ""
            with pdfplumber.open(buf) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip()
        except Exception as exc:
            logger.info("PDF extraction error: %s", exc)
            return ""
    if ext == ".docx":
        try:
            doc = DocxDocument(buf)
            return "\n".join(p.text for p in doc.paragraphs).strip()
        except Exception as exc:
            logger.info("DOCX extraction error: %s", exc)
            return ""
    return ""


def _is_allowed_resume(filename: str) -> bool:
    return os.path.splitext(filename or "")[1].lower() in {".pdf", ".docx"}


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


@router.post("/api/ats-analyze")
async def ats_analyze(
    resume: UploadFile = File(default=None),
    job_description: str = Form(default=""),
    github_username: str = Form(default=""),
    leetcode_username: str = Form(default=""),
    codeforces_username: str = Form(default=""),
):
    pipeline, meta = _get_pipeline()
    if pipeline is None:
        return structured_error(
            "MODEL_NOT_LOADED",
            "ML model not loaded. Train the model first with `python -m ml.train_model`.",
            status=503,
        )

    if resume is None:
        return structured_error("RESUME_REQUIRED", "No resume file provided.", status=400)
    if not resume.filename:
        return structured_error("RESUME_FILE_EMPTY", "No file selected.", status=400)
    if not job_description.strip():
        return structured_error(
            "JOB_DESCRIPTION_REQUIRED", "Job description cannot be empty.", status=400
        )
    if not _is_allowed_resume(resume.filename):
        return structured_error(
            "RESUME_FORMAT_UNSUPPORTED",
            "Unsupported file format. Please upload a PDF or DOCX.",
            status=415,
        )

    analysis_id = uuid.uuid4().hex
    try:
        data = await resume.read()
        if len(data) > _UPLOAD_MAX_BYTES:
            return structured_error(
                "RESUME_TOO_LARGE",
                f"Resume exceeds {_UPLOAD_MAX_BYTES // (1024 * 1024)} MB limit.",
                status=413,
            )
        ext = os.path.splitext(resume.filename)[1].lower()
        resume_text = extract_resume_text(data, ext)
        if not resume_text:
            return structured_error(
                "RESUME_PARSE_FAILED",
                "Could not extract readable text from this resume.",
                status=400,
            )

        platform_status = {
            "github": "not_requested",
            "leetcode": "not_requested",
            "codeforces": "not_requested",
        }

        gh_user = github_username.strip()
        lc_user = leetcode_username.strip()
        cf_user = codeforces_username.strip()

        if gh_user:
            github_data = get_github_data(gh_user)
            platform_status["github"] = github_data.get("fetch_status", "error")
        else:
            github_data = _empty_platform_payload("github")

        if lc_user:
            leetcode_data = get_leetcode_data(lc_user)
            platform_status["leetcode"] = leetcode_data.get("fetch_status", "error")
        else:
            leetcode_data = _empty_platform_payload("leetcode")

        if cf_user:
            codeforces_data = get_codeforces_data(cf_user)
            platform_status["codeforces"] = codeforces_data.get("fetch_status", "error")
        else:
            codeforces_data = _empty_platform_payload("codeforces")

        features = build_feature_vector(
            resume_text,
            job_description.strip(),
            github_data,
            leetcode_data,
            codeforces_data,
            fetch_status=platform_status,
        )

        explanation = pipeline.explain(features)

        resume_skills = set(extract_skills_from_text(resume_text))
        jd_skills = set(extract_skills_from_text(job_description.strip()))
        missing_keywords = sorted(jd_skills - resume_skills)

        recommendations = generate_recommendations(explanation, missing_keywords)

        return {
            "analysis_id": analysis_id,
            "model_version": meta.get("model_version"),
            "feature_version": meta.get("feature_version"),
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
    except Exception as exc:
        logger.exception("ATS analysis failed: %s", exc)
        return structured_error(
            "ATS_ANALYSIS_FAILED",
            f"Analysis failed: {exc}",
            details={"analysis_id": analysis_id},
            status=500,
        )
