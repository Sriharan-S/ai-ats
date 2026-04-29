# Database Schema Documentation

## 1. Overview

The current project does not have a database. It processes uploaded resumes, API data, model predictions, SHAP explanations, and recommendations in memory. For a real product and research-backed system, the project needs persistent storage.

Recommended database:

```text
PostgreSQL
```

Recommended Python ORM:

```text
SQLAlchemy or SQLModel
```

Recommended migration tool:

```text
Alembic
```

## 2. Database Goals

The database should support:

- Student profiles.
- Consent and privacy tracking.
- Uploaded resume metadata.
- Parsed resume text or redacted resume text.
- Public platform snapshots.
- Job descriptions.
- Student-job assessment pairs.
- Feature vectors.
- Model predictions.
- SHAP explanations.
- Recommendations.
- Recommendation progress.
- Expert labels for real-data model training.
- Model versions and evaluation results.
- Audit logs for sensitive actions.

## 3. Entity Relationship Summary

High-level relationship flow:

```text
students
  -> student_profiles
  -> resumes
  -> platform_accounts
  -> platform_snapshots

jobs
  -> student_job_pairs
  -> feature_vectors
  -> predictions
  -> shap_explanations
  -> recommendations

student_job_pairs
  -> expert_labels

students
  -> recommendation_progress
```

## 4. Core Tables

## 4.1 students

Stores student identity and high-level academic information.

```sql
CREATE TABLE students (
    id UUID PRIMARY KEY,
    display_name VARCHAR(160),
    email VARCHAR(255) UNIQUE,
    department VARCHAR(160),
    graduation_year INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP
);
```

Fields:

| Field | Purpose |
| --- | --- |
| `id` | Primary student ID |
| `display_name` | Student display name |
| `email` | Login/contact email |
| `department` | Department or program |
| `graduation_year` | Graduation year |
| `deleted_at` | Soft delete marker |

Privacy note:

- Use soft delete only for internal integrity, but support full hard deletion when a student requests data deletion.

## 4.2 consent_records

Tracks explicit student consent.

