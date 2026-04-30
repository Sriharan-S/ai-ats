# AIATS — Project Overview & Application Logic

A plain-language guide to what this product does, why it exists, who it's
for, and how every part of it actually works in practice. No code, no APIs,
no library names — just the workflow.

---

## 1. The Problem

Two things are broken at the same time in early-career hiring.

**On the student side:**
- Students apply to dozens of jobs without ever knowing *why* they were
  rejected. ATS scanners filter their resumes silently.
- Their real evidence of capability — commits on GitHub, problems solved on
  LeetCode, contests on Codeforces — never makes it into the hiring decision
  because nobody is connecting that data to the resume.
- Generic career advice ("learn DSA", "build projects") doesn't tell them
  *which* skill, *for which* role, in *what* order.

**On the recruiter / institution side:**
- Resumes claim skills the candidate has never actually used.
- A keyword-only ATS rewards resume-stuffing and punishes genuine builders
  who didn't word things "the right way".
- There's no signal about whether the candidate's actual public work backs
  up what they wrote.

**The gap:** there is no single place where a student's resume, their public
coding evidence, and a job description are evaluated together — and where
the result is explained back to them in a way they can act on.

---

## 2. The Solution

AIATS is a **student-facing career assistant** that takes three things —
a resume, a target job description, and (optionally) the student's public
coding handles — and produces:

1. A **match score** (0 to 100) that estimates how well the profile fits
   the job.
2. An **honest breakdown** of which factors pushed the score up and which
   pulled it down.
3. **Specific next steps**, including links to learning roadmaps, that
   would close the gap if the student followed them.

The product is positioned as a *coaching tool*, not an automated rejection
system. Students see scores, reasons, and a path forward. They are never
told "you're not good enough." They're told "here's the gap, here's the
roadmap, here's the project to build."

---

## 3. Who It's For

- **Students** preparing for placements / internships, who want to know
  where they stand against a real job description before applying.
- **Self-learners** who want their existing GitHub / LeetCode / Codeforces
  activity to show up as evidence of skill, not just a username on the
  resume.
- **Career counsellors and placement cells** who want a way to give
  cohort-level guidance backed by real signals rather than gut feel
  *(this surface is in the roadmap, not yet shipped).*

---

## 4. The Three User Workflows

The product has three first-class flows. Each is reachable from the home
page and works on its own; combining them is what gives the strongest
result.

### 4.1 Profile Tracker

**Goal:** show a student what their public coding life looks like in one
place.

**What the user does:**
1. Enters one or more handles — GitHub username, LeetCode username,
   Codeforces handle.
2. Hits "Fetch Profiles".

**What the product does:**
1. For each platform the user supplied, it reaches out to that platform's
   public data source and pulls authentic, traceable signals — total
   commits, pull requests, repositories, the languages those repos are
   actually written in, problems solved at each difficulty, contest
   rating, contest history, and recent submission timestamps.
2. It is honest about what it could *not* find. For each platform it
   reports one of the following statuses, and the UI renders each
   distinctly:
   - *Connected* — data was fetched successfully.
   - *User not found* — the platform itself said this username does not
     exist.
   - *Rate limited* — the platform throttled the request; the student is
     told to try again later.
   - *Upstream timeout / Upstream error* — the platform was unreachable.
   - *Auth required* — the request was rejected by the platform.
3. It never silently substitutes zeros for failures, which is what most
   demo trackers do. A failed fetch is shown as a failed fetch.

**What the user gets:**
- For GitHub: a count of commits, PRs, repos, and a chart of language
  distribution by actual byte share across their repositories.
- For LeetCode: total solved, an easy/medium/hard donut, ranking, contest
  rating, and a list of recent submissions with timestamps.
- For Codeforces: current and max rating, rank, contest count, a rating
  history chart over their last twelve contests, and the average problem
  difficulty of their recent accepted submissions.

This is the "I exist as a developer" view.

### 4.2 ATS Assessment

**Goal:** answer "how well does my resume + my real evidence match this
specific job?"

**What the user does:**
1. Uploads a resume (PDF or DOCX).
2. Pastes a job description.
3. Optionally enters one or more coding-platform handles.
4. Hits "Analyze".

**What the product does:**
1. Stores the uploaded file in a private, temporary location with a
   randomized filename.
