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

Endpoints that need to signal richer error context use a structured shape:

```json
{
  "error": {
    "code": "RESUME_PARSE_FAILED",
    "message": "Could not extract readable text from this resume.",
    "details": {}
  }
}
```

`/api/ats-analyze`, `/api/roadmaps/<slug>`, and the catch-all 404 already use
this shape. The platform tracking endpoints (`/api/track/*`) return their
domain payload plus a `fetch_status` field instead — they always return a
structured body even when the upstream API failed, so the UI can render
"User not found" / "Rate limited" / etc. distinct from the success state.

`fetch_status` is one of:

```text
success | not_found | rate_limited | unauthorized | timeout | error | not_requested
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

Backend behavior (current):

- `total_commits` comes from GitHub Search (`/search/commits?q=author:`),
  capped at 1000 by GitHub itself. When the cap is hit, `total_commits_capped`
  is `true`. **No fabricated padding** is applied if the user has few events.
- `total_pull_requests` comes from GitHub Search (`/search/issues?q=type:pr+author:`).
- Repositories are paginated via the `Link: rel="next"` header (up to 5 pages).
- `language_stats` are computed from real per-repo language byte counts
  aggregated across non-fork repos.
- `commit_timestamps` are real PushEvent timestamps (last 90d) used by the
  consistency-score feature.
- All upstream calls go through `services.http_client` (retry, backoff,
  classification of 404 / 429 / 403-rate-limit / timeout).

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
  "repos": ["project-one", "project-two"],
  "total_commits_capped": false,
  "fetch_status": "success",
  "fetched_at": "2026-04-29T10:30:00+00:00"
}
```

Status-mapped responses:

- HTTP 404 + `fetch_status: "not_found"` if GitHub says the user does not exist.
- HTTP 503 + `fetch_status: "rate_limited"` or `"timeout"` for upstream issues.
- HTTP 200 with `fetch_status: "error"` for unexpected failures (body still
  carries zeros so the UI can render the failure distinctly from "no data").

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

Backend behavior (current):

- One GraphQL query fetches submission stats, contest ranking, and the last
  20 accepted submissions in a single round-trip.
- `recent_submissions` carries `{title, timestamp, lang}` per item — the
  `timestamp` (unix seconds) is what the `problem_solving_velocity` feature
  uses, so this field is no longer empty for real users.
- If GraphQL fails, falls back to the public Heroku stats endpoint for solved
  counts only, and reports `fetch_status` accordingly.

Success response:

```json
{
  "solved": 150,
  "easy": 70,
  "medium": 65,
  "hard": 15,
  "ranking": 45000,
  "total_languages": 4,
  "contest_rating": 1623,
  "recent_submissions": [
    {"title": "Two Sum", "timestamp": 1717000000, "lang": "python3"}
  ],
  "fetch_status": "success",
  "fetched_at": "2026-04-29T10:30:00+00:00"
}
```

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

Backend behavior (current):

- `user.info` populates rating/rank.
- `user.rating` populates contest history.
- `user.status?from=1&count=200` fetches recent submissions; the average of
  the last 50 accepted-submission `problem.rating` values feeds the
  `codeforces_avg_problem_rating` ML feature.
- Codeforces returns 200 with `status:"FAILED"` for unknown handles — this
  is mapped to `fetch_status: "not_found"` and HTTP 404.

Success response:

```json
{
  "rating": 1300,
  "max_rating": 1450,
  "rank": "pupil",
  "max_rank": "specialist",
  "contests": 12,
  "contest_history": [
    {"name": "Codeforces Round 1000", "rating": 1320, "rank": 4321}
  ],
  "recent_submissions": [
    {"timestamp": 1716000000, "verdict": "OK", "problem_rating": 1500}
  ],
  "avg_problem_rating": 1387.4,
  "fetch_status": "success",
  "fetched_at": "2026-04-29T10:30:00+00:00"
}
```

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
  "analysis_id": "8b3f2a17b3924c1d9d0a87f6e5d7c2a1",
  "model_version": "ats-v1.1.0",
  "feature_version": "features-v1.1.0",
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
        "advice": "Your resume is missing keywords required by this job: docker, sql.",
        "action": "Update your resume to demonstrate docker, sql — add a project, certification, or bullet point that uses each one.",
        "topic": null,
        "shap_impact": 0.08,
        "feature_label": "Skill-Keyword Match",
        "roadmap_available": false,
        "roadmap_url": null
      }
    ],
    "total_gaps": 1
  },
  "platform_status": {
    "github": "success",
    "leetcode": "not_requested",
    "codeforces": "rate_limited"
  },
  "platform_data": {
    "github": {
      "total_commits": 120,
      "total_repos": 12,
      "languages": ["Python", "JavaScript"],
      "fetch_status": "success"
    },
    "leetcode": {
      "solved": 0,
      "ranking": 0,
      "fetch_status": "not_requested"
    },
    "codeforces": {
      "rating": 0,
      "avg_problem_rating": 0,
      "fetch_status": "rate_limited"
    }
  }
}
```

Notes on the response:

- `score` is a **calibrated** probability of class `Match` * 100. Calibration
  is fit via `CalibratedClassifierCV(method='isotonic', cv=5)` so the number
  is interpretable as "the model's estimated match probability".
- `shap_values` are computed on the **same** raw feature vector the
  underlying XGBoost saw — no scaling mismatch. Each value is the marginal
  contribution of that feature to the tree's log-odds output.
- `recommendations.gaps` for `Skill-Keyword Match` cites the actual top-3
  missing keywords from the JD. Per-keyword gaps only get a `roadmap_url`
  when the corresponding `roadmap-content/<slug>.json` actually exists.
- `platform_status` distinguishes `not_requested` (user did not provide a
  username) from `rate_limited`, `not_found`, `error`, etc. The frontend
  uses this to render explicit reasons instead of silent zeros.

Error responses (structured, one shape):

```json
{ "error": { "code": "MODEL_NOT_LOADED", "message": "ML model not loaded...", "details": {} } }
{ "error": { "code": "RESUME_REQUIRED", "message": "No resume file provided.", "details": {} } }
{ "error": { "code": "RESUME_FILE_EMPTY", "message": "No file selected.", "details": {} } }
{ "error": { "code": "JOB_DESCRIPTION_REQUIRED", "message": "Job description cannot be empty.", "details": {} } }
{ "error": { "code": "RESUME_FORMAT_UNSUPPORTED", "message": "Unsupported file format. Please upload a PDF or DOCX.", "details": {} } }
{ "error": { "code": "RESUME_PARSE_FAILED", "message": "Could not extract readable text from this resume.", "details": {} } }
{ "error": { "code": "ATS_ANALYSIS_FAILED", "message": "Analysis failed: ...", "details": {"analysis_id": "..."} } }
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
  "model_version": "ats-v1.1.0",
  "feature_version": "features-v1.1.0",
  "dataset_version": "synthetic-bootstrap-v1",
  "feature_count": 29,
  "trained_at": "2026-04-29T10:30:00+00:00"
}
```

`model_version`, `feature_version`, `dataset_version`, and `trained_at`
come from `backend/ml/model_meta.json`, which is written by
`python -m ml.train_model` alongside `model.joblib`. If the model is not
loaded these fields are `null`.

Purpose:

- Frontend can check backend availability and model readiness.
- Deployment platform can check service health.
- Auditors / users can confirm which model + feature set produced a result.

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
