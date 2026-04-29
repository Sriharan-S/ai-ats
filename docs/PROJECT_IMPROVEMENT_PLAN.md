# AIATS Project Improvement Documentation

## 1. Executive Summary

This project implements an AI-Powered Student Profile Tracker and ATS analysis system. The manuscript describes a stronger target architecture: a dynamic profile tracker that combines resume parsing, GitHub activity, LeetCode statistics, Codeforces performance, engineered skill features, an ensemble machine learning model, SHAP explanations, and personalized learning recommendations.

The current codebase already contains many of those building blocks:

- Flask backend in `backend/main.py`.
- TypeScript React frontend in `frontend/`.
- Resume upload and parsing for PDF/DOCX.
- GitHub, LeetCode, and Codeforces API integrations.
- ML feature engineering in `ml/feature_engineering.py`.
- XGBoost plus Random Forest soft-voting model in `ml/pipeline.py`.
- SHAP-based explanations.
- Recommendation mapping to 40 local roadmap JSON files.
- Compiled Vite frontend served by Flask for production-like local runs.

The biggest improvement needed is not just a frontend rewrite. The system must move from a demo/prototype into a validated product:

1. Keep the backend and ML services in Python.
2. Migrate the frontend from static HTML/JavaScript to TypeScript.
3. Replace synthetic model training data with real labelled student-job data.
4. Add persistent storage for profiles, API snapshots, jobs, predictions, labels, and feedback.
5. Add reproducible evaluation, privacy controls, and deployment boundaries.

## 2. Current Project Snapshot

### 2.1 Repository Structure Observed

Important files and folders:

- `backend/main.py`: Flask API app, resume parsing, external platform calls, roadmap APIs, static frontend fallback, and ML ATS endpoint.
- `ml/feature_engineering.py`: engineered features such as commit consistency, skill density, API skill validation, and project overlap.
- `ml/pipeline.py`: StandardScaler, XGBoost, Random Forest, VotingClassifier, SHAP explanation logic.
- `ml/train_model.py`: synthetic training data generator and model training script.
- `ml/recommender.py`: maps negative SHAP factors and missing keywords to roadmap recommendations.
- `frontend/src/pages/AtsPage.tsx`: TypeScript ATS analysis UI calling `/api/ats-analyze`.
- `frontend/src/pages/TrackPage.tsx`: TypeScript profile tracking UI calling GitHub/LeetCode/Codeforces API endpoints.
- `backend/roadmap-content/`: 40 JSON roadmap files.
- `backend/uploads/`: temporary resume upload directory, ignored by git.
- `466_Manuscript.pdf` and `_paper_text.txt`: paper content used to align this improvement plan.

### 2.2 Backend Routes

Current Flask routes:

| Route | Purpose |
| --- | --- |
| `/`, `/index` | Home page |
| `/track` | Profile tracking page |
| `/learn`, `/learn/<path:subpath>` | Learning roadmap pages |
| `/ats`, `/ats/` | ATS page |
| `/ai` | Redirects to an external AI URL |
| `/api/track/github/<username>` | Fetch GitHub data |
| `/api/track/leetcode/<username>` | Fetch LeetCode data |
| `/api/track/codeforces/<username>` | Fetch Codeforces data |
| `/api/profile` | Fetch combined platform profile |
| `/api/ats-analyze` | ML-based ATS analysis with SHAP and recommendations |

### 2.3 Frontend Status

The frontend is currently a static multi-page interface:

| File | Lines | Fetch calls | Notes |
| --- | ---: | ---: | --- |
| `ats.html` | 758 | 2 | ATS UI, charts, form handling, result rendering |
| `track.html` | 793 | 3 | Platform dashboard and chart rendering |
| `index.html` | 468 | 0 | Landing/home content |
| `learn.html` | 216 | 0 | Roadmap selection |
| `learnmap.html` | 195 | 0 | Roadmap rendering |
| `contacts.html` | 87 | 0 | Static page |
| `privacy.html` | 93 | 0 | Static page |
| `ai.html` | 19 | 0 | Redirect helper |

Problems with the current frontend:

- Large inline scripts make changes risky.
- No TypeScript types for API responses.
- No component boundaries.
- No reusable API client.
- No build system, linting, or frontend tests.
- Chart rendering and DOM updates are tightly coupled.
- UI state is manually coordinated through raw DOM access.

## 3. Alignment With the Manuscript

The paper describes five major modules:

1. Data collection from resumes and public developer APIs.
2. Preprocessing with text and numerical transformations.
3. Advanced feature engineering.
4. Ensemble ATS model with XGBoost, Random Forest, and soft voting.
5. SHAP-based explainability and personalized recommendations.

The current implementation partially matches this architecture.

### 3.1 Implemented Well

- Resume parsing exists for PDF and DOCX.
- GitHub, LeetCode, and Codeforces integrations exist.
- Feature engineering functions exist for the features named in the paper.
- XGBoost and Random Forest are combined through a soft VotingClassifier.
- SHAP explanations are exposed through the ATS endpoint.
- Roadmap-based recommendations are generated from negative explanation factors.

### 3.2 Gaps Against the Paper

| Manuscript Claim | Current State | Improvement Needed |
| --- | --- | --- |
| Historical time-stamped data is stored | No database or history store | Add PostgreSQL and API snapshot tables |
| Real student profiles are used | Model training uses synthetic data | Build real labelled dataset |
| 500+ students, 200 jobs, 10,000 labelled pairs | Not implemented | Add data collection and labelling workflow |
| Formal results section and metrics | Not available | Add evaluation pipeline and reports |
| Exponential backoff and robust API retries | Minimal try/except and direct requests | Add retry policy, caching, rate limit handling |
| Cold-start handling | Zero-filled missing platform data | Add explicit missingness flags and fair scoring |
| Privacy and consent | No visible consent model or data retention rules | Add opt-in consent, retention, deletion, audit logs |
| Production frontend SPA | Static HTML pages | Build TypeScript frontend |

## 4. Real Data and Analysis Plan

The current ML model is trained using synthetic data from `ml/train_model.py`. This is acceptable for a prototype, but it cannot support a research claim or production-grade recommendation system.

### 4.1 Data Sources

Collect real data from opt-in students:

- Resume text and parsed resume sections.
- GitHub public repositories, languages, events, contribution rhythm, pull requests.
- LeetCode solved counts by difficulty, ranking, language usage, recent activity where available.
- Codeforces rating, max rating, rank, contests, and rating history.
- Student-declared target roles.
- Target job descriptions.
- Expert labels for student-job fit.
- Later phase: actual interview, shortlist, offer, or placement outcomes.

### 4.2 Minimum Dataset for Phase II

The manuscript proposes:

- 500+ students.
- 200 entry-level job descriptions.
- 10,000 student-job pairs.
- 3 expert reviewers per pair.
- 1 to 5 fit score.
- Classification label: `Match = 1` when average score is at least 3.5, otherwise `No Match = 0`.

This should become the actual dataset target.

Recommended tables:

```text
students
- id
- consent_status
- department
- graduation_year
- created_at

student_profiles
- id
- student_id
- resume_text_hash
- resume_text_redacted
- github_username
- leetcode_username
- codeforces_username
- created_at

platform_snapshots
- id
- student_id
- platform
- raw_json
- collected_at
- fetch_status

jobs
- id
- title
- company_or_source
- role_family
- job_description
- required_skills
- collected_at

student_job_pairs
- id
- student_id
- job_id
- feature_version
- feature_json
- created_at

expert_labels
- id
- pair_id
- reviewer_id
- fit_score_1_to_5
- notes
- created_at

predictions
- id
- pair_id
- model_version
- score
- shap_json
- recommendations_json
- created_at
```

### 4.3 Feature Improvements for Real Data

Current feature names are a good start, but real data needs more robust features.

Add platform missingness flags:

- `has_github_profile`
- `has_leetcode_profile`
- `has_codeforces_profile`
- `github_fetch_failed`
- `leetcode_fetch_failed`
- `codeforces_fetch_failed`

Improve GitHub features:

- Commits per active week.
- Active weeks in last 90/180/365 days.
- Repository recency.
- Fork vs original repository ratio.
- Pull request count from search API, not only recent events.
- Language percentages from all public repos, with pagination.
- Project quality signals: README presence, stars, topics, tests, deployment link.

Improve LeetCode features:

- Solved count by difficulty.
- Medium plus hard ratio.
- Contest rating if available.
- Recent solved velocity.
- Topic coverage, such as arrays, trees, graphs, dynamic programming.

Improve Codeforces features:

- Current rating, max rating, contest count.
- Rating trend over last 5 to 10 contests.
- Upsolve proxy if submissions are collected.

Improve resume and job matching:

- Extract resume sections instead of using full resume text for every text feature.
- Separate skills, projects, education, certifications, experience, achievements.
- Use a controlled skill taxonomy to normalize terms like `js`, `javascript`, `node.js`, `node`.
- Add semantic similarity using sentence embeddings after baseline metrics are stable.