2. Extracts plain text from the resume.
3. If the user supplied platform handles, fetches each platform in
   parallel — same logic as the Profile Tracker, with the same explicit
   per-platform status outcomes.
4. Builds a **feature vector** — a fixed-shape numeric snapshot — that
   captures both the text alignment between resume and job description
   *and* the strength of the public evidence. (See §5 for the full list.)
5. Feeds the vector into the scoring model and gets back a 0–100 score
   and a contribution from each individual feature.
6. Computes which job-description keywords are missing from the resume,
   then maps each gap to a learning roadmap.
7. Deletes the uploaded file from disk before responding.

**What the user gets:**
- A headline score (Strong / Good / Moderate / Low Match).
- An "Executive Summary" sentence written based on the score band, plus
  small print showing exactly which model version produced the result so
  the same upload never feels mysterious.
- An **Explanation tab** with two charts:
  - Top positive factors — features that pushed the score up.
  - Top negative factors — features that pulled the score down.
  - A horizontal bar chart of every feature's contribution.
- A **Skill Gaps & Actions tab** — one card per gap, with concrete
  advice, an action item, and a "View Roadmap" button when the gap maps
  to a learning path that exists.
- A **Platform Evidence tab** — for each platform, the literal status
  (*Fetched* / *Not provided* / *User not found* / *Unavailable: rate
  limit* / etc.) plus the numbers that fed into the score.

### 4.3 Learning Roadmaps

**Goal:** turn "you're missing X" into "here's how to learn X."

**What the user does:**
- Browses or searches the roadmap library.
- Filters by Role-Based (Frontend, Backend, DevOps, AI Engineer, etc.) or
  Skill-Based (Python, SQL, Git, System Design, etc.).
- Clicks into a roadmap to see its topics, descriptions, and curated
  resource links.

**Where roadmaps come from:**
- The product ships with a curated library of roadmap definitions — one
  per skill or role — covering the topics needed to be employable in that
  area, the order to learn them in, and links to articles, videos, and
  documentation.

