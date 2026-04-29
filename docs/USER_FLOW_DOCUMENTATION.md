# User Flow Documentation

## 1. Overview

This document describes how users should move through the AIATS / Raven platform. It covers the current student-facing flows and future flows for saved dashboards, recommendations, and counselor/admin review.

Primary user types:

- Student.
- Career counselor or faculty mentor.
- Expert reviewer.
- Admin.

Current implementation is mainly student-facing. Counselor, expert reviewer, and admin flows are recommended future additions.

## 2. Core Student Journey

The ideal student journey is:

```text
Open Home
  -> Track public coding profile
  -> Upload resume and job description
  -> Receive ATS score and explanations
  -> Review missing skills
  -> Open recommended roadmaps
  -> Complete learning actions
  -> Reassess later and compare improvement
```

This journey should make the system feel like a career improvement loop, not a one-time score generator.

## 3. Flow 1: First-Time Visitor

## 3.1 Entry Point

Route:

```text
/
```

User goal:

- Understand the platform quickly.
- Choose a useful action.

Steps:

1. User lands on Home page.
2. User reads the main value proposition.
3. User chooses one of the main actions:
   - `Assess Resume`
   - `Track Profile`
   - `Browse Roadmaps`

Expected UI:

- Hero section with primary action.
- Feature cards.
- Simple architecture/process section.

Success outcome:

- User reaches one of the core workflows within one click.

Failure/edge cases:

- User does not know where to start.

Recommended solution:

- Make `Assess Resume` the strongest primary button.
- Keep `Track Profile` as secondary.
- Show `Browse Roadmaps` as a lower-friction option.

## 4. Flow 2: Track Coding Profile

## 4.1 Entry Point

Route:

```text
/track
```

User goal:

- See public coding activity from GitHub, LeetCode, and Codeforces.

## 4.2 Normal Flow

Steps:

1. User opens Track page.
2. Empty state asks for platform usernames.
3. User enters one or more usernames:
   - GitHub username.
   - LeetCode username.
   - Codeforces handle.
4. User clicks `Fetch Profile`.
5. Frontend validates that at least one username exists.
6. Frontend calls platform APIs through Flask.
7. Loading state appears.
8. Backend fetches data from requested platforms.
9. Frontend renders platform sections.
10. User reviews stats and charts.

Success result:

- GitHub section shows commits, pull requests, repositories, languages, language chart.
- LeetCode section shows solved problems by difficulty and ranking.
- Codeforces section shows rating, max rating, rank, contests, rating chart.

## 4.3 Partial Success Flow

Example:

- GitHub succeeds.
- LeetCode API fails.
- Codeforces was not provided.

Expected UI:

- GitHub panel renders normally.
- LeetCode panel shows an error state with `Retry LeetCode`.
- Codeforces panel is hidden or marked `Not provided`.

Important:

- Do not convert API failure into a silent zero score.
- Label missing data clearly.

## 4.4 Error Flow

Cases:

- No usernames entered.
- Username not found.
- Platform API unavailable.
- Backend timeout.

Expected behavior:

- If no usernames: show inline validation near form.
- If one platform fails: show per-platform error.
- If all fail: show error summary and keep form input.

## 4.5 End of Flow Actions

After viewing profile data, user can:

- Refresh one platform.
- Open public platform profile.
- Continue to `Assess Resume`.
- Browse learning roadmaps.

Recommended CTA:

```text
Use this profile in ATS Assessment
```

Future behavior:

- Store fetched profile snapshot and pass it into ATS flow.

## 5. Flow 3: ATS Resume Assessment

## 5.1 Entry Point

Route:

```text
/ats
```

User goal:

- Understand how well a resume matches a target job.
- Learn what to improve.

## 5.2 Normal Flow

Steps:

1. User opens ATS page.
2. User uploads resume file.
3. User pastes job description.
4. User optionally enters GitHub, LeetCode, and Codeforces usernames.
5. User clicks `Analyze Resume`.
6. Frontend validates required fields.
7. Frontend sends `multipart/form-data` to `/api/ats-analyze`.
8. Backend saves temporary resume.
9. Backend extracts resume text.
10. Backend fetches optional platform data.
11. Backend builds feature vector.
12. Backend runs ML model.
13. Backend generates SHAP explanation.
14. Backend identifies missing keywords.
15. Backend generates recommendations.
16. Frontend renders score, explanations, gaps, and platform evidence.

## 5.3 ATS Result Review Flow

After analysis, user sees:

1. Score summary.
2. Score band:
   - Strong Match.
   - Good Match.
   - Moderate Match.
   - Low Match.
