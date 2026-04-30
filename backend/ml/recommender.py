"""
Skill-Gap Recommendation Engine for AI-Powered Student Profile Tracker.

Translates SHAP-based skill gap analysis into personalized learning
path recommendations by mapping negative SHAP features to existing
roadmap content.
"""

import os
import json

# Map SHAP feature labels to roadmap topics and learning resources
SKILL_GAP_MAP = {
    # GitHub-related gaps
    'GitHub Commits': {
        'topic': 'git-github',
        'skill': 'Git & GitHub',
        'advice': 'Increase your commit frequency. Try to commit code daily, even small changes.',
        'action': 'Start contributing to open-source projects or build personal projects with regular commits.',
    },
    'GitHub Pull Requests': {
        'topic': 'git-github',
        'skill': 'Open Source Contribution',
        'advice': 'Create pull requests on open-source projects to demonstrate collaborative development.',
        'action': 'Find beginner-friendly issues on GitHub and submit PRs.',
    },
    'GitHub Repositories': {
        'topic': 'full-stack',
        'skill': 'Project Portfolio',
        'advice': 'Build more projects and publish them on GitHub to strengthen your portfolio.',
        'action': 'Create 2-3 new projects showcasing different technologies.',
    },
    'Programming Languages (GitHub)': {
        'topic': 'python',
        'skill': 'Language Diversity',
        'advice': 'Learn additional programming languages to broaden your skill set.',
        'action': 'Pick a new language and build a project with it.',
    },
    'Commit Consistency': {
        'topic': 'git-github',
        'skill': 'Coding Consistency',
        'advice': 'Your commit pattern is irregular. Consistent daily coding shows dedication.',
        'action': 'Set a goal to code and commit at least 5 days a week.',
    },

    # LeetCode-related gaps
    'LeetCode Problems Solved': {
        'topic': 'python',
        'skill': 'Problem Solving',
        'advice': 'Solve more coding problems to improve your algorithmic thinking.',
        'action': 'Aim to solve 2-3 problems daily on LeetCode.',
    },
    'LeetCode Easy Problems': {
        'topic': 'python',
        'skill': 'Fundamentals',
        'advice': 'Strengthen your fundamentals by completing more easy-level problems.',
        'action': 'Complete all easy problems in core categories: arrays, strings, and linked lists.',
    },
    'LeetCode Medium Problems': {
        'topic': 'system-design',
        'skill': 'Intermediate Algorithms',
        'advice': 'Push yourself to solve medium-difficulty problems for interview readiness.',
        'action': 'Focus on dynamic programming, trees, and graph problems.',
    },
    'LeetCode Hard Problems': {
        'topic': 'system-design',
        'skill': 'Advanced Algorithms',
        'advice': 'Tackle hard problems to demonstrate elite problem-solving skills.',
        'action': 'Attempt 1-2 hard problems per week in areas like advanced DP and graph algorithms.',
    },
    'Hard Problem Ratio': {
        'topic': 'system-design',
        'skill': 'Problem Difficulty Mix',
        'advice': 'Your ratio of hard problems is low. Challenge yourself with harder problems.',
        'action': 'Shift your practice balance to include more medium and hard problems.',
    },
    'Medium Problem Ratio': {
        'topic': 'system-design',
        'skill': 'Problem Difficulty Balance',
        'advice': 'Increase the proportion of medium problems you solve.',
        'action': 'Target the most commonly asked medium-level interview questions.',
    },
    'Problem-Solving Velocity': {
        'topic': 'python',
        'skill': 'Active Practice',
        'advice': 'Your recent problem-solving activity is low. Stay active and consistent.',
        'action': 'Set up a daily routine: solve at least one problem daily for the next 30 days.',
    },

    # Codeforces-related gaps
    'Codeforces Rating': {
        'topic': 'python',
        'skill': 'Competitive Programming',
        'advice': 'Participate in more competitive programming contests to boost your rating.',
        'action': 'Join Codeforces contests regularly and upsolve problems after each contest.',
    },
    'Codeforces Max Rating': {
        'topic': 'python',
        'skill': 'Competitive Performance',
        'advice': 'Your peak competitive rating is low compared to expectations.',
        'action': 'Focus on speed and accuracy during timed practice sessions.',
    },
    'Codeforces Contests': {
        'topic': 'python',
        'skill': 'Contest Participation',
        'advice': 'Participate in more programming contests to demonstrate competitive ability.',
        'action': 'Commit to participating in at least 2 contests per month.',
    },

    # Resume & Skill Match gaps
    'Skill-Keyword Match': {
        'topic': None,
        'skill': 'Resume Keywords',
        'advice': 'Your resume is missing critical keywords from the job description.',
        'action': 'Review the job description and incorporate relevant technical keywords into your resume.',
    },
    'Skill Validation (Resume vs GitHub)': {
        'topic': None,
        'skill': 'Skill Verification',
        'advice': 'Skills listed on your resume are not verified by your GitHub activity.',
        'action': 'Build projects using the skills you claim on your resume and push them to GitHub.',
    },
    'Project-Job Description Overlap': {
        'topic': 'full-stack',
        'skill': 'Relevant Projects',
        'advice': 'Your project experience doesn\'t align well with this job description.',
        'action': 'Build a project that directly addresses the key responsibilities in the job listing.',
    },
    'Resume Length': {
        'topic': None,
        'skill': 'Resume Quality',
        'advice': 'Your resume may be too short or too long. Aim for 1-2 pages.',
        'action': 'Review your resume for completeness. Include projects, experience, and quantifiable achievements.',
    },
    'Resume Skills Count': {
        'topic': None,
        'skill': 'Technical Breadth',
        'advice': 'You have fewer technical skills listed than expected.',
        'action': 'Learn and add more relevant technical skills to your profile.',
    },
}

