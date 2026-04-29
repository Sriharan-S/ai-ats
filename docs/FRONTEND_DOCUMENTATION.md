# AIATS Frontend Documentation

## 1. Purpose

This document defines the target frontend for the AIATS / Raven project. It describes the pages, navigation, buttons, forms, views, scroll behavior, loading states, empty states, responsive behavior, and TypeScript component structure needed when migrating the current static HTML frontend to a TypeScript frontend.

The backend should remain Python/Flask. The frontend should move to a TypeScript application, preferably Vite + React + TypeScript.

## 2. Frontend Goals

The frontend should help students do four main things:

1. Understand what the platform does.
2. Track coding profiles across GitHub, LeetCode, and Codeforces.
3. Assess a resume against a job description using the ML ATS system.
4. Follow personalized or browsable learning roadmaps.

The experience should feel like a practical student career dashboard, not only a landing page. The first priority is usability: upload, analyze, review, improve, and track progress.

## 3. Site Map

Target routes:

| Route | Page | Purpose |
| --- | --- | --- |
| `/` | Home | Introduce the product and route users to core workflows |
| `/track` | Profile Tracker | Fetch and display platform analytics |
| `/ats` | ATS Assessment | Upload resume, enter job description, receive score and recommendations |
| `/learn` | Roadmap Library | Browse role-based and skill-based roadmaps |
| `/learn/:slug` | Roadmap Detail | View roadmap topics, descriptions, and resource links |
| `/ai` | AI Assistant | Future AI career coach or external AI route |
| `/privacy` | Privacy | Explain data handling, resume upload, API data, and consent |
| `/contact` | Contact | Support/contact form or static contact details |
| `/dashboard` | Student Dashboard | Future authenticated profile overview |
| `/admin` | Admin/Counselor Dashboard | Future cohort analytics and labelling tools |

Minimum migration scope:

- `/`
- `/track`
- `/ats`
- `/learn`
- `/learn/:slug`
- `/privacy`

## 4. Global Layout

### 4.1 Navbar

The navbar should be visible on every page.

Elements:

- Brand/logo button: `Raven` or final project name.
- Navigation links:
  - Track
  - Learn
  - Assess
  - AI
  - Privacy
- Mobile menu button.
- Optional future profile button after authentication.

Behavior:

- Sticky at top.
- Active page link highlighted.
- Mobile nav collapses behind a menu button.
- Clicking the brand navigates to `/`.
- Keyboard accessible with visible focus state.

Recommended TypeScript component:

```text
components/layout/AppShell.tsx
components/layout/Navbar.tsx
components/layout/MobileNav.tsx
```

### 4.2 Footer

Elements:

- Project name.
- Short description.
- Links: Privacy, Contact, GitHub/project repository if available.
- Version/build label in small text.

Behavior:

- Footer appears after main content.
- On short pages, footer should stay visually near bottom.
- On long pages, footer appears after all scrollable content.

### 4.3 Main Content Width

Suggested layout widths:

- Home page: max width 1120px.
- Track page: max width 960px.
- ATS page: max width 900px.
- Roadmap pages: max width 800px.
- Admin/dashboard pages: max width 1200px.

### 4.4 Shared States

Every API-driven page should support:

- Idle state.
- Loading state.
- Success state.
- Empty state.
- Partial success state.
- Error state.

Example:

- Track page can show GitHub data while LeetCode fails.
- ATS page can show resume parse error without clearing the form.
- Roadmap page can show a not-found state for unknown slugs.

## 5. Home Page

Route: `/`

### 5.1 Purpose

The Home page should quickly explain the value of the project and route students into the main actions.

### 5.2 Page Sections

1. Hero section.
2. Primary action buttons.
3. Feature overview.
4. System flow / architecture summary.
5. Footer.

### 5.3 Hero Section

Elements:

- Product badge or small status text.
- Main heading.
- Supporting description.
- Primary button: `Assess Resume`.
- Secondary button: `Track Profile`.
- Optional third link: `Browse Roadmaps`.