3. Positive factors.
4. Negative factors.
5. Missing keyword chips.
6. Recommendations.
7. Roadmap links.

User actions:

- Click `View Recommendations`.
- Click `Open Roadmap`.
- Click `Analyze Another Resume`.
- Future: `Download Report`.
- Future: `Save Assessment`.

## 5.4 Validation Flow

Cases:

- Resume missing.
- Unsupported file type.
- Job description empty.
- Job description too short.

Expected UI:

- Show inline message.
- Scroll to first invalid field.
- Do not submit API request.

## 5.5 Backend Error Flow

Cases:

- Model not loaded.
- Resume text cannot be extracted.
- External API timeout.
- Unhandled backend error.

Expected UI:

- Show error panel above results area.
- Keep uploaded filename and form text if possible.
- Give a retry option.
- If model unavailable, show clear instruction:

```text
The ML model is not loaded. Please train or load the model before analysis.
```

## 5.6 Low Match Flow

If score is below 40:

Expected UI:

- Avoid discouraging wording.
- Show top 3 improvement actions.
- Link directly to beginner-friendly roadmaps.
- Explain missing platform data if no profiles were provided.

Suggested message:

```text
This role currently has several gaps. Start with the highest-impact skills below and reassess after updating your resume or projects.
```

## 5.7 Good Match Flow

If score is 60 or higher:

Expected UI:

- Show strengths first.
- Show targeted refinements.
- Encourage resume keyword alignment and project evidence.

## 5.8 End of Flow Actions

User can:

- Open a roadmap.
- Save the assessment in future.
- Download/share report in future.
- Reassess after improvements.

## 6. Flow 4: Learning Roadmaps

## 6.1 Entry Point

Routes:

```text
/learn
/learn/:slug
```

User goal:

- Find a structured learning path.

## 6.2 Browse Flow

Steps:

1. User opens Learn page.
2. User sees roadmap categories:
   - Role Based.
   - Skill Based.
3. User searches or filters roadmaps.
4. User clicks a roadmap card/button.
5. User opens roadmap detail page.

Expected UI:

- Search input.
- Filter tabs.
- Roadmap cards.
- Empty state if search has no results.

## 6.3 Roadmap Detail Flow

Steps:

1. User opens `/learn/:slug`.
2. User sees roadmap title.
3. User sees ordered topic list.
4. User expands a topic.
5. User reads description.
6. User opens resource links.

Expected UI:

- Back link.
- Topic accordion.
- Resource list.
- Link type badges.

## 6.4 Recommendation-to-Roadmap Flow

This is the most important roadmap entry point.

Steps:

1. User completes ATS assessment.
2. Recommendation card displays missing skill.
3. Card includes `Open Roadmap`.
4. User clicks roadmap link.
5. Roadmap opens at relevant topic if mapping exists.

Current behavior:

- Recommendations link to roadmap pages by topic slug.

Recommended future behavior:

- Deep link to exact roadmap topic.
- Example: `/learn/sql?topic=joins`

## 6.5 Roadmap Progress Flow

Future authenticated behavior:

1. User clicks `Mark as Planned`.
2. Recommendation appears in dashboard.
3. User clicks `Start`.
4. User marks topics complete.
5. User reassesses resume later.
6. Dashboard shows score improvement.

## 7. Flow 5: AI Career Coach

## 7.1 Current Flow

Route:

```text
/ai
```

Current behavior:

- Redirects to an external AI URL.

## 7.2 Future Flow

User goal:

- Ask conversational questions about score, resume, skills, and next steps.

Steps:

1. User opens AI page.
2. User selects context:
   - Latest ATS result.
   - Latest profile tracker data.
   - Current roadmap.
3. User chooses suggested prompt or types a question.
4. AI responds with specific guidance.
5. User saves useful recommendation.

Suggested prompts:

- `Explain my ATS score simply.`
- `What project should I build next?`
- `Which missing skill should I learn first?`
- `Rewrite my resume summary for this role.`

Safety note:

- The AI coach should not claim to guarantee hiring outcomes.

## 8. Flow 6: Returning Student Dashboard

Future route:

```text
/dashboard
```

User goal:

- Track improvement over time.

## 8.1 Normal Flow

Steps:

1. Student logs in.
2. Dashboard loads latest saved data.
3. Student sees:
   - Profile completeness.
   - Latest ATS score.
   - Active recommendations.
   - Roadmap progress.
   - Platform activity.
4. Student continues an action:
   - Refresh profile.
   - Reassess resume.
   - Continue roadmap.

## 8.2 Dashboard Cards

Cards:

- Latest Match Score.
- Profile Completeness.
- Active Skill Gaps.
- Roadmap Progress.
- Platform Activity.
- Recent Assessments.