# Additional topic mappings for keyword-based gap detection
KEYWORD_TOPIC_MAP = {
    'python': 'python',
    'java': 'java',
    'javascript': 'javascript',
    'typescript': 'typescript',
    'react': 'react',
    'angular': 'angular',
    'vue': 'vue',
    'node': 'nodejs',
    'nodejs': 'nodejs',
    'sql': 'sql',
    'postgresql': 'postgresql-dba',
    'php': 'php',
    'git': 'git-github',
    'github': 'git-github',
    'frontend': 'frontend',
    'backend': 'backend',
    'devops': 'devops',
    'docker': 'devops',
    'kubernetes': 'devops',
    'api': 'api-design',
    'system design': 'system-design',
    'data': 'data-analyst',
    'machine learning': 'ai-data-scientist',
    'ai': 'ai-engineer',
    'deep learning': 'ai-data-scientist',
    'android': 'android',
    'ios': 'ios',
    'cyber security': 'cyber-security',
    'blockchain': 'blockchain',
    'qa': 'qa',
    'testing': 'qa',
    'ux': 'ux-design',
    'game': 'game-developer',
}


def _format_keyword_list(keywords: list, *, limit: int = 3) -> str:
    cleaned = [k.strip() for k in keywords if isinstance(k, str) and k.strip()]
    if not cleaned:
        return ""
    snippet = cleaned[:limit]
    if len(cleaned) > limit:
        return ", ".join(snippet) + f", and {len(cleaned) - limit} more"
    if len(snippet) == 1:
        return snippet[0]
    return ", ".join(snippet[:-1]) + f", and {snippet[-1]}"


def identify_skill_gaps(shap_explanation: dict, missing_keywords: list | None = None) -> list:
    """Identify skill gaps from SHAP explanation.

    When the negative-impact feature is `Skill-Keyword Match` and we know
    which keywords are actually missing, we cite them by name in the advice
    so the user sees a concrete reason instead of boilerplate.
    """
    gaps = []
    missing_keywords = missing_keywords or []
    top_negative = shap_explanation.get('top_negative', [])

    for label, shap_value in top_negative:
        gap_info = SKILL_GAP_MAP.get(label)
        if not gap_info:
            continue

        advice = gap_info['advice']
        action = gap_info['action']

        if label == 'Skill-Keyword Match' and missing_keywords:
            joined = _format_keyword_list(missing_keywords, limit=3)
            advice = (
                f"Your resume is missing keywords required by this job: {joined}."
            )
            action = (
                f"Update your resume to demonstrate {joined} — add a project, "
                f"certification, or bullet point that uses each one."
            )
        elif label == 'Skill Validation (Resume vs GitHub)' and missing_keywords:
            joined = _format_keyword_list(missing_keywords, limit=2)
            action = (
                f"Build a public GitHub project that uses {joined} so the "
                f"resume claims are backed by code recruiters can read."
            )

        gaps.append({
            'skill': gap_info['skill'],
            'advice': advice,
            'action': action,
            'topic': gap_info['topic'],
            'shap_impact': abs(shap_value),
            'feature_label': label,
        })

    gaps.sort(key=lambda g: g['shap_impact'], reverse=True)
    return gaps