Button behavior:

- `Assess Resume` navigates to `/ats`.
- `Track Profile` navigates to `/track`.
- `Browse Roadmaps` navigates to `/learn`.

Visual behavior:

- The hero should fit in the first viewport with a hint of the feature section below.
- Avoid making the page only a marketing hero. It should quickly lead to usable workflows.

### 5.4 Feature Overview

Cards:

1. Profile Tracking
   - Description: GitHub, LeetCode, Codeforces analytics.
   - Button/link: `Track Progress`.
2. ATS Assessment
   - Description: Resume and job description matching.
   - Button/link: `Try ATS`.
3. Explainable AI
   - Description: SHAP factors explain why the score changed.
   - Button/link: `See Analysis`.
4. Learning Roadmaps
   - Description: Recommendations mapped to learning paths.
   - Button/link: `Browse Roadmaps`.

### 5.5 Architecture Summary

Show a simple step flow:

1. Student enters profile handles and uploads resume.
2. Backend fetches public platform data.
3. Resume and job description are parsed.
4. ML model builds features and predicts match score.
5. SHAP explains positive and negative factors.
6. Recommendations link to learning roadmaps.

### 5.6 Scroll Behavior

- Normal page scroll.
- Navbar remains sticky.
- Primary actions should be visible without scrolling on desktop.
- On mobile, the hero can scroll naturally, but buttons must remain near the top.

## 6. Profile Tracker Page

Route: `/track`

### 6.1 Purpose

The Profile Tracker page lets students enter platform usernames and view coding profile analytics from GitHub, LeetCode, and Codeforces.

### 6.2 Main Views

1. Input view.
2. Empty state.
3. Loading overlay.
4. Results view.
5. Partial error view.

### 6.3 Input Section

Fields:

| Field | Type | Required | Placeholder |
| --- | --- | --- | --- |
| GitHub username | Text input | Optional | `e.g. sriharan2544` |
| LeetCode username | Text input | Optional | `e.g. sriharan` |
| Codeforces handle | Text input | Optional | `e.g. sriharan` |

Buttons:

- Primary button: `Fetch Profile`.
- Secondary button: `Clear`.
- Optional button: `Use Sample Data`.

Validation:

- At least one username must be entered.
- Trim whitespace.
- Show inline validation under the form if all fields are empty.
- Disable `Fetch Profile` while loading.

Keyboard behavior:

- Pressing Enter in any input should trigger `Fetch Profile`.
- Escape can clear validation messages but should not clear typed input.

### 6.4 Empty State

Shown before first search.

Elements:

- Icon or simple illustration.
- Title: `Enter your platform usernames`.
- Text: Explain that the student can fetch public coding activity.
- Optional small examples for GitHub, LeetCode, Codeforces.

### 6.5 Loading State

Current UI has a full-screen loading overlay. In TypeScript version:

- Show a loading overlay or inline loading panel.
- Text should update by platform:
  - `Fetching GitHub profile...`
  - `Fetching LeetCode profile...`
  - `Fetching Codeforces profile...`
  - `Building dashboard...`

Button behavior:

- `Fetch Profile` disabled.
- Inputs remain visible but disabled or read-only.

### 6.6 Results View

Results should be divided into platform sections.

#### GitHub Section

Header:

- GitHub icon.
- Title: `GitHub`.
- Badge with username.
- Status badge: `Connected`, `Not found`, `Unavailable`, or `Not provided`.

Stat cards:

- Commits.
- Pull Requests.
- Repositories.
- Languages.

Charts:

- Language distribution chart.
- Optional future chart: commit timeline.

Additional elements:

- Top repositories list.
- Last updated timestamp.
- Link button: `Open GitHub Profile`.

Buttons:

- `Refresh GitHub`.
- `Open Profile`.
- Optional `View Raw Data` for debugging/admin mode.

#### LeetCode Section

