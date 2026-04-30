"""
Feature Engineering Module for AI-Powered Student Profile Tracker.

Creates high-signal predictive features from raw API data and resume text,
as described in the conference paper:
  - Commit Consistency Score
  - Problem-Solving Velocity
  - Skill Keyword Density
  - API Skill Validation Ratio
  - Project-Skill Overlap (TF-IDF cosine similarity)
"""

import numpy as np
from datetime import datetime, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re


def compute_commit_consistency_score(commit_timestamps: list) -> float:
    """
    Measures regularity of GitHub commits over time.
    A student who commits consistently (e.g., 5-10 commits every week)
    scores higher than one who uploads everything in a single day.

    Returns a score between 0.0 and 1.0.
    """
    if not commit_timestamps or len(commit_timestamps) < 2:
        return 0.0

    # Parse timestamps and sort
    dates = []
    for ts in commit_timestamps:
        if isinstance(ts, str):
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                dates.append(dt)
            except (ValueError, TypeError):
                continue
        elif isinstance(ts, datetime):
            dates.append(ts)

    if len(dates) < 2:
        return 0.0

    dates.sort()

    # Calculate gaps between consecutive commits (in days)
    gaps = [(dates[i + 1] - dates[i]).total_seconds() / 86400
            for i in range(len(dates) - 1)]

    if not gaps:
        return 0.0

    mean_gap = np.mean(gaps)
    std_gap = np.std(gaps)

    # Coefficient of variation (lower = more consistent)
    if mean_gap == 0:
        return 1.0

    cv = std_gap / mean_gap

    # Convert to 0-1 score: low CV = high consistency
    # Use sigmoid-like transformation
    consistency = 1.0 / (1.0 + cv)

    # Bonus for having many commits
    volume_bonus = min(len(dates) / 100, 0.2)  # up to 0.2 bonus for 100+ commits

    return min(consistency + volume_bonus, 1.0)


def compute_problem_solving_velocity(submissions: list, window_days: int = 30) -> float:
    """
    Measures the number of problems solved over a rolling window.
    Returns problems solved per week in the recent window.
    """
    if not submissions:
        return 0.0

    now = datetime.now()
    cutoff = now - timedelta(days=window_days)

    recent_count = 0
    for sub in submissions:
        if isinstance(sub, dict):
            ts = sub.get("timestamp", 0)
            if isinstance(ts, (int, float)):
                sub_date = datetime.fromtimestamp(ts)
            elif isinstance(ts, str):
                try:
                    sub_date = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    continue
            else:
                continue

            if sub_date >= cutoff:
                recent_count += 1
        elif isinstance(sub, (int, float)):
            # If submissions are just timestamps
            sub_date = datetime.fromtimestamp(sub)
            if sub_date >= cutoff:
                recent_count += 1

    weeks = window_days / 7
    return recent_count / max(weeks, 1)


def compute_skill_keyword_density(resume_text: str, jd_text: str) -> float:
    """
    Raw count of keywords from the JD found in the resume,
    normalized by the length of the resume.
    """
    if not resume_text or not jd_text:
        return 0.0

    resume_lower = resume_text.lower()
    jd_lower = jd_text.lower()

    # Extract meaningful keywords from JD (words with 3+ chars, no stopwords)
    stopwords = {
        'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can',
        'had', 'her', 'was', 'one', 'our', 'out', 'has', 'have', 'been',
        'will', 'with', 'this', 'that', 'from', 'they', 'were', 'your',
        'what', 'when', 'make', 'like', 'long', 'look', 'many', 'some',
        'way', 'could', 'would', 'them', 'than', 'other', 'about', 'into',
        'work', 'must', 'should', 'also', 'able', 'such', 'more',
        'experience', 'strong', 'required', 'preferred', 'role', 'team',
        'including', 'working', 'years', 'knowledge', 'skills', 'ability'
    }

    jd_words = set(re.findall(r'\b[a-z]{3,}\b', jd_lower))
    jd_keywords = jd_words - stopwords

    if not jd_keywords:
        return 0.0

    resume_words = set(re.findall(r'\b[a-z]{3,}\b', resume_lower))
    matches = jd_keywords & resume_words

    # Normalize by total JD keywords
    return len(matches) / len(jd_keywords)