def _available_roadmap_slugs(roadmap_dir: str | None = None) -> set:
    if roadmap_dir is None:
        roadmap_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'roadmap-content'
        )
    if not os.path.exists(roadmap_dir):
        return set()
    return {
        f[:-5] for f in os.listdir(roadmap_dir)
        if f.endswith('.json')
    }


def identify_keyword_gaps(missing_keywords: list, roadmap_dir: str | None = None) -> list:
    """Map missing JD keywords to learning roadmap topics.

    A keyword is only emitted as a separate gap if it maps to a roadmap that
    actually exists on disk — otherwise we'd be promising the user a link
    that 404s. If no roadmap exists we still emit the gap so the user knows
    the keyword is required, but with a generic next step.
    """
    gaps = []
    available = _available_roadmap_slugs(roadmap_dir)

    for keyword in missing_keywords:
        kw_lower = keyword.lower().strip()
        topic = KEYWORD_TOPIC_MAP.get(kw_lower)
        roadmap_exists = bool(topic and topic in available)

        if topic and roadmap_exists:
            advice = (
                f'"{keyword}" is required by this job but missing from your '
                f'resume.'
            )
            action = (
                f'Open the {topic.replace("-", " ")} roadmap below and start '
                f'with the {keyword} fundamentals; then add a small project '
                f'using {keyword} to your GitHub.'
            )
        else:
            advice = (
                f'"{keyword}" appears in the job description but not on your '
                f'resume. We do not have a curated roadmap for it yet.'
            )
            action = (
                f'Search the official documentation or MDN for {keyword}, '
                f'then ship one project that uses it.'
            )

        gaps.append({
            'skill': keyword,
            'topic': topic if roadmap_exists else None,
            'advice': advice,
            'action': action,
            'shap_impact': 0,
            'feature_label': f'Missing: {keyword}',
        })

    return gaps


def map_gaps_to_roadmaps(gaps: list, roadmap_dir: str | None = None) -> list:
    """Enrich gap information with links to existing learning roadmaps."""
    available_roadmaps = _available_roadmap_slugs(roadmap_dir)

    for gap in gaps:
        topic = gap.get('topic')
        if topic and topic in available_roadmaps:
            gap['roadmap_available'] = True
            gap['roadmap_url'] = f'/learn/{topic}'
        else:
            gap['roadmap_available'] = False
            gap['roadmap_url'] = None

    return gaps


def generate_recommendations(shap_explanation: dict, missing_keywords: list = None) -> dict:
    """
    Generate complete personalized recommendations.

    Args:
        shap_explanation: dict from pipeline.explain()
        missing_keywords: optional list of keywords missing from resume

    Returns:
        dict with score, gaps (prioritized), and summary text
    """
    score = shap_explanation.get('score', 0)
    missing_keywords = missing_keywords or []

    # SHAP-based gaps, with keyword-aware advice for the keyword-match feature.
    gaps = identify_skill_gaps(shap_explanation, missing_keywords=missing_keywords)

    # Per-keyword gaps mapped to existing roadmaps when possible.
    if missing_keywords:
        keyword_gaps = identify_keyword_gaps(missing_keywords)
        gaps.extend(keyword_gaps)

    # Annotate each gap with a roadmap URL where one exists.
    gaps = map_gaps_to_roadmaps(gaps)

    # Stable ordering: SHAP impact first; gaps that have a roadmap break ties
    # so users see actionable items before generic ones.
    gaps.sort(
        key=lambda g: (
            -float(g.get('shap_impact', 0) or 0),
            0 if g.get('roadmap_available') else 1,
        )
    )

    # Generate summary
    if score >= 80:
        summary = "Excellent match! Your profile strongly aligns with this job description."
        priority = "low"
    elif score >= 60:
        summary = "Good match, but there are areas for improvement."
        priority = "medium"
    elif score >= 40:
        summary = "Moderate match. Focus on the skill gaps below to significantly improve your score."
        priority = "high"
    else:
        summary = "Low match. Significant skill development is needed for this role."
        priority = "critical"

    return {
        'score': score,
        'summary': summary,
        'priority': priority,
        'gaps': gaps[:8],  # Top 8 most impactful gaps
        'total_gaps': len(gaps),
    }
