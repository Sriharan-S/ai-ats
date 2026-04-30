import os

from ml.recommender import (
    generate_recommendations,
    identify_keyword_gaps,
    identify_skill_gaps,
)


def test_skill_keyword_match_advice_cites_actual_missing_keywords():
    explanation = {
        "score": 55,
        "top_negative": [("Skill-Keyword Match", -0.18)],
    }
    gaps = identify_skill_gaps(explanation, missing_keywords=["docker", "sql", "aws"])
    assert len(gaps) == 1
    advice = gaps[0]["advice"]
    assert "docker" in advice
    assert "sql" in advice
    assert "aws" in advice


def test_keyword_gaps_only_link_to_existing_roadmaps(tmp_path):
    roadmap_dir = tmp_path / "rm"
    roadmap_dir.mkdir()
    # Only make the python roadmap exist
    (roadmap_dir / "python.json").write_text("{}", encoding="utf-8")

    gaps = identify_keyword_gaps(["python", "react"], roadmap_dir=str(roadmap_dir))
    by_skill = {g["skill"]: g for g in gaps}

    assert by_skill["python"]["topic"] == "python"
    # react has a mapping in KEYWORD_TOPIC_MAP but no roadmap file in this dir
    assert by_skill["react"]["topic"] is None


def test_generate_recommendations_orders_by_impact_then_roadmap():
    explanation = {
        "score": 50,
        "top_negative": [
            ("Skill-Keyword Match", -0.10),
            ("Resume Length", -0.20),  # higher impact, but no roadmap
        ],
    }
    rec = generate_recommendations(explanation, missing_keywords=["docker"])
    assert rec["priority"] in {"low", "medium", "high", "critical"}
    # The highest absolute impact gap leads.
    assert rec["gaps"][0]["feature_label"] == "Resume Length"


def test_real_roadmap_dir_is_respected():
    """Sanity check against the actual roadmap-content directory shipped with the repo."""
    rec_path = os.path.join(os.path.dirname(__file__), os.pardir, "roadmap-content")
    if not os.path.isdir(rec_path):
        return  # skip silently if running outside the repo layout

    gaps = identify_keyword_gaps(["frontend", "definitely-not-a-real-topic"])
    by_skill = {g["skill"]: g for g in gaps}
    assert by_skill["frontend"]["topic"] == "frontend"
    assert by_skill["definitely-not-a-real-topic"]["topic"] is None
