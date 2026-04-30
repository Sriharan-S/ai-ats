"""Pipeline shape and faithfulness checks.

These tests train a tiny model on synthetic features so we don't depend on
the saved model.joblib being present.
"""
import numpy as np
import pytest

from ml.pipeline import ATSPipeline, FEATURE_LABELS, FEATURE_NAMES
from ml.train_model import generate_bootstrap_data


@pytest.fixture(scope="module")
def trained_pipeline():
    df, targets = generate_bootstrap_data(n_samples=300, random_state=0)
    X = df[FEATURE_NAMES].values
    pipe = ATSPipeline()
    pipe.train(X, targets)
    return pipe, X


def test_score_in_zero_one_hundred_range(trained_pipeline):
    pipe, _ = trained_pipeline
    features = {name: 0 for name in FEATURE_NAMES}
    score = pipe.predict_score(features)
    assert 0.0 <= score <= 100.0


def test_explanation_includes_every_label(trained_pipeline):
    pipe, _ = trained_pipeline
    features = {name: 1 for name in FEATURE_NAMES}
    explanation = pipe.explain(features)
    expected_labels = set(FEATURE_LABELS.values())
    actual_labels = set(explanation["shap_values"].keys())
    assert expected_labels == actual_labels


def test_shap_values_sum_close_to_xgb_prediction(trained_pipeline):
    """SHAP additivity: for the underlying XGB regressor, base_value plus
    the sum of SHAP values must equal the model's raw prediction on the
    same feature vector. We test this against the SHAP estimator (not the
    averaged voting prediction returned by predict_score).
    """
    pipe, X = trained_pipeline
    sample = X[0:1]
    raw_pred = pipe.shap_model.predict(sample)[0]

    sv = np.asarray(pipe.explainer.shap_values(sample)).flatten()
    base = pipe.explainer.expected_value
    if isinstance(base, np.ndarray):
        base = float(base.flatten()[0])
    else:
        base = float(base)

    reconstructed = base + sv.sum()
    assert abs(reconstructed - raw_pred) < 0.5  # half-a-point tolerance


def test_resume_only_strong_match_scores_well(trained_pipeline):
    """A clean resume + JD with strong keyword match should score in the
    "Good Match" band even with no public coding profiles."""
    pipe, _ = trained_pipeline
    features = {name: 0 for name in FEATURE_NAMES}
    features.update({
        "skill_keyword_density": 0.80,
        "project_skill_overlap": 0.45,
        "resume_word_count": 450,
        "resume_skills_count": 12,
        "jd_skills_count": 14,
    })
    score = pipe.predict_score(features)
    assert score >= 60.0, f"Resume-only strong match should >= 60, got {score:.1f}"


def test_resume_only_moderate_scores_above_floor(trained_pipeline):
    pipe, _ = trained_pipeline
    features = {name: 0 for name in FEATURE_NAMES}
    features.update({
        "skill_keyword_density": 0.50,
        "project_skill_overlap": 0.25,
        "resume_word_count": 350,
        "resume_skills_count": 8,
        "jd_skills_count": 10,
    })
    score = pipe.predict_score(features)
    # No platforms attached, but a real keyword match — must not collapse to
    # the previous calibrated-classifier behavior of 10–25%.
    assert score >= 45.0, f"Resume-only moderate should >= 45, got {score:.1f}"