```sql
CREATE TABLE consent_records (
    id UUID PRIMARY KEY,
    student_id UUID NOT NULL REFERENCES students(id),
    consent_type VARCHAR(80) NOT NULL,
    status VARCHAR(40) NOT NULL,
    consent_text_version VARCHAR(40) NOT NULL,
    granted_at TIMESTAMP,
    revoked_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

Consent types:

- `resume_processing`
- `github_public_data`
- `leetcode_public_data`
- `codeforces_public_data`
- `model_training`
- `research_reporting`

Status values:

- `granted`
- `revoked`
- `expired`

## 4.3 student_profiles

Stores a student's current profile configuration.

```sql
CREATE TABLE student_profiles (
    id UUID PRIMARY KEY,
    student_id UUID NOT NULL REFERENCES students(id),
    headline VARCHAR(255),
    target_role VARCHAR(160),
    github_username VARCHAR(120),
    leetcode_username VARCHAR(120),
    codeforces_handle VARCHAR(120),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

Purpose:

- Keep current public platform handles.
- Store target career direction.

## 4.4 resumes

Stores resume metadata and parsed text.

```sql
CREATE TABLE resumes (
    id UUID PRIMARY KEY,
    student_id UUID NOT NULL REFERENCES students(id),
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255),
    file_type VARCHAR(20) NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    text_hash VARCHAR(128),
    parsed_text_redacted TEXT,
    parse_status VARCHAR(40) NOT NULL,
    parse_error TEXT,
    uploaded_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP
);
```

Recommended policy:

- Do not store raw resume files longer than necessary unless the student explicitly chooses to save them.
- Store redacted parsed text for analysis history.
- Store `text_hash` to detect duplicate uploads.

Parse status values:

- `pending`
- `success`
- `failed`

## 4.5 platform_accounts

Stores connected public platform accounts.

```sql
CREATE TABLE platform_accounts (
    id UUID PRIMARY KEY,
    student_id UUID NOT NULL REFERENCES students(id),
    platform VARCHAR(40) NOT NULL,
    username VARCHAR(120) NOT NULL,
    profile_url TEXT,
    connection_status VARCHAR(40) NOT NULL,
    last_verified_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (platform, username)
);
```

Platform values:

- `github`
- `leetcode`
- `codeforces`

Connection status values:

- `active`
- `not_found`
- `private`
- `api_error`
- `not_verified`

## 4.6 platform_snapshots

Stores time-stamped API responses and normalized metrics.

```sql
CREATE TABLE platform_snapshots (
    id UUID PRIMARY KEY,
    student_id UUID NOT NULL REFERENCES students(id),
    platform_account_id UUID REFERENCES platform_accounts(id),
    platform VARCHAR(40) NOT NULL,
    fetch_status VARCHAR(40) NOT NULL,
    raw_json JSONB,
    normalized_json JSONB,
    fetched_at TIMESTAMP NOT NULL DEFAULT NOW(),
    error_message TEXT
);
```

Purpose:

- Enable historical trend analysis.
- Avoid repeated API calls.
- Support reproducible model features.

Recommended indexes:

```sql
CREATE INDEX idx_platform_snapshots_student_platform
ON platform_snapshots(student_id, platform, fetched_at DESC);
```

## 5. Job and Assessment Tables

## 5.1 jobs

Stores job descriptions used for assessment and training.

```sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY,
    title VARCHAR(255),
    company VARCHAR(255),
    source VARCHAR(255),
    role_family VARCHAR(120),
    job_description TEXT NOT NULL,
    required_skills JSONB,
    preferred_skills JSONB,
    location VARCHAR(160),
    experience_level VARCHAR(80),
    collected_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

Role family examples:

- `frontend`
- `backend`
- `full_stack`
- `data_analyst`
- `ai_ml`
- `devops`
- `mobile`
- `qa`

## 5.2 student_job_pairs

Links a student/resume/profile snapshot to a job.

```sql
CREATE TABLE student_job_pairs (
    id UUID PRIMARY KEY,
    student_id UUID NOT NULL REFERENCES students(id),
    resume_id UUID REFERENCES resumes(id),
    job_id UUID NOT NULL REFERENCES jobs(id),
    profile_snapshot_id UUID,
    pair_source VARCHAR(80) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

Pair source values:

- `student_assessment`
- `expert_labelling`
- `admin_created`
- `research_dataset`

## 5.3 feature_vectors

Stores model input features for reproducibility.

```sql
CREATE TABLE feature_vectors (
    id UUID PRIMARY KEY,
    pair_id UUID NOT NULL REFERENCES student_job_pairs(id),
    feature_version VARCHAR(80) NOT NULL,
    features_json JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

Example `features_json`:

```json
{
  "github_total_commits": 120,
  "github_total_repos": 12,
  "leetcode_solved": 150,
  "codeforces_rating": 1300,
  "commit_consistency_score": 0.72,
  "skill_keyword_density": 0.54,
  "api_skill_validation_ratio": 0.66,
  "project_skill_overlap": 0.41,
  "has_github_profile": true,
  "has_leetcode_profile": true,
  "has_codeforces_profile": false
}
```

Important:

- Store missingness flags.
- Store feature version every time.
- Never overwrite feature vectors used by a past prediction.

## 5.4 predictions

Stores ATS model outputs.

```sql
CREATE TABLE predictions (
    id UUID PRIMARY KEY,
    pair_id UUID NOT NULL REFERENCES student_job_pairs(id),
    feature_vector_id UUID NOT NULL REFERENCES feature_vectors(id),
    model_version VARCHAR(80) NOT NULL,
    score NUMERIC(5,2) NOT NULL,
    score_band VARCHAR(40),
    prediction_label VARCHAR(40),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

Score bands:

- `strong_match`
- `good_match`
- `moderate_match`
- `low_match`

## 5.5 shap_explanations

Stores local explanation output for each prediction.

```sql
CREATE TABLE shap_explanations (
    id UUID PRIMARY KEY,
    prediction_id UUID NOT NULL REFERENCES predictions(id),
    shap_values_json JSONB NOT NULL,
    top_positive_json JSONB NOT NULL,
    top_negative_json JSONB NOT NULL,
    base_value NUMERIC,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

Purpose:

- Re-render old explanations.
- Audit why a recommendation was produced.
- Support paper analysis.

## 5.6 recommendations

Stores generated skill-gap recommendations.

```sql
CREATE TABLE recommendations (
    id UUID PRIMARY KEY,
    prediction_id UUID NOT NULL REFERENCES predictions(id),
    skill VARCHAR(160) NOT NULL,
    advice TEXT NOT NULL,
    action TEXT NOT NULL,
    topic_slug VARCHAR(160),
    roadmap_url TEXT,
    priority VARCHAR(40),
    source VARCHAR(80) NOT NULL,
    shap_impact NUMERIC,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

Source values:

- `shap_negative_feature`
- `missing_keyword`
- `manual`
- `llm_generated`

## 5.7 recommendation_progress

Tracks whether students act on recommendations.

```sql
CREATE TABLE recommendation_progress (
    id UUID PRIMARY KEY,
    recommendation_id UUID NOT NULL REFERENCES recommendations(id),
    student_id UUID NOT NULL REFERENCES students(id),
    status VARCHAR(40) NOT NULL,
    student_notes TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

Status values:

- `planned`
- `in_progress`
- `completed`
- `dismissed`

## 6. Expert Labelling Tables

## 6.1 reviewers

Stores expert reviewers for dataset labelling.

```sql
CREATE TABLE reviewers (
    id UUID PRIMARY KEY,
    display_name VARCHAR(160) NOT NULL,
    email VARCHAR(255),
    role VARCHAR(120),
    organization VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

Reviewer roles:

- `technical_recruiter`
- `faculty`
- `industry_mentor`
- `admin`

## 6.2 expert_labels

Stores expert fit scores for student-job pairs.

```sql
CREATE TABLE expert_labels (
    id UUID PRIMARY KEY,
    pair_id UUID NOT NULL REFERENCES student_job_pairs(id),
    reviewer_id UUID NOT NULL REFERENCES reviewers(id),
    fit_score INTEGER NOT NULL CHECK (fit_score BETWEEN 1 AND 5),
    label_notes TEXT,
    labelled_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (pair_id, reviewer_id)
);
```

Model training rule:

- Average 3 expert labels per student-job pair.
- Normalize average score to create regression target.
- Classification target: `Match = 1` if average score is at least `3.5`.

## 6.3 label_aggregates

Optional materialized table for faster training dataset export.

```sql
CREATE TABLE label_aggregates (
    pair_id UUID PRIMARY KEY REFERENCES student_job_pairs(id),
    label_count INTEGER NOT NULL,
    average_fit_score NUMERIC(3,2) NOT NULL,
    match_label INTEGER NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

## 7. Model Registry Tables

## 7.1 model_versions

Tracks trained model artifacts.

```sql
CREATE TABLE model_versions (
    id UUID PRIMARY KEY,
    model_version VARCHAR(80) UNIQUE NOT NULL,
    feature_version VARCHAR(80) NOT NULL,
    artifact_path TEXT NOT NULL,
    training_dataset_version VARCHAR(80),
    trained_at TIMESTAMP NOT NULL DEFAULT NOW(),
    trained_by VARCHAR(160),
    notes TEXT
);
```

## 7.2 model_metrics

Stores evaluation metrics.

```sql
CREATE TABLE model_metrics (
    id UUID PRIMARY KEY,
    model_version_id UUID NOT NULL REFERENCES model_versions(id),
    split_name VARCHAR(80) NOT NULL,
    metric_name VARCHAR(80) NOT NULL,
    metric_value NUMERIC NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

Metric examples:

- `accuracy`
- `precision_match`
- `recall_match`
- `f1_weighted`
- `roc_auc`
- `pr_auc`
- `mae`
- `calibration_error`

## 8. Roadmap Tables

Current roadmap data lives in JSON files under `roadmap-content/`. It can remain file-based for phase 1. If progress tracking is needed, add database tables.

## 8.1 roadmaps

```sql
CREATE TABLE roadmaps (
    id UUID PRIMARY KEY,
    slug VARCHAR(160) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(80) NOT NULL,
    description TEXT,
    source VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

## 8.2 roadmap_topics

```sql
CREATE TABLE roadmap_topics (
    id UUID PRIMARY KEY,
    roadmap_id UUID NOT NULL REFERENCES roadmaps(id),
    position INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

## 8.3 roadmap_resources

```sql
CREATE TABLE roadmap_resources (
    id UUID PRIMARY KEY,
    topic_id UUID NOT NULL REFERENCES roadmap_topics(id),
    title VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    resource_type VARCHAR(80),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

## 8.4 student_roadmap_progress

```sql
CREATE TABLE student_roadmap_progress (
    id UUID PRIMARY KEY,
    student_id UUID NOT NULL REFERENCES students(id),
    roadmap_id UUID NOT NULL REFERENCES roadmaps(id),
    topic_id UUID REFERENCES roadmap_topics(id),
    status VARCHAR(40) NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (student_id, roadmap_id, topic_id)
);
```

## 9. Audit and Privacy Tables

## 9.1 audit_logs

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    actor_student_id UUID REFERENCES students(id),
    actor_reviewer_id UUID REFERENCES reviewers(id),
    action VARCHAR(120) NOT NULL,
    entity_type VARCHAR(120),
    entity_id UUID,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

Use for:

- Resume upload.
- Resume deletion.
- Consent changes.
- Assessment created.
- Recommendation completed.
- Admin label changes.

## 9.2 data_deletion_requests

```sql
CREATE TABLE data_deletion_requests (
    id UUID PRIMARY KEY,
    student_id UUID NOT NULL REFERENCES students(id),
    status VARCHAR(40) NOT NULL,
    requested_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    notes TEXT
);
```

Status values:

- `requested`
- `in_review`
- `completed`
- `rejected`

## 10. Recommended Indexes

```sql
CREATE INDEX idx_resumes_student_uploaded
ON resumes(student_id, uploaded_at DESC);

CREATE INDEX idx_jobs_role_family
ON jobs(role_family);

CREATE INDEX idx_pairs_student_created
ON student_job_pairs(student_id, created_at DESC);

CREATE INDEX idx_predictions_pair_created
ON predictions(pair_id, created_at DESC);

CREATE INDEX idx_recommendations_prediction
ON recommendations(prediction_id);

CREATE INDEX idx_expert_labels_pair
ON expert_labels(pair_id);

CREATE INDEX idx_platform_snapshots_student_fetched
ON platform_snapshots(student_id, fetched_at DESC);
```

## 11. Data Retention Rules

Recommended defaults:

| Data | Retention |
| --- | --- |
| Uploaded raw resume file | Delete after parsing unless student saves it |
| Parsed redacted resume text | Keep while account is active |
| Platform raw JSON | Keep latest plus periodic snapshots |
| Predictions and SHAP output | Keep for student history |
| Expert labels | Keep for research dataset if consent allows |
| Audit logs | Keep according to institution policy |

## 12. Phase-by-Phase Implementation

### Phase 1: Minimum Persistence

Add:

- `students`
- `resumes`
- `jobs`
- `student_job_pairs`
- `feature_vectors`
- `predictions`
- `shap_explanations`
- `recommendations`

### Phase 2: Platform History

Add:

- `platform_accounts`
- `platform_snapshots`
- API refresh jobs.

### Phase 3: Real Dataset Labelling

Add:

- `reviewers`
- `expert_labels`
- `label_aggregates`

### Phase 4: Roadmap Progress

Add:

- `roadmaps`
- `roadmap_topics`
- `roadmap_resources`
- `student_roadmap_progress`
- `recommendation_progress`

### Phase 5: Governance

Add:

- `consent_records`
- `audit_logs`
- `data_deletion_requests`
- `model_versions`
- `model_metrics`

## 13. Important Design Decisions

1. Store features and predictions separately.
   - Features are inputs.
   - Predictions are outputs.
   - This supports reproducibility.

2. Store platform snapshots.
   - Public profile data changes over time.
   - Snapshots allow longitudinal analysis.

3. Store consent records separately.
   - Consent can change.
   - Research/model-training consent should be explicit.

4. Store model version with every prediction.
   - Scores from different models are not directly comparable unless versioned.

5. Add missingness flags to feature vectors.
   - Missing GitHub data is different from zero GitHub activity.