**How roadmaps connect back to the assessment:**
- Every gap surfaced by the ATS Assessment carries the slug of a roadmap
  *only if that roadmap actually exists in the library*. The product
  refuses to promise a link that would 404. If no roadmap exists for a
  given missing keyword, the gap is still shown so the student knows the
  keyword is required, but the next-step is generic ("read official docs,
  build one project") rather than a link to nowhere.

---

## 5. The Analysis Pipeline (End-to-End)

This is what happens behind the scenes from the moment a student clicks
*Analyze* to the moment they see their result.

### Stage 1 — Intake

- The resume file is validated:
  - Right format? (PDF or DOCX only)
  - Under the size limit?
  - Was a job description actually pasted?
- If anything is wrong, the user gets a precise, named error — not a
  generic "something failed". Examples: *Resume required*, *Resume file
  empty*, *Job description required*, *Resume format unsupported*,
  *Resume could not be read*.
- The file is saved with a random filename in a private upload area.

### Stage 2 — Resume Reading

- The text content is extracted from the resume.
- If the file is a scan / image-only PDF, text extraction returns nothing
  and the user gets a clear "we couldn't read this resume" message — not
  a wrong score.

### Stage 3 — Public Evidence Collection

- For each platform handle the user supplied, a fetch is attempted. Every
  fetch is wrapped with retries, timeouts, and rate-limit handling.
- Every fetch returns one of the seven statuses (success, not found, rate
  limited, unauthorized, timeout, error, not requested).
- These statuses are remembered all the way through to the final response,
  so the UI can show the user *exactly* why a platform is or isn't
  contributing to their score.

### Stage 4 — Feature Construction

This is where everything the product knows about the student gets reduced
to a fixed-shape numeric snapshot the model can score. There are five
families of features:

**Text-alignment features** — the heart of the score for resume-only users:
- *Skill-keyword density* — how many of the meaningful keywords in the
  job description also appear in the resume.
- *Project-skill overlap* — a similarity measure between the resume's
  language and the job description's language as a whole.
- *Resume skills count*, *Job description skills count* — how many
  identifiable technical skills appear in each.
- *Resume word count* — a rough indicator of resume completeness.

**GitHub features:**
- Total commits (real, fetched from search — never fabricated).
- Total pull requests.
- Total public repositories.
- Number of distinct programming languages used.
- *Commit consistency score* — does the student commit regularly, or in
  one giant burst?
- *Skill validation ratio* — how many skills claimed on the resume are
  actually backed by a language used in the student's repos.

**LeetCode features:**
- Total problems solved, plus separate easy/medium/hard counts.
- Hard ratio and medium ratio (the difficulty mix matters more than the
  raw count).
- Ranking.
- *Problem-solving velocity* — how many problems they've solved recently,
  per week.

**Codeforces features:**
- Current and max rating.
- Contest count.
- Average difficulty of recent accepted problems.

**Honesty features (missingness flags):**
- Did the student provide a GitHub / LeetCode / Codeforces profile at all?
- Did the fetch fail (was the platform unreachable / rate-limited)?

These flags are crucial. Without them the model can't tell the difference
between "this student has no GitHub" and "this student has GitHub but we
couldn't reach it just now". With them, the model treats the two cases
distinctly and never floors a student's score for an outage.

### Stage 5 — Scoring

- The feature vector is handed to a model that predicts a continuous
  0–100 *match score* directly. The score is interpreted as "how well
  this resume + evidence matches this job description", not as a
  probability of being hired.
- The score is computed in a way that respects how recruiters actually
  read ATS results:
  - Text alignment with the job description is the dominant signal.
  - Public-platform evidence is a bonus when present.
  - A student who provides only a resume + JD with strong keyword match
    can still earn a *Good Match* score; missing platforms are not
    treated as failure.
  - A student who provides handles but the upstream platform is down
    receives a small adjustment, not a collapse.

### Stage 6 — Explanation

The product never returns a score without explaining *why*. For every
feature in the vector, the model reports its individual contribution to
the prediction — positive (helped the score) or negative (hurt the score).
These contributions are honest in the strict sense that they sum to the
prediction itself; they're not a post-hoc story.

The explanation surfaces:
- The top features that helped the score (positive factors).
- The top features that hurt the score (negative factors).
- The full breakdown for the user who wants to scroll the list.

This is what powers the recommendations.

### Stage 7 — Recommendations

The product looks at the negative factors and produces actionable advice.

- For each negative factor, the recommender consults a built-in mapping
  from the factor to a category of advice. Example: a low *Skill-Keyword
  Match* triggers an advice card that names the actual top-3 missing
  keywords from this student's job description, not generic boilerplate.
- For each missing keyword from the job description, if a learning
  roadmap for that skill exists in the library, a roadmap link is
  attached. If not, a generic "read official docs, build one project"
  next-step is attached so the user is never left without somewhere to
  go.
- All gaps are sorted so the highest-impact gaps appear first. When two
  gaps have similar impact, the one with a real roadmap link wins, so
  actionable items lead.

### Stage 8 — Cleanup

- The uploaded resume is deleted from disk after the analysis finishes —
  pass or fail. The product does not retain the file.

### Stage 9 — Delivery

The student sees the final result with three parts:

1. The **score**, with a clear band label (Strong / Good / Moderate / Low
   Match).
2. The **explanation** (positive factors, negative factors, full feature
   chart).
3. The **gaps and actions** (advice cards, roadmap links).

Plus the small print: the model version, the feature version, and a
unique analysis ID. The same upload always leaves a trace the student or
admin can reference.

---

## 6. The Reasoning Layer (Why a Score Is What It Is)

This is the part of the product that exists specifically to keep it from
behaving like a black box.

**Every score has a transparent, complete explanation.** Three properties
of how the explanation is built make this real, not decorative:

1. **The model and the explanation see the same thing.** The features fed
   into the score and the features fed into the explanation are
   identical. There is no preprocessing layer in between that would make
   the explanation describe a different input than the model used.
2. **The contributions add up to the prediction.** Each feature's
   contribution is its real share of the prediction. Add the
   contributions together with the model's baseline and you reconstruct
   the score itself. This isn't a marketing claim — it's tested.
3. **No fabricated inputs.** If GitHub returns very few recent events,
   the product does *not* multiply the repo count by a fudge factor and
   call that "commits". It reports the real number from the proper
   source. The ones the product makes up are zero.

The explanation is what makes recommendations possible. We can say "your
top blocker right now is the keyword match — these three keywords from
the job description aren't on your resume" because the model literally
told us so.

---

## 7. The Recommendation Engine (Why It Doesn't Hand-Wave)

A common pattern in ATS-style products is to wrap a generic LLM call and
return generic advice. AIATS does the opposite: it pulls advice from a
finite, audited mapping of "negative factor → advice → roadmap topic"
that the team controls.

**Three properties that matter:**

1. **Keyword-specific advice.** When the negative factor is *Skill-Keyword
   Match*, the advice cites the actual missing keywords from this job
   description. The user doesn't see "your resume is missing critical
   keywords" — they see "your resume is missing: docker, sql, aws".
2. **Verified roadmap links.** Every roadmap link the product offers has
   been verified against the on-disk roadmap library at the moment of the
   request. If the roadmap doesn't exist, no link is shown. The user
   never gets a 404.
3. **Stable ordering.** Highest impact gaps lead. When impacts are close,
   gaps that map to a real roadmap come before generic ones, so the
   student's next click is always actionable.

---

## 8. Data Lifecycle

What the product stores and what it doesn't.

**During an assessment:**
- The resume file is held only as long as it takes to extract its text.
  It is deleted whether the analysis succeeded or failed.
- Platform data (GitHub / LeetCode / Codeforces) is fetched live. The
  product does not keep a long-term copy of it.
- The analysis result is delivered to the student in the response. It is
  not persisted to a database in this version of the product.

**Future surface (acknowledged, not yet shipped):**
- Optional opt-in storage so a student can see their score history and
  whether their score improved after they followed a roadmap.
- A counsellor / placement-cell view aggregating cohort gaps with no
  individual identification by default.
- Real, labelled student-job pair data to train the model on actual
  hiring outcomes instead of a rule-based bootstrap dataset.

---

## 9. Honesty Boundaries (What's Modeled vs Measured vs Missing)

**Measured (real, fetched from the source):**
- Total commits, pull requests, repositories, and language byte
  distribution from GitHub's own search.
- Solved problem counts, ranking, contest rating, and recent submission
  timestamps from LeetCode.
- Rating, contest history, and recent submission verdicts/difficulties
  from Codeforces.
- Resume text from the uploaded file.

**Modeled (derived from real signals):**
- Commit consistency.
- Problem-solving velocity.
- Skill-keyword density between resume and job description.
- Resume-vs-GitHub skill validation.
- The 0–100 match score itself.

**Currently missing (and clearly labeled as such):**
- The training data is rule-based bootstrap data, not real student
  outcomes. The model card / metadata says so explicitly. Any metric
  produced on this dataset is an internal sanity check, not a research
  result.
- There is no longitudinal view — yet. We don't track whether following
  a recommendation actually moved a student's score in the next
  assessment.
- There is no counsellor dashboard yet.

The product is honest about the boundary between these three buckets at
every layer — in the API response, in the UI, and in the documentation.

---

## 10. Trust Properties the Product Commits To

These are the rules the product enforces on itself, not aspirations.

1. **No fabricated platform numbers.** If we don't know a value, the
   product reports zero with an explicit "fetch failed" / "not provided"
   status — not a guess.
2. **No silent failures.** If a platform is rate-limited or down, the
   user sees that in the UI distinctly from "user has no profile".
3. **No silent versioning.** Every assessment carries the model version,
   the feature version, and a unique analysis ID, so the same input can
   always be traced back to the same logic.
4. **No dead links.** Every roadmap link offered as a next step has been
   verified to exist at the moment it's offered.
5. **No retention by default.** Resumes are deleted after the analysis.
   Long-term storage is opt-in and not in this release.
6. **Transparent reasoning.** Every score is broken into per-feature
   contributions that add up to the score itself, not into a narrative
   generated after the fact.

---

## 11. End-to-End Walkthrough — One Student's Story

Let's follow Priya, a third-year CS student looking at a *Backend
Developer Intern* posting.

1. Priya opens AIATS, lands on the home page, and clicks **ATS
   Assessment**.
2. She uploads her resume PDF, pastes the backend intern job description,
   and types her GitHub username (`priya-dev`). She doesn't have a
   LeetCode or Codeforces account yet, so she leaves those empty.
3. The product accepts the upload, reads the text from the PDF, and
   reaches out to GitHub for `priya-dev`.
4. GitHub returns: 87 real commits across 5 repos, mostly Python with
   some HTML and JavaScript. The product does not pad this number.
5. The product builds Priya's feature vector. Her resume mentions
   *Python, Flask, REST APIs*, and the JD asks for *Python, FastAPI,
   PostgreSQL, Docker, Git*. The text alignment is decent but not
   perfect. The GitHub evidence backs Python well but doesn't show
   Docker or PostgreSQL.
6. The model scores Priya at **68 — Good Match**.
7. The Explanation tab shows her top positives are *Skill-Keyword Match*,
   *Skill Validation (Resume vs GitHub)*, and *GitHub Commits*. The top
   negatives are *Project-Job Description Overlap*, *LeetCode Problems
   Solved* (she has zero), and *Codeforces Rating* (also zero).
8. The Skill Gaps tab shows three concrete cards:
   - *Resume Keywords* — "Your resume is missing keywords required by
     this job: docker, postgresql." Action: add a project that uses both.
   - *Active Practice* — "Your recent problem-solving activity is low."
     Action: solve at least one problem daily for the next 30 days.
     Roadmap: links to the Python practice roadmap (verified to exist).
   - *Project-Job Description Overlap* — "Your project experience doesn't
     align well with this job description." Action: build a project that
     directly addresses the responsibilities in the job listing.
     Roadmap: links to the Backend roadmap.
9. The Platform Evidence tab shows GitHub *Fetched* with her real
   numbers, LeetCode *Not provided*, Codeforces *Not provided* — clear
   that the missing platforms aren't an outage, they're an opportunity.
10. The footer of the result shows `Model ats-v2.0.0 · Features
    features-v2.0.0 · Analysis 8b3f2a17`. If Priya re-uploads tomorrow
    and the score behaves differently, that ID is her receipt.
11. Priya clicks **View Roadmap** on the Backend gap, lands on the
    Backend roadmap page, expands the *Databases* topic, and starts on a
    PostgreSQL tutorial.

A week later she ships a small Flask + PostgreSQL + Docker side-project
to her GitHub. She comes back to AIATS, runs the same assessment, and
this time her score reflects the new evidence.

---

## 12. What's Out of Scope (For Now)

To keep the product honest, here is what AIATS *deliberately does not do*:

- It does not promise to predict whether the student will be hired.
- It does not collect demographic or protected attributes; the score is
  not allowed to depend on them.
- It does not scrape private data — only public GitHub / LeetCode /
  Codeforces information, and only when the student gave a handle.
- It does not produce an LLM-style essay disguised as a "recommendation".
  Recommendations come from a controlled mapping with verifiable links.
- It does not sell any resume to anyone. The file is deleted after the
  assessment.
- It does not currently store assessment history. That's a future,
  opt-in feature.

---

## 13. The Roadmap For The Product Itself

Where the project is heading, in order of priority:

1. **Real labelled data.** Move from rule-based bootstrap data to a
   labelled dataset of real student-job pairs reviewed by experts.
2. **Score history.** Let students opt in to keep a record of past
   assessments so they can see "before / after I followed the roadmap".
3. **Counsellor view.** Cohort dashboards for placement cells, with no
   individual student identification by default — focused on aggregate
   skill gaps by role.
4. **Smarter resume parsing.** Extract structured sections (Education,
   Experience, Projects, Skills, Achievements) and let features score
   the relevant section instead of the resume as a whole.
5. **More platforms.** HackerRank, Kaggle, Stack Overflow reputation, and
   PR review activity, all opt-in.
6. **Outcome tracking.** Did the student get the interview? The offer?
   This is the only way to validate the model against ground truth.

---

## 14. Summary — In One Paragraph

AIATS is a coaching tool that turns a student's resume, target job
description, and public coding evidence into a transparent 0–100 match
score, an honest breakdown of why the score is what it is, and a set of
concrete next steps backed by curated learning roadmaps. It is built on
real platform data, not fabricated counts; explains every result through
contributions that add up to the score itself; verifies every learning
link before offering it; deletes uploads after analysis; and is upfront
in both the UI and the documentation about which numbers are measured,
which are modeled, and what the product still doesn't know.