def compute_api_skill_validation_ratio(resume_skills: list, github_languages: list) -> float:
    """
    Measures overlap between skills listed on resume and languages
    detected in the user's GitHub repositories.
    High ratio = resume claims are backed by practical work.
    """
    if not resume_skills or not github_languages:
        return 0.0

    resume_set = {s.lower().strip() for s in resume_skills}
    github_set = {l.lower().strip() for l in github_languages}

    # Common aliases
    aliases = {
        'js': 'javascript',
        'ts': 'typescript',
        'py': 'python',
        'cpp': 'c++',
        'c#': 'csharp',
        'golang': 'go',
        'node': 'javascript',
        'react': 'javascript',
        'angular': 'typescript',
        'vue': 'javascript',
        'django': 'python',
        'flask': 'python',
        'spring': 'java',
        'pytorch': 'python',
        'tensorflow': 'python',
    }

    # Expand resume skills with aliases
    expanded_resume = set()
    for skill in resume_set:
        expanded_resume.add(skill)
        if skill in aliases:
            expanded_resume.add(aliases[skill])

    # Expand github languages with aliases
    expanded_github = set()
    for lang in github_set:
        expanded_github.add(lang)
        if lang in aliases:
            expanded_github.add(aliases[lang])

    overlap = expanded_resume & expanded_github

    if not expanded_resume:
        return 0.0

    return len(overlap) / len(expanded_resume)


def compute_project_skill_overlap(resume_projects_text: str, jd_text: str) -> float:
    """
    TF-IDF-based cosine similarity between the student's resume/projects
    and the job description.
    """
    if not resume_projects_text or not jd_text:
        return 0.0

    try:
        vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=500,
            ngram_range=(1, 2)
        )
        tfidf_matrix = vectorizer.fit_transform([resume_projects_text, jd_text])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        return float(similarity[0][0])
    except Exception:
        return 0.0


def extract_skills_from_text(text: str) -> list:
    """
    Extracts technical skills/keywords from resume or JD text.
    """
    tech_skills = [
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust',
        'ruby', 'php', 'swift', 'kotlin', 'scala', 'r', 'matlab',
        'html', 'css', 'react', 'angular', 'vue', 'node', 'express', 'django',
        'flask', 'spring', 'rails', 'laravel', 'nextjs', 'next.js',
        'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
        'git', 'github', 'gitlab', 'ci/cd', 'jenkins', 'travis',
        'machine learning', 'deep learning', 'nlp', 'computer vision',
        'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy',
        'data structures', 'algorithms', 'system design', 'api design',
        'rest', 'graphql', 'microservices', 'agile', 'scrum',
        'linux', 'bash', 'powershell', 'networking',
        'selenium', 'jest', 'junit', 'pytest',
        'figma', 'sketch', 'adobe xd',
        'blockchain', 'solidity', 'web3',
        'hadoop', 'spark', 'kafka', 'airflow',
        'tableau', 'power bi', 'excel',
    ]

    text_lower = text.lower()
    found = [skill for skill in tech_skills if skill in text_lower]
    return found


def _has_signal(data: dict, keys: list) -> int:
    """Return 1 if any of the named numeric/list keys carry a non-zero signal."""
    for key in keys:
        value = data.get(key)
        if isinstance(value, (int, float)) and value > 0:
            return 1
        if isinstance(value, (list, str)) and len(value) > 0:
            return 1
    return 0