Header:

- LeetCode label/icon.
- Title: `LeetCode`.
- Username badge.
- Status badge.

Stat cards:

- Total Solved.
- Easy.
- Medium.
- Hard.
- Ranking.

Charts:

- Donut chart for Easy/Medium/Hard.
- Optional future chart: solved over time.

Buttons:

- `Refresh LeetCode`.
- `Open LeetCode Profile`.

#### Codeforces Section

Header:

- Codeforces label/icon.
- Title: `Codeforces`.
- Username badge.
- Status badge.

Stat cards:

- Current Rating.
- Max Rating.
- Rank.
- Contests.

Charts:

- Rating history line chart.

Buttons:

- `Refresh Codeforces`.
- `Open Codeforces Profile`.

### 6.7 Partial Success Behavior

If one API fails:

- Show successful platform sections normally.
- Show failed platform section with an error panel.
- Error panel should include:
  - What failed.
  - Possible reason.
  - Retry button.

Example:

```text
LeetCode profile could not be fetched. The API may be unavailable or the username may be incorrect.
```

### 6.8 Scroll Behavior

- After successful fetch, scroll to the first available platform section.
- If there is an error, scroll to the error summary above results.
- Platform sections stack vertically.
- On desktop, charts and stat cards can sit inside the same section.
- On mobile, stat cards use two columns, charts full width.

### 6.9 TypeScript Components

```text
pages/TrackPage.tsx
components/profile/ProfileSearchForm.tsx
components/profile/PlatformStatusBadge.tsx
components/profile/GitHubPanel.tsx
components/profile/LeetCodePanel.tsx
components/profile/CodeforcesPanel.tsx
components/profile/StatCard.tsx
components/charts/LanguageChart.tsx
components/charts/LeetCodeDifficultyChart.tsx
components/charts/CodeforcesRatingChart.tsx
```

## 7. ATS Assessment Page

Route: `/ats`

### 7.1 Purpose

The ATS Assessment page lets students upload a resume, paste a job description, optionally connect public coding profiles, and receive:

- Job match score.
- Positive factors.
- Negative factors.
- Missing keywords.
- Skill-gap recommendations.
- Roadmap links.

### 7.2 Main Views

1. Input form.
2. Loading analysis view.
3. ML results view.
4. Error view.

### 7.3 Input Form

Fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| Resume | File input | Required | Accept `.pdf`, `.docx` |
| Job Description | Textarea | Required | Minimum recommended length: 100 characters |
| GitHub Username | Text input | Optional | Adds platform evidence |
| LeetCode Username | Text input | Optional | Adds problem-solving evidence |
| Codeforces Handle | Text input | Optional | Adds contest evidence |

Buttons:

- Primary: `Analyze Resume`.
- Secondary: `Clear Form`.
- Optional: `Load Sample Job`.
- Optional: `Paste from Clipboard`.

Validation:

- Resume file is required.
- File must be PDF or DOCX.
- Job description is required.
- Job description should not be too short.
- File size should be checked before upload.
- Display validation inline near the affected field.

Button behavior:

- `Analyze Resume` disabled until required inputs are valid.
- During upload, button shows loading text.
- `Clear Form` resets resume, job description, usernames, results, and errors.

### 7.4 Loading Analysis View

Use a multi-step progress panel.

Steps:

1. Uploading resume.
2. Extracting resume text.
3. Fetching public platform data.
4. Building feature vector.
5. Running ML model.
6. Generating SHAP explanations.
7. Preparing recommendations.

Behavior:

- Show current step.
- Keep form values intact.
- Allow cancel only if backend supports request cancellation later.
- Prevent duplicate submissions.

### 7.5 Results Summary

Top result panel:

- Circular score gauge.
- Score value from 0 to 100.
- Score label:
  - `Strong Match`: 80-100.
  - `Good Match`: 60-79.
  - `Moderate Match`: 40-59.
  - `Low Match`: 0-39.
