"""Smoke test for the /api/ats-analyze response contract."""
import io
import os

import pytest

import main as app_module
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
    monkeypatch.setattr(app_module, "ats_pipeline", _StubPipeline())
    monkeypatch.setattr(
        app_module,
        "model_meta",
        {
            "model_version": "ats-test-1",
            "feature_version": "features-test-1",
            "dataset_version": "test-bootstrap",
            "feature_count": len(FEATURE_NAMES),
            "trained_at": "2026-04-29T00:00:00+00:00",
        },
    )
    # Avoid hitting real APIs during the test.
    monkeypatch.setattr(app_module, "get_github_data", lambda u: {"fetch_status": "success", "total_commits": 5, "total_repos": 2, "languages": ["Python"], "commit_timestamps": []})
    monkeypatch.setattr(app_module, "get_leetcode_data", lambda u: {"fetch_status": "success", "solved": 10, "ranking": 100, "recent_submissions": []})
    monkeypatch.setattr(app_module, "get_codeforces_data", lambda u: {"fetch_status": "success", "rating": 1200, "avg_problem_rating": 1100, "recent_submissions": []})

    app_module.app.config.update({"TESTING": True})
    return app_module.app.test_client()


def test_health_includes_model_metadata(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True
    assert body["model_version"] == "ats-test-1"
    assert body["feature_version"] == "features-test-1"
    assert body["feature_count"] == len(FEATURE_NAMES)


def test_ats_analyze_returns_versioned_payload(client, monkeypatch):
    # Force resume parsing to return a known string instead of touching the
    # filesystem extractor.
    monkeypatch.setattr(app_module, "extract_resume_text", lambda path: "I have python and docker experience")

    fake_resume = io.BytesIO(b"PDF stub")
    data = {
        "job_description": "Looking for python aws docker engineer",
        "github_username": "octocat",
    }
    data["resume"] = (fake_resume, "resume.pdf")

    resp = client.post("/api/ats-analyze", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200, resp.get_data(as_text=True)
    body = resp.get_json()

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
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400
    body = resp.get_json()
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
