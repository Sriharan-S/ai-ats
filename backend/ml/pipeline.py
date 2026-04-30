"""
ML Pipeline for AI-Powered Student Profile Tracker.

The score is a continuous regression target in [0, 100] — interpreted as
"how well this resume + profile evidence matches the job description". This
is closer to what users expect of an ATS score than the previous calibrated
P(Match) formulation, and it produces sensible values even when the user
provides a resume + JD only (no GitHub / LeetCode / Codeforces handles).

Stack:
  - XGBRegressor + RandomForestRegressor combined via VotingRegressor.
  - SHAP TreeExplainer attached to the XGBoost regressor (faithful — both
    the regressor and the SHAP estimator see the same raw feature matrix,
    no scaling).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import joblib
import numpy as np
import shap
from sklearn.ensemble import RandomForestRegressor, VotingRegressor
from sklearn.model_selection import KFold, cross_val_score
from xgboost import XGBRegressor

# Feature names used by the model (must match feature_engineering.build_feature_vector keys)
FEATURE_NAMES = [
    'github_total_commits',
    'github_total_prs',
    'github_total_repos',
    'github_total_languages',
    'leetcode_solved',
    'leetcode_easy',
    'leetcode_medium',
    'leetcode_hard',
    'leetcode_ranking',
    'codeforces_rating',
    'codeforces_max_rating',
    'codeforces_contests',
    'codeforces_avg_problem_rating',
    'commit_consistency_score',
    'problem_solving_velocity',
    'skill_keyword_density',
    'api_skill_validation_ratio',
    'project_skill_overlap',
    'leetcode_hard_ratio',
    'leetcode_medium_ratio',
    'resume_word_count',
    'resume_skills_count',
    'jd_skills_count',
    'has_github_profile',
    'has_leetcode_profile',
    'has_codeforces_profile',
    'github_fetch_failed',
    'leetcode_fetch_failed',
    'codeforces_fetch_failed',
]

FEATURE_LABELS = {
    'github_total_commits': 'GitHub Commits',
    'github_total_prs': 'GitHub Pull Requests',
    'github_total_repos': 'GitHub Repositories',
    'github_total_languages': 'Programming Languages (GitHub)',
    'leetcode_solved': 'LeetCode Problems Solved',
    'leetcode_easy': 'LeetCode Easy Problems',
    'leetcode_medium': 'LeetCode Medium Problems',
    'leetcode_hard': 'LeetCode Hard Problems',
    'leetcode_ranking': 'LeetCode Ranking',
    'codeforces_rating': 'Codeforces Rating',
    'codeforces_max_rating': 'Codeforces Max Rating',
    'codeforces_contests': 'Codeforces Contests',
    'codeforces_avg_problem_rating': 'Codeforces Avg Problem Rating',
    'commit_consistency_score': 'Commit Consistency',
    'problem_solving_velocity': 'Problem-Solving Velocity',
    'skill_keyword_density': 'Skill-Keyword Match',
    'api_skill_validation_ratio': 'Skill Validation (Resume vs GitHub)',
    'project_skill_overlap': 'Project-Job Description Overlap',
    'leetcode_hard_ratio': 'Hard Problem Ratio',
    'leetcode_medium_ratio': 'Medium Problem Ratio',
    'resume_word_count': 'Resume Length',
    'resume_skills_count': 'Resume Skills Count',
    'jd_skills_count': 'Job Description Skills Count',
    'has_github_profile': 'GitHub Profile Present',
    'has_leetcode_profile': 'LeetCode Profile Present',
    'has_codeforces_profile': 'Codeforces Profile Present',
    'github_fetch_failed': 'GitHub Fetch Failed',
    'leetcode_fetch_failed': 'LeetCode Fetch Failed',
    'codeforces_fetch_failed': 'Codeforces Fetch Failed',
}

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model.joblib')
META_PATH = os.path.join(os.path.dirname(__file__), 'model_meta.json')


def _xgb_regressor() -> XGBRegressor:
    return XGBRegressor(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        objective='reg:squarederror',
    )


def _rf_regressor() -> RandomForestRegressor:
    return RandomForestRegressor(
        n_estimators=200,
        max_depth=10,
        min_samples_split=4,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )


class ATSPipeline:
    """End-to-end ATS regression pipeline.

    `predict_score(features)` returns the model's predicted match score in
    [0, 100]. `explain(features)` adds a SHAP breakdown drawn from the
    underlying XGBoost regressor.
    """

    def __init__(self):
        self.model: VotingRegressor | None = None
        self.shap_model: XGBRegressor | None = None
        self.explainer = None
        self._build_model()

    def _build_model(self):
        xgb = _xgb_regressor()
        rf = _rf_regressor()
        self.model = VotingRegressor(estimators=[('xgb', xgb), ('rf', rf)])

    def train(self, X: np.ndarray, y: np.ndarray):
        self.model.fit(X, y)

        # Standalone XGB on the same data, used for SHAP. Same hyperparams as
        # the one inside the voting regressor — SHAP additivity holds for
        # this estimator.
        self.shap_model = _xgb_regressor()
        self.shap_model.fit(X, y)
        self.explainer = shap.TreeExplainer(self.shap_model)

    def predict_score(self, features_dict: dict) -> float:
        X = self._dict_to_array(features_dict)
        prediction = float(self.model.predict(X)[0])
        return float(np.clip(prediction, 0.0, 100.0))

    def explain(self, features_dict: dict) -> dict:
        X = self._dict_to_array(features_dict)
        score = self.predict_score(features_dict)

        shap_values = self.explainer.shap_values(X)
        sv = np.asarray(shap_values).flatten()

        shap_dict = {}
        for i, fname in enumerate(FEATURE_NAMES):
            label = FEATURE_LABELS.get(fname, fname)
            shap_dict[label] = float(sv[i])

        sorted_features = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)
        top_positive = [(k, v) for k, v in sorted_features if v > 0][:6]
        top_negative = [(k, v) for k, v in sorted_features if v < 0][:6]

        base_value = self.explainer.expected_value
        if isinstance(base_value, np.ndarray):
            base_value = float(base_value.flatten()[0])
        else:
            base_value = float(base_value)

        return {
            'score': round(score, 1),
            'shap_values': shap_dict,
            'top_positive': top_positive,
            'top_negative': top_negative,
            'base_value': base_value,
            'feature_values': {FEATURE_LABELS.get(k, k): v for k, v in features_dict.items()},
        }

    def _dict_to_array(self, features_dict: dict) -> np.ndarray:
        values = [features_dict.get(name, 0) for name in FEATURE_NAMES]
        return np.array([values], dtype=np.float64)

    def save(self, model_path: str | None = None):
        joblib.dump(
            {
                'voting_model': self.model,
                'shap_model': self.shap_model,
                'feature_names': FEATURE_NAMES,
                'task': 'regression',
            },
            model_path or MODEL_PATH,
        )

    def load(self, model_path: str | None = None):
        bundle = joblib.load(model_path or MODEL_PATH)
        if not isinstance(bundle, dict):
            raise RuntimeError(
                "Loaded model is in legacy format. Retrain with "
                "`python -m ml.train_model`."
            )

        # New regression bundle
        if 'voting_model' in bundle:
            self.model = bundle['voting_model']
            self.shap_model = bundle.get('shap_model')
        # Legacy classification bundle — fail loud.
        elif 'calibrated_model' in bundle:
            raise RuntimeError(
                "Loaded model bundle was trained with the legacy classifier. "
                "Retrain with `python -m ml.train_model` to upgrade to the "
                "regression scorer."
            )
        else:
            raise RuntimeError("Unknown model bundle layout.")

        if self.shap_model is None:
            raise RuntimeError(
                "Loaded model bundle is missing the SHAP estimator. "
                "Retrain with `python -m ml.train_model`."
            )
        self.explainer = shap.TreeExplainer(self.shap_model)


def load_pipeline() -> ATSPipeline:
    pipeline = ATSPipeline()
    pipeline.load()
    return pipeline


def evaluate_pipeline(X: np.ndarray, y: np.ndarray) -> dict:
    """5-fold CV regression metrics."""
    model = VotingRegressor(estimators=[('xgb', _xgb_regressor()), ('rf', _rf_regressor())])
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    r2 = cross_val_score(model, X, y, cv=kf, scoring='r2')
    mae = cross_val_score(model, X, y, cv=kf, scoring='neg_mean_absolute_error')
    rmse = cross_val_score(model, X, y, cv=kf, scoring='neg_root_mean_squared_error')

    return {
        'r2': float(np.mean(r2)),
        'mae': float(-np.mean(mae)),
        'rmse': float(-np.mean(rmse)),
    }


def write_meta(
    *,
    model_version: str,
    feature_version: str,
    dataset_version: str,
    sample_size: int,
    target_summary: dict,
    metrics: dict,
    meta_path: str | None = None,
) -> None:
    meta = {
        'model_version': model_version,
        'feature_version': feature_version,
        'dataset_version': dataset_version,
        'task': 'regression',
        'feature_count': len(FEATURE_NAMES),
        'feature_names': FEATURE_NAMES,
        'sample_size': sample_size,
        'target_summary': target_summary,
        'cv_metrics': metrics,
        'trained_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    }
    with open(meta_path or META_PATH, 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2)


def read_meta(meta_path: str | None = None) -> dict:
    path = meta_path or META_PATH
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