- One-sentence summary from recommendations.

Buttons:

- `Analyze Another Resume`.
- `Download Report` future feature.
- `Save Assessment` future authenticated feature.
- `View Recommendations`.

Scroll behavior:

- After successful analysis, scroll to the score summary.
- `View Recommendations` scrolls to recommendations section.

### 7.6 Results Tabs

Target tabs:

1. `AI Score`
2. `Explanation`
3. `Skill Gaps`
4. `Platform Evidence`

Tab behavior:

- Tabs should be buttons, not links.
- Active tab clearly highlighted.
- Keyboard accessible with arrow navigation if possible.
- URL query can optionally preserve active tab, such as `/ats?tab=explanation`.

### 7.7 Explanation View

Purpose:

Show why the score was produced.

Elements:

- Positive factors list.
- Negative factors list.
- SHAP bar chart.
- Plain-language explanation panel.

Positive factor card:

- Feature name.
- SHAP impact value.
- Short explanation.

Negative factor card:

- Feature name.
- SHAP impact value.
- Why it hurts.
- Suggested action if available.

Chart:

- Horizontal bars.
- Positive values in green.
- Negative values in red.
- Bars sorted by absolute impact.

### 7.8 Skill Gaps View

Elements:

- Missing keyword chips.
- Recommendation cards.
- Priority badges.
- Roadmap links.

Missing keyword chips:

- Render each missing skill as a chip.
- Clicking a chip can filter recommendations related to that skill in the future.

Recommendation card:

- Priority badge.
- Skill name.
- Advice.
- Action.
- Roadmap button if available.

Buttons:

- `Open Roadmap`.
- `Mark as Planned` future authenticated feature.
- `Mark Complete` future authenticated feature.

### 7.9 Platform Evidence View

Show the platform data that contributed to the score.

Sections:

- GitHub summary.
- LeetCode summary.
- Codeforces summary.

Each section should show:

- Whether username was provided.
- Whether fetch succeeded.
- Main metrics used by the model.
- Warning if data is missing.

Important behavior:

- Missing platform data should be explained as `Not provided` or `Unavailable`, not silently displayed as zero.

### 7.10 Error View

Possible errors:

- No resume uploaded.
- Unsupported file format.
- Resume text extraction failed.
- Job description empty.
- ML model not loaded.
- Platform API timeout.
- Backend server error.

Error view elements:

- Clear title.
- Human-readable message.
- Technical details hidden behind `Show details`.
- Retry button.
- Keep form values.

### 7.11 Scroll Behavior

- Input form starts at top.
- During analysis, do not jump until result is ready.
- On success, smooth scroll to score summary.
- On validation error, scroll to first invalid field.
- On backend error, scroll to error panel.
- Long recommendation lists should use normal page scroll, not nested scroll boxes.

### 7.12 TypeScript Components

```text
pages/AtsPage.tsx
components/ats/AtsUploadForm.tsx
components/ats/AnalysisProgress.tsx
components/ats/ScoreGauge.tsx
components/ats/ResultsTabs.tsx
components/ats/ShapBarList.tsx
components/ats/MissingKeywordChips.tsx
components/ats/RecommendationList.tsx
components/ats/RecommendationCard.tsx
components/ats/PlatformEvidencePanel.tsx
components/common/ErrorPanel.tsx
components/common/EmptyState.tsx
```

## 8. Learning Roadmaps Page

Route: `/learn`

### 8.1 Purpose

The Roadmap Library page lets students browse predefined role-based and skill-based learning paths.

### 8.2 Main Elements

- Page heading.
- Short description.
- Search input.
- Role-based category.
- Skill-based category.
- Roadmap buttons/cards.

Current roadmaps include examples such as:

- Frontend.
- Backend.
- DevOps.
- Full Stack.
- Data Analyst.
- Android.
- iOS.
- Cyber Security.
- UX Design.
- MLOps.
- React.
- Vue.
- Angular.
- JavaScript.
- Node.js.
- TypeScript.
- Python.
- SQL.
- System Design.
- API Design.
- Java.
- Git & GitHub.

