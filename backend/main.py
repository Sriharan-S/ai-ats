from flask import Flask, jsonify, request, send_from_directory
import requests as http_requests
import json
from dotenv import load_dotenv
import os
import uuid
import pdfplumber
from docx import Document as DocxDocument
from werkzeug.utils import secure_filename

# ML Pipeline imports
from ml.pipeline import ATSPipeline, load_pipeline, MODEL_PATH
from ml.feature_engineering import build_feature_vector, extract_skills_from_text
from ml.recommender import generate_recommendations

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIST = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend", "dist"))

app = Flask(__name__, static_folder=None)

load_dotenv()

# Environment variables
GITHUB_PAT = os.getenv("GITHUB_PAT")
HEADERS_GITHUB = {"Accept": "application/vnd.github.v3+json"}
if GITHUB_PAT:
    HEADERS_GITHUB["Authorization"] = f"Bearer {GITHUB_PAT}"
GITHUB_API_URL = "https://api.github.com"

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv("UPLOAD_MAX_MB", "10")) * 1024 * 1024
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load ML pipeline
ats_pipeline = None
try:
    if os.path.exists(MODEL_PATH):
        ats_pipeline = load_pipeline()
        app.logger.info("ML pipeline loaded successfully.")
    else:
        app.logger.warning("Model not found. Run 'python -m ml.train_model' first.")
except Exception as e:
    app.logger.warning("Failed to load ML pipeline: %s", e)


# ============================================================
# API INTEGRATION: GitHub
# ============================================================

def _github_request(url, timeout=10):
    """Make a GitHub API request, trying authenticated first, then unauthenticated."""
    # Try with auth header
    try:
        resp = http_requests.get(url, headers=HEADERS_GITHUB, timeout=timeout)
        if resp.status_code == 200:
            return resp
        app.logger.info("GitHub authenticated request failed with %s: %s", resp.status_code, url)
    except Exception as e:
        app.logger.info("GitHub authenticated request error for %s: %s", url, e)

    # Fallback: unauthenticated
    try:
        resp = http_requests.get(url, timeout=timeout)
        if resp.status_code == 200:
            return resp
        app.logger.info("GitHub unauthenticated request failed with %s: %s", resp.status_code, url)
    except Exception as e:
        app.logger.info("GitHub unauthenticated request error for %s: %s", url, e)

    return None


def get_github_data(username):
    """Fetch comprehensive GitHub data for a user."""
    result = {
        'total_commits': 0,
        'total_pull_requests': 0,
        'total_repos': 0,
        'total_languages': 0,
        'languages': [],
        'language_stats': {},
        'commit_timestamps': [],
        'repos': [],
    }

    try:
        app.logger.info("Fetching GitHub data for %s", username)

        # Fetch repos
        repos_url = f"{GITHUB_API_URL}/users/{username}/repos?per_page=100&sort=updated"
        resp = _github_request(repos_url)
        if resp is None:
            app.logger.info("Could not fetch GitHub repos for %s", username)
            return result

        repos = resp.json()
        result['total_repos'] = len(repos)
        result['repos'] = [r['name'] for r in repos[:20]]
        app.logger.info("Found %s GitHub repos for %s", len(repos), username)

        # Aggregate languages (limit to top 10 repos to avoid rate limits)
        lang_set = set()
        lang_bytes = {}
        for repo in repos[:10]:
            if repo.get('language'):
                lang_set.add(repo['language'])
            if repo.get('languages_url'):
                try:
                    lr = _github_request(repo['languages_url'], timeout=5)
                    if lr is not None:
                        for lang, bytes_count in lr.json().items():
                            lang_set.add(lang)
                            lang_bytes[lang] = lang_bytes.get(lang, 0) + bytes_count
                except Exception as e:
                    app.logger.info("Skipping GitHub language stats for %s: %s", repo.get('name', 'unknown'), e)

        result['languages'] = list(lang_set)
        result['total_languages'] = len(lang_set)

        # Sort languages by usage
        sorted_langs = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)
        total_bytes = sum(v for _, v in sorted_langs) or 1
        result['language_stats'] = {
            lang: round(bytes_count / total_bytes * 100, 1)
            for lang, bytes_count in sorted_langs[:10]
        }

        # Fetch events (commits, PRs)
        events_url = f"{GITHUB_API_URL}/users/{username}/events?per_page=100"
        resp = _github_request(events_url)
        if resp is not None:
            events = resp.json()
            for event in events:
                if event['type'] == 'PushEvent':
                    commits = event.get('payload', {}).get('commits', [])
                    result['total_commits'] += len(commits)
                    result['commit_timestamps'].append(event.get('created_at', ''))
                elif event['type'] == 'PullRequestEvent':
                    result['total_pull_requests'] += 1

        # If we got very few commits from events, estimate from repos
        if result['total_commits'] < 10:
            result['total_commits'] = max(result['total_commits'], len(repos) * 8)

        app.logger.info(
            "GitHub data complete for %s: %s commits, %s repos, %s languages",
            username,
            result['total_commits'],
            result['total_repos'],
            result['total_languages'],
        )

    except Exception as e:
        app.logger.exception("GitHub data error for %s: %s", username, e)

    return result


