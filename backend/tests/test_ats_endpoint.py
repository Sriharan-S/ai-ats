"""Smoke test for the /api/ats-analyze response contract."""
import io

import pytest
from fastapi.testclient import TestClient

from ml.feature_engineering import build_feature_vector
from ml.pipeline import FEATURE_NAMES


class _StubPipeline:
    """Stand-in for ATSPipeline that returns a deterministic explanation."""

    def explain(self, features: dict) -> dict:
        labels = ["GitHub Commits", "Skill-Keyword Match", "Resume Length"]
        return {
            "score": 70.0,
            "shap_values": {label: 0.0 for label in labels},
            "top_positive": [("GitHub Commits", 0.1)],
            "top_negative": [("Skill-Keyword Match", -0.15), ("Resume Length", -0.08)],
            "base_value": 0.0,
            "feature_values": {},
        }


@pytest.fixture
def client(monkeypatch):
    from app.routers import ats as ats_module
    from app.routers import platforms as platforms_module

    monkeypatch.setattr(
        ats_module,
        "_get_pipeline",
        lambda: (
            _StubPipeline(),
            {
                "model_version": "ats-test-1",
                "feature_version": "features-test-1",
                "dataset_version": "test-bootstrap",
                "feature_count": len(FEATURE_NAMES),
                "trained_at": "2026-04-29T00:00:00+00:00",
            },
        ),
    )

    fake_github = lambda u: {"fetch_status": "success", "total_commits": 5, "total_repos": 2, "languages": ["Python"], "commit_timestamps": []}
    fake_leetcode = lambda u: {"fetch_status": "success", "solved": 10, "ranking": 100, "recent_submissions": []}
    fake_codeforces = lambda u: {"fetch_status": "success", "rating": 1200, "avg_problem_rating": 1100, "recent_submissions": []}

    monkeypatch.setattr(ats_module, "get_github_data", fake_github)
    monkeypatch.setattr(ats_module, "get_leetcode_data", fake_leetcode)
    monkeypatch.setattr(ats_module, "get_codeforces_data", fake_codeforces)
    monkeypatch.setattr(platforms_module, "get_github_data", fake_github)
    monkeypatch.setattr(platforms_module, "get_leetcode_data", fake_leetcode)
    monkeypatch.setattr(platforms_module, "get_codeforces_data", fake_codeforces)

    monkeypatch.setattr(ats_module, "extract_resume_text", lambda data, ext: "I have python and docker experience")

    # Health endpoint reads model presence from MODEL_PATH; stub both helpers.
    from app.routers import health as health_module
    monkeypatch.setattr(health_module, "_read_meta", lambda: {
        "model_version": "ats-test-1",
        "feature_version": "features-test-1",
        "dataset_version": "test-bootstrap",
        "feature_count": len(FEATURE_NAMES),
        "trained_at": "2026-04-29T00:00:00+00:00",
    })
    monkeypatch.setattr(health_module, "_model_present", lambda: True)

    import main as main_module
    return TestClient(main_module.app)


def test_health_includes_model_metadata(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True
    assert body["model_version"] == "ats-test-1"
    assert body["feature_version"] == "features-test-1"
    assert body["feature_count"] == len(FEATURE_NAMES)


def test_ats_analyze_returns_versioned_payload(client):
    fake_resume = io.BytesIO(b"PDF stub")
    data = {
        "job_description": "Looking for python aws docker engineer",
        "github_username": "octocat",
    }

    resp = client.post(
        "/api/ats-analyze",
        data=data,
        files={"resume": ("resume.pdf", fake_resume, "application/pdf")},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["model_version"] == "ats-test-1"
    assert body["feature_version"] == "features-test-1"
    assert "analysis_id" in body
    assert body["platform_status"]["github"] == "success"
    assert body["platform_status"]["leetcode"] == "not_requested"
    assert body["platform_data"]["github"]["fetch_status"] == "success"
    assert isinstance(body["missing_keywords"], list)
    # AWS is in the JD but not the resume — should appear as a missing keyword.
    assert "aws" in body["missing_keywords"]


def test_ats_analyze_structured_error_for_missing_resume(client):
    resp = client.post(
        "/api/ats-analyze",
        data={"job_description": "Looking for python"},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "RESUME_REQUIRED"


def test_build_feature_vector_uses_codeforces_avg_problem_rating():
    features = build_feature_vector(
        resume_text="python",
        jd_text="python",
        github_data={},
        leetcode_data={},
        codeforces_data={"avg_problem_rating": 1500},
        fetch_status={"github": "not_requested", "leetcode": "not_requested", "codeforces": "success"},
    )
    assert features["codeforces_avg_problem_rating"] == 1500.0