### 8.3 Search and Filter

Add:

- Search input: `Search roadmaps...`
- Filter tabs:
  - `All`
  - `Role Based`
  - `Skill Based`
  - `Recommended`

Behavior:

- Search filters roadmap cards immediately.
- Empty search result shows a friendly empty state.
- Recommended tab appears when the user came from ATS recommendations or has saved gaps.

### 8.4 Roadmap Card/Button

Each roadmap item should show:

- Roadmap name.
- Category.
- Short description if available.
- Number of topics if known.
- Button: `Open`.

Behavior:

- Entire card clickable.
- `Open` navigates to `/learn/:slug`.

### 8.5 Scroll Behavior

- Normal page scroll.
- Search/filter bar should remain near top but does not need to be sticky in phase 1.
- On mobile, roadmap cards stack in one column.
- On desktop, use a responsive grid.

### 8.6 TypeScript Components

```text
pages/LearnPage.tsx
components/roadmaps/RoadmapSearch.tsx
components/roadmaps/RoadmapFilterTabs.tsx
components/roadmaps/RoadmapGrid.tsx
components/roadmaps/RoadmapCard.tsx
```

## 9. Roadmap Detail Page

Route: `/learn/:slug`

### 9.1 Purpose

Show the full learning path for a selected roadmap.

### 9.2 Main Elements

- Back link: `Back to Roadmaps`.
- Roadmap title.
- Optional summary.
- Topic list.
- Expandable topic rows.
- Resource links inside each topic.
- Progress controls in future authenticated version.

### 9.3 Topic Row

Each topic row should show:

- Topic number.
- Topic title.
- Expand/collapse icon.
- Optional status indicator:
  - Not started.
  - In progress.
  - Completed.

Expanded content:

- Description.
- Resource links.
- Link type badge, such as article, video, course, docs.

Buttons:

- `Open Resource`.
- `Mark Complete` future authenticated feature.

### 9.4 Scroll Behavior

- Clicking a topic expands it in place.
- Only one topic can be expanded at a time in simple mode, or multiple can be expanded if users prefer.
- The expanded topic should remain visible after clicking.
- Back link returns to `/learn` and should preserve search/filter state in future.

### 9.5 Empty and Error States

If roadmap slug is unknown:

- Show `Roadmap not found`.
- Button: `Back to Roadmaps`.

If roadmap has no topics:

- Show `No topics available yet`.

### 9.6 TypeScript Components

```text
pages/RoadmapDetailPage.tsx
components/roadmaps/RoadmapHeader.tsx
components/roadmaps/TopicAccordion.tsx
components/roadmaps/TopicItem.tsx
components/roadmaps/ResourceLinkList.tsx
```

## 10. AI Assistant Page

Route: `/ai`

### 10.1 Current State

The current `/ai` route redirects to an external URL.

### 10.2 Target Purpose

The AI page should become a career coach interface that can use:

- ATS result.
- Profile tracker data.
- Learning roadmap gaps.
- Student goals.

### 10.3 Page Elements

- Chat panel.
- Suggested prompts.
- Context panel showing active resume/profile/job.
- Buttons:
  - `Ask Career Coach`.
  - `Use Latest ATS Result`.
  - `Use Profile Tracker Data`.
  - `Clear Chat`.

### 10.4 Suggested Prompts

- `How can I improve my resume for this role?`
- `Which project should I build next?`
- `What should I learn this month?`
- `Explain my ATS score simply.`

### 10.5 Migration Priority

Low for phase 1. Keep redirect or placeholder until the core Track, ATS, and Learn flows are complete.

## 11. Privacy Page

Route: `/privacy`

### 11.1 Purpose

Students need to understand what data is used, why, and how it is stored.

### 11.2 Page Sections

