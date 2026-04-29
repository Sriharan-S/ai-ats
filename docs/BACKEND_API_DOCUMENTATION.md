# Backend API Documentation

## 1. Overview

The current backend is a Flask application defined in `backend/main.py`. It exposes JSON API endpoints for profile tracking, roadmap data, resume parsing, platform data collection, and ML-based ATS scoring.

The TypeScript frontend owns the user interface. Flask serves the compiled `frontend/dist` build in production-like local runs and otherwise acts as the Python API backend.

Base URL for local development:

```text
http://localhost:5000
```

## 2. Current Backend Responsibilities

- Serve the compiled TypeScript frontend when `frontend/dist` exists.
- Upload and parse PDF/DOCX resumes.
- Fetch public GitHub profile data.
- Fetch public LeetCode profile data.
- Fetch public Codeforces profile data.
- Serve roadmap JSON through API endpoints.
- Build ATS feature vectors.
- Run the ML model.
- Generate SHAP explanations.
- Generate skill-gap recommendations.

## 3. Authentication

Current state:

- No user authentication is implemented.
- GitHub API can use `GITHUB_PAT` from `.env`.

Recommended future state:

- Student login for saved assessments.
- Admin/counselor login for cohort dashboards.
- Role-based access control.
- API keys stored only on backend.
- No frontend exposure of backend-only API keys.

## 4. Environment Variables

Current variables:

| Variable | Purpose | Required |
| --- | --- | --- |
| `GITHUB_PAT` | GitHub Personal Access Token for higher rate limits | Recommended |
| `UPLOAD_MAX_MB` | Maximum resume upload size in MB | Optional, defaults to `10` |
| `CORS_ALLOWED_ORIGIN` | Frontend origin allowed in local development | Optional, defaults to `http://localhost:5173` |
| `FLASK_DEBUG` | Set to `1` for Flask debug mode | Optional, defaults to `0` |
| `HOST` | Flask bind host | Optional, defaults to `0.0.0.0` |
| `PORT` | Flask port | Optional, defaults to `5000` |

Recommended variables:

| Variable | Purpose |
| --- | --- |
| `FLASK_ENV` | Development/production mode |
| `DATABASE_URL` | PostgreSQL connection string |
| `UPLOAD_MAX_MB` | Maximum resume upload size |
| `CORS_ALLOWED_ORIGIN` | Allowed frontend origin |
| `MODEL_REGISTRY_DIR` | Model artifact directory |

## 5. Response Style

Current endpoints return either direct JSON data or:

```json
{
  "error": "Human-readable error"
}
```

Recommended standard error shape:

```json
{
  "error": {
    "code": "RESUME_PARSE_FAILED",
    "message": "Could not extract readable text from this resume.",
    "details": {}
  }
}
```

Recommended success wrapper for future APIs:

```json
{
  "data": {},
  "meta": {
    "request_id": "req_123",
    "generated_at": "2026-04-29T10:30:00Z"
  }
}
```

The current TypeScript frontend can initially consume the existing raw response shapes, then migrate to a standard wrapper later.

## 6. Page Routes

These routes currently render HTML templates.

### 6.1 Home

```http
GET /
GET /index
```

Purpose:

- Render the home page.

Current response:

- HTML page: `index.html`.

Frontend migration note:

- TypeScript frontend should own this route eventually.

### 6.2 Track Page

```http
GET /track
```

Purpose:

- Render the profile tracking page.

Current response:

- HTML page: `track.html`.

### 6.3 Learn Pages

```http
GET /learn
GET /learn/
GET /learn/<subpath>
```

Purpose:

- Render roadmap list and roadmap details.

Current response:

- `/learn` returns `learn.html`.
- `/learn/` redirects to `/learn`.
- `/learn/<subpath>` loads `roadmap-content/<subpath>.json` and renders `learnmap.html`.

Current risk:

- Invalid roadmap slugs can cause file loading errors.

Recommended future APIs:

```http
GET /api/roadmaps
GET /api/roadmaps/<slug>
```

### 6.4 ATS Page

```http
GET /ats
GET /ats/
```

Purpose:

- Render ATS assessment page.

Current response:

- HTML page: `ats.html`.

### 6.5 AI Page

```http
GET /ai
```