## 8.3 Improvement Loop

Recommended loop:

```text
Assessment
  -> Recommendation
  -> Roadmap
  -> Project/resume update
  -> Reassessment
  -> Progress comparison
```

## 9. Flow 7: Counselor/Admin Dashboard

Future route:

```text
/admin
```

User goal:

- Understand student readiness and skill gaps at cohort level.

## 9.1 Normal Flow

Steps:

1. Counselor logs in.
2. Opens dashboard.
3. Selects filters:
   - Department.
   - Graduation year.
   - Role family.
4. Reviews analytics:
   - Average match score.
   - Common missing skills.
   - Students needing support.
   - Role readiness.
5. Opens individual student profile if permitted.
6. Assigns intervention or recommends roadmap.

## 9.2 Admin Views

Views:

- Cohort Overview.
- Skill Gap Heatmap.
- Student List.
- Assessment History.
- Recommendation Completion.
- Dataset Labelling Queue.
- Model Metrics.

## 9.3 Important Privacy Rule

Counselors should only see student data with institutional permission and student consent. Resume text should be hidden or redacted unless explicitly needed.

## 10. Flow 8: Expert Labelling for Real Data

Future route:

```text
/admin/labels
```

User goal:

- Label student-job pairs for real model training.

## 10.1 Normal Flow

Steps:

1. Expert reviewer logs in.
2. Opens labelling queue.
3. Sees anonymized student profile and job description.
4. Reviews resume evidence, platform metrics, and job requirements.
5. Assigns score from 1 to 5.
6. Adds optional notes.
7. Submits label.
8. Next pair loads.

## 10.2 Label Scale

| Score | Meaning |
| --- | --- |
| 1 | Poor fit |
| 2 | Weak fit |
| 3 | Moderate fit |
| 4 | Good fit |
| 5 | Excellent fit |

Training rule:

- Average three reviewer scores.
- `Match = 1` when average score is at least 3.5.

## 10.3 Reviewer Safeguards

- Hide student name when possible.
- Randomize label order.
- Track reviewer disagreement.
- Allow reviewer to flag unclear resumes/jobs.

## 11. Cross-Page Navigation Rules

Recommended primary paths:

```text
Home -> ATS
Home -> Track
Home -> Learn
Track -> ATS
ATS -> Learn
Learn -> ATS
Dashboard -> ATS
Dashboard -> Learn
```

Navbar links:

- Track.
- Learn.
- Assess.
- AI.
- Privacy.

Context passing:

- If user enters usernames on Track, carry them into ATS when possible.
- If ATS generates recommendations, pass recommended roadmap slug to Learn.
- If user opens roadmap from recommendation, show a small banner:

```text
Recommended because your ATS result identified SQL as a skill gap.
```

## 12. State Persistence Rules

Without login:

- Keep form state in memory.
- Optional: store usernames in local storage after user consent.
- Do not store resume text in local storage.

With login:

- Save assessments to database.
- Save recommendation progress.
- Save roadmap progress.
- Save profile handles.

Sensitive data:

- Never store raw resume content in browser local storage.
- Avoid exposing API keys in frontend.

## 13. Empty States

Home:

- No empty state needed.

Track:

- `Enter your platform usernames to fetch your profile.`

ATS:

- Before analysis, show form only.
- Results area hidden until analysis.

Learn:

- If no search result: `No roadmap found for this search.`

Roadmap detail:

- If slug invalid: `Roadmap not found.`

Dashboard:

- `No assessments yet. Start by analyzing your resume.`

## 14. Loading States

Track:

- Loading text should mention platform fetch.

ATS:

- Multi-step progress:
  - Uploading.
  - Parsing.
  - Fetching profiles.
  - Running model.
  - Explaining result.
  - Building recommendations.

Learn:

- Simple skeleton list if roadmap API is used.

Dashboard:

- Skeleton cards.

## 15. Error Recovery

Rules:

- Keep user input after errors.
- Show retry buttons for API failures.
- Show platform-specific errors for Track.
- Show field-level validation for forms.
- Show technical details only behind an expandable section.

Examples:

- `Retry GitHub`.
- `Try another file`.
- `Back to Roadmaps`.
- `Run analysis again`.

## 16. Success Criteria

The user flows are successful when:

- A new user can reach ATS assessment in one click from Home.
- A student can fetch at least one platform profile without understanding APIs.
- A student can upload resume and receive a result.
- The ATS result explains both strengths and gaps.
- Every recommendation has an action.
- Roadmap navigation is clear.
- Missing or failed data is labelled honestly.
- The system encourages improvement and reassessment.