- What data is collected.
- Resume upload handling.
- Public platform data.
- API tokens and credentials.
- Data retention.
- Student consent.
- Delete data request.
- Limitations of AI scoring.

### 11.3 Buttons

- `Contact Support`.
- `Request Data Deletion` future workflow.
- `Back to Home`.

## 12. Contact Page

Route: `/contact`

### 12.1 Page Elements

- Contact heading.
- Project/team information.
- Contact email.
- Optional form:
  - Name.
  - Email.
  - Message.
  - Submit button.

### 12.2 Behavior

- If backend support is not available, keep it as static contact information.
- If a form is added, validate required fields and show success/error messages.

## 13. Future Student Dashboard

Route: `/dashboard`

### 13.1 Purpose

This page should appear after authentication and persistence are added.

### 13.2 Views

- Profile completeness.
- Latest ATS score.
- Saved resumes.
- Saved job descriptions.
- Connected platforms.
- Current recommendations.
- Roadmap progress.
- Score improvement over time.

### 13.3 Buttons

- `Upload New Resume`.
- `Assess New Job`.
- `Refresh Platforms`.
- `Continue Roadmap`.
- `Export Report`.

## 14. Future Admin/Counselor Dashboard

Route: `/admin`

### 14.1 Purpose

Help faculty/career counselors understand cohort-level readiness.

### 14.2 Views

- Cohort overview.
- Most common missing skills.
- Role readiness distribution.
- Students needing support.
- Labelling queue for expert reviewers.
- Model evaluation dashboard.

### 14.3 Buttons and Filters

- Department filter.
- Graduation year filter.
- Role family filter.
- Export CSV.
- Open student profile.
- Review label queue.

## 15. Shared UI Components

Recommended shared components:

```text
components/common/Button.tsx
components/common/IconButton.tsx
components/common/TextInput.tsx
components/common/TextArea.tsx
components/common/FileInput.tsx
components/common/Select.tsx
components/common/Tabs.tsx
components/common/Badge.tsx
components/common/StatCard.tsx
components/common/ErrorPanel.tsx
components/common/LoadingOverlay.tsx
components/common/EmptyState.tsx
components/common/PageHeader.tsx
components/common/SectionHeader.tsx
components/common/Card.tsx
```

Use consistent variants:

- Primary button.
- Secondary button.
- Quiet/text button.
- Danger button.
- Icon button.

## 16. API Integration Map

Frontend API calls:

| Page | Action | Endpoint |
| --- | --- | --- |
| Track | Fetch GitHub | `/api/track/github/:username` |
| Track | Fetch LeetCode | `/api/track/leetcode/:username` |
| Track | Fetch Codeforces | `/api/track/codeforces/:username` |
| Track | Fetch combined profile | `/api/profile` |
| ATS | Analyze resume | `/api/ats-analyze` |
| Learn | Fetch roadmap list | `/api/roadmaps` |
| Learn detail | Fetch roadmap | `/api/roadmaps/:slug` |
| Health | Backend status | `/api/health` |

Recommended approach:

- Keep existing endpoints during migration.
- Add roadmap API endpoints so the TypeScript frontend does not rely on Flask templates.
- Add consistent error shapes.

## 17. TypeScript Data Types

Create types in:

```text
frontend/src/api/types.ts
```

Core types:

```ts
export interface ApiError {
  error: string | {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

export interface GitHubProfile {
  total_commits: number;
  total_pull_requests: number;
  total_repos: number;
  total_languages: number;
  languages: string[];
  language_stats: Record<string, number>;
  commit_timestamps: string[];
  repos: string[];
}

export interface LeetCodeProfile {
  solved: number;
  easy: number;
  medium: number;
  hard: number;
  ranking: number;
  total_languages: number;
  recent_submissions: unknown[];
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

export interface AtsAnalysisResponse {
  score: number;
  shap_values: Record<string, number>;
  top_positive: Array<[string, number]>;
  top_negative: Array<[string, number]>;
  missing_keywords: string[];
  recommendations: RecommendationSummary;
  platform_data: {
    github: {
      total_commits: number;
      total_repos: number;
      languages: string[];
    };
    leetcode: {
      solved: number;
      ranking: number;
    };
    codeforces: {
      rating: number;
    };
  };
}

export interface RecommendationSummary {
  score: number;
  summary: string;
  priority: "low" | "medium" | "high" | "critical";
  gaps: RecommendationGap[];
  total_gaps: number;
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
```