Purpose:

- Redirect to an external AI URL.

Current response:

- HTTP redirect to `https://dev-3000.jayakrishna.xyz`.

Recommended future state:

- Replace redirect with a native AI career coach page/API.

## 7. API Routes

## 7.1 GitHub Tracking API

```http
GET /api/track/github/<username>
```

Purpose:

- Fetch public GitHub data for a username.

Path parameters:

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `username` | string | Yes | GitHub username |

Current backend behavior:

- Calls GitHub `/users/{username}/repos`.
- Aggregates repository count.
- Reads languages from top repositories.
- Reads recent events for commits and pull requests.
- Falls back from authenticated request to unauthenticated request.
- Estimates commits if recent events return too few.

Success response:

```json
{
  "total_commits": 120,
  "total_pull_requests": 4,
  "total_repos": 12,
  "total_languages": 5,
  "languages": ["Python", "JavaScript"],
  "language_stats": {
    "Python": 60.5,
    "JavaScript": 39.5
  },
  "commit_timestamps": ["2026-04-20T12:30:00Z"],
  "repos": ["project-one", "project-two"]
}
```

Failure/current fallback response:

```json
{
  "total_commits": 0,
  "total_pull_requests": 0,
  "total_repos": 0,
  "total_languages": 0,
  "languages": [],
  "language_stats": {},
  "commit_timestamps": [],
  "repos": []
}
```

Recommended improvements:

- Return explicit `fetch_status`.
- Handle invalid username with 404.
- Add API caching.
- Add pagination for more than 100 repositories.
- Add rate-limit details.

Recommended future response addition:

```json
{
  "fetch_status": "success",
  "fetched_at": "2026-04-29T10:30:00Z"
}
```

## 7.2 LeetCode Tracking API

```http
GET /api/track/leetcode/<username>
```

Purpose:

- Fetch public LeetCode stats for a username.

Path parameters:

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `username` | string | Yes | LeetCode username |

Current backend behavior:

- First tries LeetCode GraphQL.
- Falls back to `leetcode-stats-api.herokuapp.com`.
- Returns solved problem counts and ranking.

Success response:

```json
{
  "solved": 150,
  "easy": 70,
  "medium": 65,
  "hard": 15,
  "ranking": 45000,
  "total_languages": 4,
  "recent_submissions": []
}
```

Failure/current fallback response:

```json
{
  "solved": 0,
  "easy": 0,
  "medium": 0,
  "hard": 0,
  "ranking": 0,
  "total_languages": 0,
  "recent_submissions": []
}
```

Recommended improvements:

- Return `fetch_status`.
- Avoid silently converting API failure to zeros.
- Add contest rating if available.
- Add recent submissions if available.

## 7.3 Codeforces Tracking API

```http
GET /api/track/codeforces/<username>
```

Purpose:

- Fetch public Codeforces data for a handle.

Path parameters:

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `username` | string | Yes | Codeforces handle |

Current backend behavior:

- Calls `user.info`.
- Calls `user.rating`.
- Returns rating, rank, contests, and latest contest history.

Success response:

```json
{
  "rating": 1300,
  "max_rating": 1450,
  "rank": "pupil",
  "max_rank": "specialist",
  "contests": 12,
  "contest_history": [
    {
      "name": "Codeforces Round 1000",
      "rating": 1320,
      "rank": 4321
    }
  ]
}
```

Failure/current fallback response:

```json
{
  "rating": 0,
  "max_rating": 0,
  "rank": "unrated",
  "max_rank": "unrated",
  "contests": 0,
  "contest_history": []
}
```

Recommended improvements:

- Return 404 for invalid handle.
- Add explicit status.
- Add submission/activity features in a separate endpoint or snapshot process.

## 7.4 Combined Profile API

```http
POST /api/profile
```

Purpose:

- Fetch profile data for multiple platforms in one request.

Request content type:

```text
application/json
```

Request body:

```json
{
  "github": "github_username",
  "leetcode": "leetcode_username",
  "codeforces": "codeforces_handle"
}
```

All fields are optional, but at least one should be provided by the frontend.

Success response:

```json
{
  "github": {
    "total_commits": 120,
    "total_pull_requests": 4,
    "total_repos": 12,
    "total_languages": 5,
    "languages": ["Python"],
    "language_stats": {
      "Python": 100
    },
    "commit_timestamps": [],
    "repos": ["project-one"]
  },
  "leetcode": {
    "solved": 150,
    "easy": 70,
    "medium": 65,
    "hard": 15,
    "ranking": 45000,
    "total_languages": 4,
    "recent_submissions": []
  },
  "codeforces": {
    "rating": 1300,
    "max_rating": 1450,
    "rank": "pupil",
    "max_rank": "specialist",
    "contests": 12,
    "contest_history": []
  }
}
```

Recommended frontend usage:

- Prefer this endpoint for the Track page once it is improved to return per-platform status.
- Current `track.html` fetches each platform separately.

Recommended improvements:

- Fetch platforms concurrently in backend.
- Return partial success statuses.
- Include `errors` object per platform.

Recommended future response:

```json
{
  "data": {
    "github": {},
    "leetcode": {},
    "codeforces": {}
  },
  "status": {
    "github": "success",
    "leetcode": "failed",
    "codeforces": "not_requested"
  },
  "errors": {
    "leetcode": "LeetCode API unavailable"
  }
}
```

## 7.5 Removed Legacy ATS API

The old qualitative LLM resume endpoint has been removed from the active backend. The frontend should call only the ML-based ATS endpoint documented below.

Current migration standard:

- Do not add frontend calls to removed legacy endpoints.
- Keep resume scoring and recommendation generation behind Python APIs.
- Keep API keys and model credentials out of the TypeScript bundle.
- Store uploads as temporary server files, validate extensions, enforce `UPLOAD_MAX_MB`, and delete temporary files after processing.

## 7.6 ML ATS Analysis API

```http
POST /api/ats-analyze
```

Purpose:

- Main ML-based ATS analysis endpoint.
- Parses resume, fetches optional platform data, builds features, runs model, returns SHAP explanation and recommendations.

Request content type:

```text
multipart/form-data
```

Form fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `resume` | file | Yes | PDF or DOCX resume |
| `job_description` | string | Yes | Target job description |
| `github_username` | string | No | GitHub username |
| `leetcode_username` | string | No | LeetCode username |
| `codeforces_username` | string | No | Codeforces handle |

Success response:

```json
{
  "score": 72.5,
  "shap_values": {
    "GitHub Commits": 0.12,
    "Skill-Keyword Match": -0.08
  },
  "top_positive": [
    ["GitHub Commits", 0.12],
    ["LeetCode Problems Solved", 0.09]
  ],
  "top_negative": [
    ["Skill-Keyword Match", -0.08],
    ["Project-Job Description Overlap", -0.05]
  ],
  "missing_keywords": ["sql", "docker"],
  "recommendations": {
    "score": 72.5,
    "summary": "Good match, but there are areas for improvement.",
    "priority": "medium",
    "gaps": [
      {
        "skill": "Resume Keywords",
        "advice": "Your resume is missing critical keywords from the job description.",
        "action": "Review the job description and incorporate relevant technical keywords into your resume.",
        "topic": null,
        "shap_impact": 0.08,
        "feature_label": "Skill-Keyword Match",
        "roadmap_available": false,
        "roadmap_url": null
      }
    ],
    "total_gaps": 1
  },
  "platform_data": {
    "github": {
      "total_commits": 120,
      "total_repos": 12,
      "languages": ["Python", "JavaScript"]
    },
    "leetcode": {
      "solved": 150,
      "ranking": 45000
    },
    "codeforces": {
      "rating": 1300
    }
  }
}
```

Current error responses:

Model not loaded:

```json
{
  "error": "ML model not loaded. Please train the model first."
}
```

No resume:

```json
{
  "error": "No resume file provided."
}
```

No file selected:

```json
{
  "error": "No file selected."
}
```

Empty job description:

```json
{
  "error": "Job description cannot be empty."
}
```

Unsupported file format:

```json
{
  "error": "Unsupported file format. Please upload a PDF or DOCX."
}
```

Resume parse failure:

```json
{
  "error": "Could not extract text from resume."
}
```

Unhandled failure:

```json
{
  "error": "Analysis failed: <details>"
}
```

Recommended frontend behavior:

- Submit using `FormData`.
- Keep form values on error.
- Scroll to result on success.
- Scroll to error panel on failure.
- Display platform data as `Not provided`, `Fetched`, or `Unavailable`, not just numeric zero.

Recommended backend improvements:

- Save uploaded file with a generated safe filename.
- Add max upload size.
- Add request ID.
- Add structured error codes.
- Add model version to response.
- Add feature version to response.
- Add per-platform fetch status.
- Store prediction and SHAP result in database after persistence exists.

Recommended future response additions:

```json
{
  "model_version": "ats-v1.0.0",
  "feature_version": "features-v1.0.0",
  "platform_status": {
    "github": "success",
    "leetcode": "not_requested",
    "codeforces": "failed"
  },
  "analysis_id": "analysis_123"
}
```

## 8. Recommended New API Routes

These endpoints do not currently exist but should be added for the TypeScript frontend and future production system.

### 8.1 Health Check

```http
GET /api/health
```

Response:

```json
{
  "status": "ok",
  "model_loaded": true,
  "version": "0.1.0"
}
```

Purpose:

- Frontend can check backend availability.
- Deployment platform can check service health.

### 8.2 Roadmap List

```http
GET /api/roadmaps
```

Response:

```json
{
  "roadmaps": [
    {
      "slug": "frontend",
      "name": "Frontend",
      "category": "role",
      "topic_count": 42
    }
  ]
}
```

### 8.3 Roadmap Detail

```http
GET /api/roadmaps/<slug>
```

Response:

```json
{
  "slug": "frontend",
  "name": "Frontend",
  "topics": [
    {
      "title": "HTML",
      "description": "Learn semantic HTML.",
      "links": [
        {
          "title": "MDN HTML",
          "url": "https://developer.mozilla.org/",
          "type": "docs"
        }
      ]
    }
  ]
}
```

### 8.4 Save Assessment

```http
POST /api/assessments
```

Purpose:

- Save an ATS result for authenticated users.

### 8.5 Assessment History

```http
GET /api/assessments
GET /api/assessments/<id>
```

Purpose:

- Show student progress over time.

### 8.6 Feedback on Recommendation

```http
POST /api/recommendations/<id>/feedback
```

Purpose:

- Track whether recommendations were useful.

Request:

```json
{
  "rating": 5,
  "completed": true,
  "comment": "The roadmap helped me add a SQL project."
}
```

## 9. Status Codes

Recommended status codes:

| Status | Meaning |
| --- | --- |
| `200` | Success |
| `201` | Created |
| `400` | Invalid request |
| `401` | Not authenticated |
| `403` | Not allowed |
| `404` | Resource not found |
| `413` | Uploaded file too large |
| `415` | Unsupported media type |
| `429` | Rate limit reached |
| `500` | Server error |
| `503` | External service unavailable or model unavailable |

## 10. File Upload Rules

Current accepted formats:

- `.pdf`
- `.docx`

Recommended rules:

- Maximum file size: 5 MB or 10 MB.
- Use `secure_filename`.
- Generate unique server filename.
- Store under a private upload directory.
- Delete temporary file after text extraction unless user explicitly saves assessment.
- Reject unsupported extensions.
- Reject empty files.
- Return clear parse failure for scanned/image-only PDFs.

## 11. CORS Rules for TypeScript Frontend

During local development:

```text
Frontend: http://localhost:5173
Backend:  http://localhost:5000
```

Recommended Flask setup:

- Allow only frontend dev origin.
- Allow `GET`, `POST`, `OPTIONS`.
- Allow `Content-Type`.
- Do not use wildcard origins in production.

## 12. API Testing Checklist

Profile APIs:

- Valid GitHub username.
- Invalid GitHub username.
- GitHub API rate limit.
- Valid LeetCode username.
- Invalid LeetCode username.
- LeetCode API unavailable.
- Valid Codeforces handle.
- Invalid Codeforces handle.

ATS API:

- Missing resume.
- Empty filename.
- Unsupported file type.
- PDF resume.
- DOCX resume.
- Empty job description.
- No platform usernames.
- All platform usernames.
- One platform API fails.
- Model not loaded.
- Resume parse failure.

Roadmap future APIs:

- List roadmaps.
- Valid roadmap slug.
- Invalid roadmap slug.