### 4.4 Evaluation Design

Use both a baseline and the improved model.

Baseline:

- TF-IDF resume/job cosine similarity.
- Keyword overlap score.
- No platform data.

Improved model:

- Resume/job features.
- API-derived profile features.
- Engineered consistency and validation features.
- XGBoost plus Random Forest soft voting, or calibrated XGBoost as a simpler deployable baseline.

Metrics:

- Accuracy.
- Precision for `Match`.
- Recall for `Match`.
- Weighted F1.
- ROC-AUC.
- PR-AUC.
- Calibration error.
- Mean Absolute Error if predicting 1 to 5 fit score.

Validation:

- 5-fold stratified cross-validation.
- Student-level split to avoid the same student appearing in both train and test.
- Role-family split for testing generalization across Frontend, Backend, Data, AI/ML, and DevOps roles.

Fairness and cold-start checks:

- Compare performance for students with and without public coding profiles.
- Report score shifts caused by missing platform data.
- Ensure missing GitHub/LeetCode does not automatically produce an unfairly low score.
- Track false negatives, because missed qualified students are the highest-risk outcome.

### 4.5 Analysis Outputs to Produce

For the research paper and product dashboard, generate:

- Dataset summary: number of students, jobs, pairs, labels, class balance.
- Feature distribution charts.
- Baseline vs model metric table.
- Confusion matrix.
- Calibration curve.
- Top global SHAP features.
- Local SHAP explanations for individual students.
- Recommendation completion tracking over time.
- Before/after skill improvement analysis after students follow roadmaps.

## 5. TypeScript Frontend Migration

### 5.1 Recommendation

Use a separate TypeScript frontend built with Vite, React, and TypeScript.

Reason:

- The existing app behaves like a dashboard and form-driven tool.
- React gives clean component boundaries for ATS results, charts, tabs, upload forms, roadmap cards, and platform panels.
- Vite is lightweight and easy to connect to Flask.
- The Python backend can remain focused on APIs, ML, file parsing, and data storage.

Suggested frontend directory:

```text
frontend/
  package.json
  tsconfig.json
  vite.config.ts
  src/
    main.tsx
    App.tsx
    api/
      client.ts
      types.ts
    pages/
      HomePage.tsx
      TrackPage.tsx
      AtsPage.tsx
      LearnPage.tsx
      RoadmapPage.tsx
    components/
      charts/
      forms/
      layout/
      recommendations/
      platform/
    styles/
      globals.css
```

### 5.2 API Type Contracts

Create TypeScript interfaces before migrating UI logic.

```ts
export interface GitHubProfile {
  total_commits: number;
  total_pull_requests: number;
  total_repos: number;
  total_languages: number;
  languages: string[];
  language_stats: Record<string, number>;
  repos: string[];
}

export interface LeetCodeProfile {
  solved: number;
  easy: number;
  medium: number;
  hard: number;
  ranking: number;
  total_languages: number;
}

export interface CodeforcesProfile {
  rating: number;
  max_rating: number;
  rank: string;
  max_rank: string;
  contests: number;
  contest_history: Array<{
    name: string;
    rating: number;
    rank: number;
  }>;
}

export interface RecommendationGap {
  skill: string;
  advice: string;
  action: string;
  topic: string | null;
  shap_impact: number;
  feature_label: string;
  roadmap_available: boolean;
  roadmap_url: string | null;
}

export interface AtsAnalysisResponse {
  score: number;
  shap_values: Record<string, number>;
  top_positive: Array<[string, number]>;
  top_negative: Array<[string, number]>;
  missing_keywords: string[];
  recommendations: {
    score: number;
    summary: string;
    priority: "low" | "medium" | "high" | "critical";
    gaps: RecommendationGap[];
    total_gaps: number;
  };
  platform_data: {
    github: Pick<GitHubProfile, "total_commits" | "total_repos" | "languages">;
    leetcode: Pick<LeetCodeProfile, "solved" | "ranking">;
    codeforces: Pick<CodeforcesProfile, "rating">;
  };
}
```

### 5.3 API Client

Create a single API client in TypeScript:

```ts
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error ?? `Request failed: ${response.status}`);
  }

  return data as T;
}
```

### 5.4 Migration Phases

Phase 1: Prepare backend for API-first frontend.

- Keep current HTML working.
- Add CORS only for the Vite dev server.
- Standardize JSON error responses.
- Add `/api/health`.
- Add OpenAPI documentation for all API routes.