## 18. Responsive Behavior

### 18.1 Desktop

- Navbar horizontal.
- Forms can use multi-column layout.
- Stat cards use 4-column rows.
- Charts use full card width.
- Recommendations can be two-column only if content remains readable.

### 18.2 Tablet

- Navbar may collapse depending on width.
- Forms become 2-column or 1-column.
- Stat cards use 2 columns.

### 18.3 Mobile

- Navbar collapsed.
- All forms one column.
- Buttons full width when helpful.
- Stat cards use 2 columns for short metrics, 1 column for long labels.
- Charts full width.
- SHAP bars should avoid tiny labels; use stacked layout:
  - Feature name on top.
  - Bar below.
  - Value at right.

## 19. Accessibility Requirements

Minimum requirements:

- Every input has a visible label.
- Buttons use real `<button>` elements.
- Links navigate; buttons perform actions.
- File input has accessible label and accepted formats.
- Error messages are connected to fields where possible.
- Loading states should announce status with `aria-live`.
- Tabs should expose selected state.
- Color should not be the only way to distinguish positive/negative impact.
- All interactive elements must be keyboard reachable.

## 20. Visual Design Rules

Keep the current dark dashboard style but make it more maintainable:

- Use design tokens for colors, spacing, radius, shadows, and typography.
- Avoid inline styles in React components.
- Use consistent card radius and button height.
- Keep charts readable on dark backgrounds.
- Use restrained motion.
- Avoid excessive gradients in data-heavy sections.

Recommended files:

```text
frontend/src/styles/tokens.css
frontend/src/styles/globals.css
frontend/src/styles/components.css
```

## 21. Frontend Migration Order

1. Create Vite React TypeScript app.
2. Add app shell, navbar, footer, routing.
3. Add API client and TypeScript response types.
4. Port `/track`.
5. Port `/ats`.
6. Add roadmap list API and port `/learn`.
7. Add roadmap detail API and port `/learn/:slug`.
8. Port home, privacy, and contact pages.
9. Add tests.
10. Retire static HTML pages after parity testing.

## 22. Testing Checklist

### Home

- Primary buttons navigate correctly.
- Navbar active link works.
- Mobile menu opens and closes.

### Track

- Empty form shows validation.
- One username fetch works.
- Multiple usernames fetch in parallel.
- API failure shows partial error.
- Charts render with empty and real data.
- Refresh button works per platform.

### ATS

- Missing resume shows validation.
- Unsupported file type is rejected.
- Missing job description shows validation.
- Submit sends `FormData`.
- Loading steps display.
- Score gauge renders.
- SHAP bars render positive and negative factors.
- Missing keyword chips render.
- Recommendation roadmap links work.
- Backend error does not clear form.

### Learn

- Roadmap list renders.
- Search filters roadmaps.
- Empty search state appears.
- Roadmap card opens detail page.

### Roadmap Detail

- Unknown slug shows not found.
- Topic expands and collapses.
- Resource links open correctly.
- Back link returns to roadmap list.

## 23. Deliverable Definition

The TypeScript frontend migration is complete when:

- Static HTML workflows are fully reproduced in TypeScript.
- Track, ATS, Learn, and Roadmap Detail pages work against Flask APIs.
- API responses are typed.
- Loading, empty, error, and success states are implemented.
- Mobile layout is usable.
- Basic frontend tests pass.
- Flask backend can either serve the built frontend or the frontend can be deployed separately.
