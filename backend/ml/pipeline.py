"""
ML Pipeline for AI-Powered Student Profile Tracker.

Implements the ensemble learning strategy from the paper:
  - XGBoost (gradient boosting)
  - Random Forest (bagging)
  - VotingClassifier (soft voting)
  - SHAP TreeExplainer for interpretability
"""

import numpy as np
import pandas as pd
import joblib
import os
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold, cross_val_score
from xgboost import XGBClassifier
import shap

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
]

# Human-readable labels for SHAP explanations
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
}

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model.joblib')
SCALER_PATH = os.path.join(os.path.dirname(__file__), 'scaler.joblib')


class ATSPipeline:
    """
    End-to-end ATS ML pipeline:
      1. StandardScaler for numerical features
      2. XGBoost + Random Forest → VotingClassifier (soft voting)
      3. SHAP TreeExplainer for interpretability
    """

    def __init__(self):
        self.scaler = StandardScaler()
        self.model = None
        self.explainer = None
        self._build_model()

    def _build_model(self):
        """Build the ensemble Voting Classifier."""
        xgb = XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            use_label_encoder=False,
            eval_metric='logloss',
        )

        rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        )

        self.model = VotingClassifier(
            estimators=[('xgb', xgb), ('rf', rf)],
            voting='soft',
        )

    def train(self, X: np.ndarray, y: np.ndarray):
        """Train the pipeline on data."""
        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train voting classifier
        self.model.fit(X_scaled, y)

        # Build SHAP explainer on one of the base models (XGBoost)
        xgb_model = self.model.named_estimators_['xgb']
        self.explainer = shap.TreeExplainer(xgb_model)

    def predict_score(self, features_dict: dict) -> float:
        """
        Predict the Job Match Score (probability of class 1 = Match).
        Returns a score between 0 and 100.
        """
        X = self._dict_to_array(features_dict)
        X_scaled = self.scaler.transform(X)
        proba = self.model.predict_proba(X_scaled)
        return float(proba[0][1] * 100)  # Probability of being a "Match"

    def explain(self, features_dict: dict) -> dict:
        """
        Generate SHAP-based explanation for a prediction.
        Returns:
          - score: Job Match Score (0-100)
          - shap_values: dict of feature_label -> shap_value
          - top_positive: list of (label, value) - features pushing score UP
          - top_negative: list of (label, value) - features pushing score DOWN
          - base_value: expected value from SHAP
        """
        X = self._dict_to_array(features_dict)
        X_scaled = self.scaler.transform(X)

        score = self.predict_score(features_dict)

        # Get SHAP values
        xgb_model = self.model.named_estimators_['xgb']

        # Use unscaled data for SHAP on tree models for better interpretability
        shap_values = self.explainer.shap_values(X)

        if isinstance(shap_values, list):
            sv = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        else:
            sv = shap_values

        sv = sv.flatten()

        # Map to readable labels
        shap_dict = {}
        for i, fname in enumerate(FEATURE_NAMES):
            label = FEATURE_LABELS.get(fname, fname)
            shap_dict[label] = float(sv[i])

        # Sort by absolute impact
        sorted_features = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)

        top_positive = [(k, v) for k, v in sorted_features if v > 0][:6]
        top_negative = [(k, v) for k, v in sorted_features if v < 0][:6]

        base_value = float(self.explainer.expected_value)
        if isinstance(self.explainer.expected_value, np.ndarray):
            base_value = float(self.explainer.expected_value[1]) if len(self.explainer.expected_value) > 1 else float(self.explainer.expected_value[0])

        return {
            'score': round(score, 1),
            'shap_values': shap_dict,
            'top_positive': top_positive,
            'top_negative': top_negative,
            'base_value': base_value,
            'feature_values': {FEATURE_LABELS.get(k, k): v for k, v in features_dict.items()},
        }

    def _dict_to_array(self, features_dict: dict) -> np.ndarray:
        """Convert feature dict to numpy array in correct order."""
        values = [features_dict.get(name, 0) for name in FEATURE_NAMES]
        return np.array([values], dtype=np.float64)

    def save(self, model_path=None, scaler_path=None):
        """Save model and scaler to disk."""
        joblib.dump(self.model, model_path or MODEL_PATH)
        joblib.dump(self.scaler, scaler_path or SCALER_PATH)

    def load(self, model_path=None, scaler_path=None):
        """Load model and scaler from disk."""
        self.model = joblib.load(model_path or MODEL_PATH)
        self.scaler = joblib.load(scaler_path or SCALER_PATH)
        # Rebuild SHAP explainer
        xgb_model = self.model.named_estimators_['xgb']
        self.explainer = shap.TreeExplainer(xgb_model)


def load_pipeline() -> ATSPipeline:
    """Load a pre-trained pipeline from disk."""
    pipeline = ATSPipeline()
    pipeline.load()
    return pipeline


def evaluate_pipeline(pipeline: ATSPipeline, X: np.ndarray, y: np.ndarray) -> dict:
    """Evaluate the pipeline using 5-fold stratified cross-validation."""
    X_scaled = pipeline.scaler.transform(X)

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    accuracy = cross_val_score(pipeline.model, X_scaled, y, cv=skf, scoring='accuracy')
    f1 = cross_val_score(pipeline.model, X_scaled, y, cv=skf, scoring='f1_weighted')
    precision = cross_val_score(pipeline.model, X_scaled, y, cv=skf, scoring='precision_weighted')
    recall = cross_val_score(pipeline.model, X_scaled, y, cv=skf, scoring='recall_weighted')

    return {
        'accuracy': float(np.mean(accuracy)),
        'f1_weighted': float(np.mean(f1)),
        'precision': float(np.mean(precision)),
        'recall': float(np.mean(recall)),
    }