def build_feature_vector(
    resume_text: str,
    jd_text: str,
    github_data: dict,
    leetcode_data: dict,
    codeforces_data: dict,
    fetch_status: dict | None = None,
) -> dict:
    """
    Builds the complete feature vector for a student-job pair.

    `fetch_status` is an optional dict {github, leetcode, codeforces -> str}
    used to populate explicit missingness flags so the model can distinguish
    "user has zero commits" from "we could not reach GitHub".
    """
    features = {}
    fetch_status = fetch_status or {}

    # --- Raw Numerical Features ---
    features['github_total_commits'] = github_data.get('total_commits', 0)
    features['github_total_prs'] = github_data.get('total_pull_requests', 0)
    features['github_total_repos'] = github_data.get('total_repos', 0)
    features['github_total_languages'] = github_data.get('total_languages', 0)

    features['leetcode_solved'] = leetcode_data.get('solved', 0)
    features['leetcode_easy'] = leetcode_data.get('easy', 0)
    features['leetcode_medium'] = leetcode_data.get('medium', 0)
    features['leetcode_hard'] = leetcode_data.get('hard', 0)
    features['leetcode_ranking'] = leetcode_data.get('ranking', 0)

    features['codeforces_rating'] = float(codeforces_data.get('rating', 0))
    features['codeforces_max_rating'] = float(codeforces_data.get('max_rating', 0))
    features['codeforces_contests'] = codeforces_data.get('contests', 0)
    features['codeforces_avg_problem_rating'] = float(
        codeforces_data.get('avg_problem_rating', 0) or 0
    )

    # --- Engineered Features ---
    commit_timestamps = github_data.get('commit_timestamps', [])
    features['commit_consistency_score'] = compute_commit_consistency_score(commit_timestamps)

    submissions = leetcode_data.get('recent_submissions', [])
    features['problem_solving_velocity'] = compute_problem_solving_velocity(submissions)

    features['skill_keyword_density'] = compute_skill_keyword_density(resume_text, jd_text)

    resume_skills = extract_skills_from_text(resume_text)
    github_languages = github_data.get('languages', [])
    features['api_skill_validation_ratio'] = compute_api_skill_validation_ratio(
        resume_skills, github_languages
    )

    features['project_skill_overlap'] = compute_project_skill_overlap(resume_text, jd_text)

    # --- Difficulty ratio features ---
    total_solved = features['leetcode_solved']
    if total_solved > 0:
        features['leetcode_hard_ratio'] = features['leetcode_hard'] / total_solved
        features['leetcode_medium_ratio'] = features['leetcode_medium'] / total_solved
    else:
        features['leetcode_hard_ratio'] = 0.0
        features['leetcode_medium_ratio'] = 0.0

    # --- Resume length as a feature ---
    features['resume_word_count'] = len(resume_text.split()) if resume_text else 0

    # --- Skills count ---
    features['resume_skills_count'] = len(resume_skills)
    jd_skills = extract_skills_from_text(jd_text)
    features['jd_skills_count'] = len(jd_skills)

    # --- Missingness flags ---
    # has_*: user actually carries some signal on this platform.
    features['has_github_profile'] = _has_signal(
        github_data,
        ['total_commits', 'total_repos', 'total_pull_requests', 'languages'],
    )
    features['has_leetcode_profile'] = _has_signal(
        leetcode_data, ['solved', 'easy', 'medium', 'hard', 'ranking']
    )
    features['has_codeforces_profile'] = _has_signal(
        codeforces_data, ['rating', 'contests', 'recent_submissions']
    )

    # *_fetch_failed: distinguish "no signal" from "we couldn't reach the API".
    failure_states = {"timeout", "rate_limited", "unauthorized", "error"}
    features['github_fetch_failed'] = (
        1 if fetch_status.get('github') in failure_states else 0
    )
    features['leetcode_fetch_failed'] = (
        1 if fetch_status.get('leetcode') in failure_states else 0
    )
    features['codeforces_fetch_failed'] = (
        1 if fetch_status.get('codeforces') in failure_states else 0
    )

    return features