# ============================================================
# API INTEGRATION: LeetCode
# ============================================================

def get_leetcode_data(username):
    """Fetch LeetCode stats via the public API."""
    result = {
        'solved': 0,
        'easy': 0,
        'medium': 0,
        'hard': 0,
        'ranking': 0,
        'total_languages': 0,
        'recent_submissions': [],
    }

    try:
        # Method 1: GraphQL API
        graphql_url = "https://leetcode.com/graphql"
        query = {
            "query": """
            query getUserProfile($username: String!) {
                matchedUser(username: $username) {
                    submitStats: submitStatsGlobal {
                        acSubmissionNum {
                            difficulty
                            count
                        }
                    }
                    profile {
                        ranking
                    }
                    languageProblemCount {
                        languageName
                        problemsSolved
                    }
                }
            }
            """,
            "variables": {"username": username}
        }

        resp = http_requests.post(graphql_url, json=query, timeout=10)
        if resp.status_code == 200:
            data = resp.json().get('data', {}).get('matchedUser', {})
            if data:
                # Parse solved problems by difficulty
                stats = data.get('submitStats', {}).get('acSubmissionNum', [])
                for stat in stats:
                    diff = stat.get('difficulty', '').lower()
                    count = stat.get('count', 0)
                    if diff == 'easy':
                        result['easy'] = count
                    elif diff == 'medium':
                        result['medium'] = count
                    elif diff == 'hard':
                        result['hard'] = count
                    elif diff == 'all':
                        result['solved'] = count

                if result['solved'] == 0:
                    result['solved'] = result['easy'] + result['medium'] + result['hard']

                # Ranking
                result['ranking'] = data.get('profile', {}).get('ranking', 0)

                # Languages
                lang_data = data.get('languageProblemCount', [])
                result['total_languages'] = len(lang_data)

                return result

        # Method 2: Fallback to public stats endpoint
        stats_url = f"https://leetcode-stats-api.herokuapp.com/{username}"
        resp = http_requests.get(stats_url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            result['solved'] = data.get('totalSolved', 0)
            result['easy'] = data.get('easySolved', 0)
            result['medium'] = data.get('mediumSolved', 0)
            result['hard'] = data.get('hardSolved', 0)
            result['ranking'] = data.get('ranking', 0)

    except Exception as e:
        app.logger.info("LeetCode API error for %s: %s", username, e)

    return result


# ============================================================
# API INTEGRATION: Codeforces
# ============================================================

def get_codeforces_data(username):
    """Fetch Codeforces stats via the public API."""
    result = {
        'rating': 0,
        'max_rating': 0,
        'rank': 'unrated',
        'max_rank': 'unrated',
        'contests': 0,
        'contest_history': [],
    }

    try:
        # User info
        info_url = f"https://codeforces.com/api/user.info?handles={username}"
        resp = http_requests.get(info_url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('status') == 'OK' and data.get('result'):
                user = data['result'][0]
                result['rating'] = user.get('rating', 0)
                result['max_rating'] = user.get('maxRating', 0)
                result['rank'] = user.get('rank', 'unrated')
                result['max_rank'] = user.get('maxRank', 'unrated')

        # Contest history
        rating_url = f"https://codeforces.com/api/user.rating?handle={username}"
        resp = http_requests.get(rating_url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('status') == 'OK':
                contests = data.get('result', [])
                result['contests'] = len(contests)
                # Last 12 contest ratings for chart
                result['contest_history'] = [
                    {
                        'name': c.get('contestName', ''),
                        'rating': c.get('newRating', 0),
                        'rank': c.get('rank', 0),
                    }
                    for c in contests[-12:]
                ]

    except Exception as e:
        app.logger.info("Codeforces API error for %s: %s", username, e)

    return result


# ============================================================
# Resume Text Extraction
# ============================================================

def extract_resume_text(file_path):
    """Extract text from PDF or DOCX resume."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.pdf':
        try:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip()
        except Exception as e:
            app.logger.info("PDF extraction error: %s", e)
            return ""

    elif ext == '.docx':
        try:
            doc = DocxDocument(file_path)
            text = "\n".join([p.text for p in doc.paragraphs])
            return text.strip()
        except Exception as e:
            app.logger.info("DOCX extraction error: %s", e)
            return ""

    return ""


def is_allowed_resume(filename):
    return os.path.splitext(filename)[1].lower() in {".pdf", ".docx"}


def save_temp_resume(file_storage):
    original_name = secure_filename(file_storage.filename or "")
    ext = os.path.splitext(original_name)[1].lower()
    temp_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], temp_name)
    file_storage.save(file_path)
    return file_path


def load_data(topic=""):
    roadmap_path = os.path.join(BASE_DIR, "roadmap-content", f"{topic}.json")
    with open(roadmap_path, "r", encoding="utf-8") as file:
        return json.load(file)


# ============================================================
# API ENDPOINTS
# ============================================================

@app.after_request
def add_cors_headers(response):
    """Allow the local Vite frontend to call the Flask API during development."""
    response.headers["Access-Control-Allow-Origin"] = os.getenv("CORS_ALLOWED_ORIGIN", "http://localhost:5173")
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


@app.route('/api/health')
def api_health():
    return jsonify({
        "status": "ok",
        "model_loaded": ats_pipeline is not None,
    })


@app.route('/api/roadmaps')
def api_roadmaps():
    """List available roadmap JSON files for the TypeScript frontend."""
    roadmap_dir = os.path.join(BASE_DIR, "roadmap-content")
    roadmaps = []

    for filename in sorted(os.listdir(roadmap_dir)):
        if not filename.endswith(".json"):
            continue

        slug = filename[:-5]
        try:
            data = load_data(slug)
        except Exception as e:
            app.logger.info("Skipping unreadable roadmap %s: %s", slug, e)
            data = {}

        category = "Skill Based"
        role_keywords = {
            "frontend", "backend", "devops", "full-stack", "data-analyst",
            "android", "ios", "blockchain", "qa", "software-architect",
            "cyber-security", "ux-design", "game-developer", "mlops",
            "ai-engineer", "ai-data-scientist", "engineering-manager",
            "product-manager", "technical-writer", "devrel"
        }
        if slug in role_keywords:
            category = "Role Based"

        topics = data.get("nodes") or data.get("topics") or data.get("items")
        if topics is None and isinstance(data, dict):
            topics = data
        if topics is None:
            topics = []
        if isinstance(topics, dict):
            topic_count = len(topics)
        elif isinstance(topics, list):
            topic_count = len(topics)
        else:
            topic_count = 0

        roadmaps.append({
            "slug": slug,
            "name": slug.replace("-", " ").title(),
            "category": category,
            "topicsCount": topic_count,
            "description": f"Curated learning roadmap for {slug.replace('-', ' ')}.",
        })

    return jsonify(roadmaps)


@app.route('/api/roadmaps/<path:slug>')
def api_roadmap_detail(slug):
    """Return a normalized roadmap detail shape for the TypeScript frontend."""
    try:
        data = load_data(slug)
    except FileNotFoundError:
        return jsonify({"error": "Roadmap not found."}), 404

    raw_topics = data.get("nodes") or data.get("topics") or data.get("items")
    if raw_topics is None and isinstance(data, dict):
        raw_topics = data
    if raw_topics is None:
        raw_topics = []
    topics = []

    if isinstance(raw_topics, dict):
        iterable = raw_topics.values()
    elif isinstance(raw_topics, list):
        iterable = raw_topics
    else:
        iterable = []

    for index, item in enumerate(iterable, start=1):
        if not isinstance(item, dict):
            continue

        title = (
            item.get("title")
            or item.get("label")
            or item.get("name")
            or f"Topic {index}"
        )
        description = item.get("description") or item.get("content") or ""
        links = item.get("links") or item.get("resources") or []
        resources = []

        if isinstance(links, list):
            for link in links:
                if isinstance(link, dict):
                    resources.append({
                        "title": link.get("title") or link.get("label") or link.get("url") or "Resource",
                        "url": link.get("url") or link.get("href") or "#",
                        "type": link.get("type") or "resource",
                    })

        topics.append({
            "id": index,
            "title": title,
            "status": "not-started",
            "description": description,
            "resources": resources,
        })

    return jsonify({
        "slug": slug,
        "title": slug.replace("-", " ").title(),
        "summary": f"A curated learning path for {slug.replace('-', ' ')}.",
        "topics": topics,
    })

@app.route('/api/track/github/<username>')
def api_track_github(username):
    """Fetch GitHub data for a user."""
    data = get_github_data(username)
    return jsonify(data)


@app.route('/api/track/github/<username>', methods=['OPTIONS'])
@app.route('/api/track/leetcode/<username>', methods=['OPTIONS'])
@app.route('/api/track/codeforces/<username>', methods=['OPTIONS'])
@app.route('/api/profile', methods=['OPTIONS'])
@app.route('/api/ats-analyze', methods=['OPTIONS'])
@app.route('/api/roadmaps', methods=['OPTIONS'])
@app.route('/api/roadmaps/<path:slug>', methods=['OPTIONS'])
def api_options(**kwargs):
    return ("", 204)


@app.route('/api/track/leetcode/<username>')
def api_track_leetcode(username):
    """Fetch LeetCode data for a user."""
    data = get_leetcode_data(username)
    return jsonify(data)


@app.route('/api/track/codeforces/<username>')
def api_track_codeforces(username):
    """Fetch Codeforces data for a user."""
    data = get_codeforces_data(username)
    return jsonify(data)


@app.route('/api/profile', methods=['POST'])
def api_profile():
    """Fetch complete profile data for all platforms."""
    data = request.json or {}
    github_user = data.get('github', '')
    leetcode_user = data.get('leetcode', '')
    codeforces_user = data.get('codeforces', '')

    result = {}
    if github_user:
        result['github'] = get_github_data(github_user)
    if leetcode_user:
        result['leetcode'] = get_leetcode_data(leetcode_user)
    if codeforces_user:
        result['codeforces'] = get_codeforces_data(codeforces_user)

    return jsonify(result)


@app.route('/api/ats-analyze', methods=['POST'])
def api_ats_analyze():
    """
    ML Pipeline-based ATS analysis endpoint.

    Expects multipart form with:
      - resume: file (.pdf or .docx)
      - job_description: text
      - github_username: optional
      - leetcode_username: optional
      - codeforces_username: optional
    """
    if ats_pipeline is None:
        return jsonify({"error": "ML model not loaded. Please train the model first."}), 500

    if 'resume' not in request.files:
        return jsonify({"error": "No resume file provided."}), 400

    file = request.files['resume']
    job_description = request.form.get('job_description', '').strip()
    github_user = request.form.get('github_username', '').strip()
    leetcode_user = request.form.get('leetcode_username', '').strip()
    codeforces_user = request.form.get('codeforces_username', '').strip()

    if not file or file.filename == '':
        return jsonify({"error": "No file selected."}), 400

    if not job_description:
        return jsonify({"error": "Job description cannot be empty."}), 400

    if not is_allowed_resume(file.filename):
        return jsonify({"error": "Unsupported file format. Please upload a PDF or DOCX."}), 400

    file_path = None
    try:
        file_path = save_temp_resume(file)

        resume_text = extract_resume_text(file_path)
        if not resume_text:
            return jsonify({"error": "Could not extract text from resume."}), 400

        # Fetch platform data
        github_data = get_github_data(github_user) if github_user else {
            'total_commits': 0, 'total_pull_requests': 0, 'total_repos': 0,
            'total_languages': 0, 'languages': [], 'commit_timestamps': []
        }
        leetcode_data = get_leetcode_data(leetcode_user) if leetcode_user else {
            'solved': 0, 'easy': 0, 'medium': 0, 'hard': 0,
            'ranking': 0, 'recent_submissions': []
        }
        codeforces_data = get_codeforces_data(codeforces_user) if codeforces_user else {
            'rating': 0, 'max_rating': 0, 'contests': 0
        }

        # Build feature vector
        features = build_feature_vector(
            resume_text, job_description,
            github_data, leetcode_data, codeforces_data
        )

        # Get prediction + SHAP explanation
        explanation = ats_pipeline.explain(features)

        # Extract missing keywords for recommendations
        resume_skills = set(extract_skills_from_text(resume_text))
        jd_skills = set(extract_skills_from_text(job_description))
        missing_keywords = list(jd_skills - resume_skills)

        # Generate recommendations
        recommendations = generate_recommendations(explanation, missing_keywords)

        return jsonify({
            'score': explanation['score'],
            'shap_values': explanation['shap_values'],
            'top_positive': explanation['top_positive'],
            'top_negative': explanation['top_negative'],
            'missing_keywords': missing_keywords,
            'recommendations': recommendations,
            'platform_data': {
                'github': {
                    'total_commits': github_data.get('total_commits', 0),
                    'total_repos': github_data.get('total_repos', 0),
                    'languages': github_data.get('languages', []),
                },
                'leetcode': {
                    'solved': leetcode_data.get('solved', 0),
                    'ranking': leetcode_data.get('ranking', 0),
                },
                'codeforces': {
                    'rating': codeforces_data.get('rating', 0),
                },
            },
        })

    except Exception as e:
        app.logger.exception("ATS analysis failed: %s", e)
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                app.logger.warning("Failed to delete temporary resume %s: %s", file_path, e)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    """Serve the built TypeScript frontend in production-like Flask runs."""
    if path.startswith("api/"):
        return jsonify({"error": "API route not found."}), 404

    if path and os.path.exists(os.path.join(FRONTEND_DIST, path)):
        return send_from_directory(FRONTEND_DIST, path)

    index_path = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.exists(index_path):
        return send_from_directory(FRONTEND_DIST, "index.html")

    return jsonify({
        "status": "frontend_not_built",
        "message": "Run the TypeScript frontend with `npm run dev` or build it with `npm run build`.",
    }), 404


if __name__ == "__main__":
    debug_enabled = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(
        debug=debug_enabled,
        port=int(os.getenv("PORT", "5000")),
        host=os.getenv("HOST", "0.0.0.0"),
    )