Phase 2: Create TypeScript app shell.

- Add `frontend/` Vite React project.
- Implement layout, routing, global styles, and API client.
- Port `track.html` first because it has clear platform API boundaries.

Phase 3: Port ATS workflow.

- Convert resume upload form to React.
- Use typed `FormData`.
- Render score, SHAP factors, missing keywords, platform summary, and roadmap recommendations.
- Replace raw DOM manipulation with React state.

Phase 4: Port learning roadmap pages.

- Either keep Flask-rendered roadmaps temporarily or expose roadmap JSON through `/api/roadmaps`.
- Render roadmap pages in TypeScript.

Phase 5: Retire static HTML.

- Build TypeScript frontend with `npm run build`.
- Serve built assets from Flask or deploy frontend separately.
- Remove duplicated static HTML only after parity testing.

### 5.5 Development Setup

Backend:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Vite proxy example:

```ts
server: {
  proxy: {
    "/api": "http://localhost:5000"
  }
}
```

## 6. Python Backend Improvement Plan

### 6.1 Split `main.py`

`main.py` currently handles routing, external API calls, parsing, model invocation, and page rendering. Split it into modules:

```text
backend/
  app.py
  config.py
  routes/
    pages.py
    ats.py
    profile.py
    roadmaps.py
  services/
    github_service.py
    leetcode_service.py
    codeforces_service.py
    resume_parser.py
    ats_service.py
  ml/
    feature_engineering.py
    pipeline.py
    recommender.py
  schemas/
    ats.py
    profile.py
```

Use an app factory:

```python
def create_app():
    app = Flask(__name__)
    register_routes(app)
    return app
```

### 6.2 File Upload Safety

Current upload handling saves files using the original filename. Improve it:

- Use `secure_filename`.
- Add unique IDs to filenames.
- Enforce file size limits.
- Validate MIME type and extension.
- Store uploads outside public static paths.
- Delete temporary files after parsing unless user consent allows retention.
- Scan or reject encrypted PDFs.

### 6.3 External API Reliability

Add:

- Retry with exponential backoff.
- Request timeout constants.
- Rate-limit awareness.
- Per-platform error status in API responses.
- Cache successful platform snapshots.
- Background refresh jobs for slow APIs.

### 6.4 Data Persistence

Add PostgreSQL for:

- Users/students.
- Consent.
- Profile snapshots.
- Job descriptions.
- Model features.
- Predictions.
- SHAP explanations.
- Recommendations.
- User feedback and outcomes.

Use SQLAlchemy or SQLModel with Alembic migrations.

### 6.5 API Contract and Validation

Add:

- Pydantic schemas or Marshmallow schemas.
- Consistent response shapes.
- OpenAPI documentation.
- Clear error codes.
- Request IDs in logs.

Example error shape:

```json
{
  "error": {
    "code": "RESUME_PARSE_FAILED",
    "message": "Could not extract readable text from this PDF.",
    "details": {}
  }
}
```

## 7. ML and XAI Improvement Plan

### 7.1 Replace Synthetic Training

`ml/train_model.py` currently generates synthetic data. Keep it only for local smoke testing. Add a real training entrypoint:

```text
ml/
  datasets/
    build_dataset.py
    validate_dataset.py
  train_real_model.py
  evaluate_model.py
  model_card.md
```

### 7.2 Add Model Versioning

Track:

- Dataset version.
- Feature version.
- Model version.
- Training date.
- Metrics.
- Label distribution.
- SHAP summary.
- Known limitations.

Tools to consider:

- MLflow for experiment tracking.
- DVC for dataset versioning.
- A plain `model_registry/` folder for a lightweight first step.

### 7.3 Fix Explainability Details

Current code scales features before prediction but passes unscaled features to the SHAP explainer. For tree models trained on scaled values, SHAP should explain the same transformed representation used by the model, or the model should be trained on unscaled tree-friendly numeric features.

Recommended choices:

- For tree models, remove `StandardScaler` unless linear models are added.
- If scaling remains, compute SHAP on the scaled matrix and map values back carefully in the UI.
- Add tests confirming the SHAP feature order matches `FEATURE_NAMES`.

### 7.4 Calibration

The score is currently the probability of class 1 multiplied by 100. Add calibration:

- CalibratedClassifierCV.
- Reliability curve.
- Expected calibration error.
- Score bands: low, moderate, good, strong.

This matters because students will treat the score as guidance, not just a model output.

## 8. Product Improvements

### 8.1 Student Dashboard

Add:

- Profile completeness score.
- Platform connection status.
- Skill evidence timeline.
- Role-specific readiness.
- Recommendation progress tracking.
- Before/after score comparison after actions are completed.

### 8.2 Counselor/Admin Dashboard

Add:

- Cohort skill gaps.
- Most common missing skills by role.
- Department-level readiness trends.
- Exportable reports.
- Intervention tracking.

### 8.3 Recommendation Quality

Current recommendations are rule-mapped from SHAP labels and missing keywords. Improve by:

- Ranking gaps by impact and feasibility.
- Mapping skills to specific roadmap nodes, not only full roadmap pages.
- Adding project suggestions tied to target roles.
- Tracking whether a recommendation was completed.
- Measuring score improvement after completion.

## 9. Security, Privacy, and Ethics

Must-have controls:

- Explicit opt-in consent for each platform.
- Clear data retention policy.
- Delete-my-data workflow.
- No hidden scraping of private data.
- Avoid storing raw resumes unless required.
- Redact personally identifiable information for model training.
- Do not use protected demographic attributes for scoring.
- Monitor false negatives and subgroup performance.
- Explain when a score is less reliable due to missing data.

Important product copy:

- This should be positioned as a student guidance tool, not an automatic rejection system.
- Scores should support coaching and planning.
- Students should see actionable reasons and next steps.

## 10. Testing Plan

Backend tests:

- Resume parsing for PDF and DOCX.
- API service handling for success, missing user, rate limit, timeout.
- Feature vector construction.
- Missing platform data behavior.
- ATS endpoint response shape.
- Recommendation mapping.

Frontend tests:

- API client error handling.
- ATS upload form validation.
- Track page loading/error/success states.
- Chart rendering with empty and populated data.
- Recommendation cards and roadmap links.

ML tests:

- Feature order matches model order.
- Model can train on a fixture dataset.
- Prediction output is between 0 and 100.
- SHAP output contains all expected feature labels.
- Real dataset validation rejects missing labels or impossible values.

End-to-end tests:

- Upload resume and job description.
- Fetch platform data.
- Render score and recommendations.
- Open a recommended roadmap.

## 11. Implementation Roadmap

### Sprint 1: Stabilize Backend

- Create virtual environment and install dependencies.
- Add `/api/health`.
- Add structured error responses.
- Secure upload handling.
- Split external API services out of `main.py`.
- Add tests for parsing and feature creation.

### Sprint 2: TypeScript Foundation

- Create Vite React TypeScript frontend.
- Add typed API client.
- Add app routing.
- Port Track page.
- Add charts as reusable components.

### Sprint 3: ATS TypeScript Migration

- Port ATS upload form.
- Render typed ATS response.
- Render SHAP bars and recommendations.
- Remove legacy qualitative resume endpoints from the active frontend contract.

### Sprint 4: Real Data Pipeline

- Add PostgreSQL schema.
- Store profile snapshots and job descriptions.
- Build student-job pair dataset export.
- Add labelling workflow.

### Sprint 5: Real Model Training and Evaluation

- Train on labelled pairs.
- Compare baseline vs improved model.
- Generate evaluation report.
- Add model card.
- Add SHAP global analysis.

### Sprint 6: Product Validation

- Pilot with a student cohort.
- Track recommendation completion.
- Measure score change and placement/interview outcomes.
- Use results to update the paper's Results and Discussion section.

## 12. Immediate Next Actions

1. Install Python dependencies and verify the current backend:

```bash
pip install -r requirements.txt
python -m ml.train_model
python main.py
```

2. Create the TypeScript frontend:

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install chart.js react-chartjs-2
```

3. Add API types before porting UI code.

4. Add PostgreSQL schema for real profiles and labels.

5. Replace synthetic-only training with a real dataset pipeline.

## 13. Known Current Blockers

- This machine's current Python environment does not have `numpy` installed, so the model evaluation command could not run during this analysis.
- The project is not currently inside a Git repository, so there is no version history or branch workflow visible from this folder.
- There is no Node/TypeScript project yet.
- There is no database layer yet.
- The current trained model artifact exists, but the training script is synthetic-data based, so it should not be used as research evidence.

## 14. Target End State

The improved system should be:

- Python backend for API, ML, parsing, data storage, and model serving.
- TypeScript React frontend for all user-facing workflows.
- PostgreSQL-backed student profile history.
- Real labelled dataset for training and evaluation.
- Reproducible model metrics and SHAP analysis.
- Privacy-first, opt-in, student guidance product.
- Ready to support a stronger paper with actual results instead of expected results.
