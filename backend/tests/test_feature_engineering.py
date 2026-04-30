from ml.feature_engineering import (
    build_feature_vector,
    compute_api_skill_validation_ratio,
    compute_skill_keyword_density,
    extract_skills_from_text,
)
from ml.pipeline import FEATURE_NAMES


def test_build_feature_vector_covers_every_declared_feature():
    features = build_feature_vector(
        resume_text="Python and Docker experience",
        jd_text="Looking for Python Docker AWS",
        github_data={
            "total_commits": 10,
            "total_pull_requests": 1,
            "total_repos": 2,
            "total_languages": 3,
            "languages": ["Python"],
            "commit_timestamps": [],
        },
        leetcode_data={
            "solved": 5,
            "easy": 3,
            "medium": 1,
            "hard": 1,
            "ranking": 100000,
            "recent_submissions": [],
        },
        codeforces_data={
            "rating": 1200,
            "max_rating": 1300,
            "contests": 4,
            "avg_problem_rating": 1100,
        },
        fetch_status={"github": "success", "leetcode": "success", "codeforces": "success"},
    )

    for name in FEATURE_NAMES:
        assert name in features, f"build_feature_vector missing key {name}"


def test_missingness_flags_when_data_absent():
    features = build_feature_vector(
        resume_text="",
        jd_text="",
        github_data={},
        leetcode_data={},
        codeforces_data={},
        fetch_status={"github": "not_requested", "leetcode": "timeout", "codeforces": "rate_limited"},
    )
    assert features["has_github_profile"] == 0
    assert features["has_leetcode_profile"] == 0
    assert features["has_codeforces_profile"] == 0
    assert features["github_fetch_failed"] == 0   # not_requested != failure
    assert features["leetcode_fetch_failed"] == 1
    assert features["codeforces_fetch_failed"] == 1


def test_skill_keyword_density_finds_overlap():
    density = compute_skill_keyword_density(
        resume_text="I have used python and docker for several projects",
        jd_text="We need python docker kubernetes",
    )
    assert 0 < density <= 1


def test_api_skill_validation_picks_up_aliases():
    ratio = compute_api_skill_validation_ratio(
        resume_skills=["js", "python"],
        github_languages=["JavaScript", "Python"],
    )
    assert ratio > 0


def test_extract_skills_returns_known_skills():
    skills = extract_skills_from_text("Built APIs with python flask and react")
    assert "python" in skills
    assert "flask" in skills
    assert "react" in skills
