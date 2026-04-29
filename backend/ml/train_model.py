"""
Training Script for AI-Powered Student Profile Tracker.

Generates synthetic training data with realistic distributions
and trains the ensemble model (XGBoost + RF VotingClassifier).

Usage:
    python -m ml.train_model
"""

import numpy as np
import pandas as pd
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.pipeline import ATSPipeline, FEATURE_NAMES, evaluate_pipeline


def generate_synthetic_data(n_samples=500, random_state=42):
    """
    Generate synthetic student-job pair data with realistic distributions.

    The label (match/no-match) is determined by a combination of features
    to simulate real-world correlations.
    """
    rng = np.random.RandomState(random_state)

    data = {}

    # --- GitHub Features ---
    data['github_total_commits'] = rng.exponential(120, n_samples).astype(int).clip(0, 2000)
    data['github_total_prs'] = rng.poisson(8, n_samples).clip(0, 100)
    data['github_total_repos'] = rng.poisson(10, n_samples).clip(0, 80)
    data['github_total_languages'] = rng.poisson(4, n_samples).clip(1, 15)

    # --- LeetCode Features ---
    data['leetcode_solved'] = rng.exponential(60, n_samples).astype(int).clip(0, 500)
    total_solved = data['leetcode_solved']
    data['leetcode_easy'] = (total_solved * rng.beta(5, 3, n_samples)).astype(int)
    data['leetcode_medium'] = (total_solved * rng.beta(4, 5, n_samples)).astype(int)
    data['leetcode_hard'] = np.clip(total_solved - data['leetcode_easy'] - data['leetcode_medium'], 0, None).astype(int)
    data['leetcode_ranking'] = rng.exponential(80000, n_samples).astype(int).clip(100, 500000)

    # --- Codeforces Features ---
    data['codeforces_rating'] = rng.normal(1200, 400, n_samples).clip(0, 3000)
    data['codeforces_max_rating'] = data['codeforces_rating'] + rng.exponential(100, n_samples)
    data['codeforces_max_rating'] = data['codeforces_max_rating'].clip(0, 3500)
    data['codeforces_contests'] = rng.poisson(10, n_samples).clip(0, 100)

    # --- Engineered Features ---
    data['commit_consistency_score'] = rng.beta(3, 3, n_samples).clip(0, 1)
    data['problem_solving_velocity'] = rng.exponential(3, n_samples).clip(0, 30)
    data['skill_keyword_density'] = rng.beta(3, 5, n_samples).clip(0, 1)
    data['api_skill_validation_ratio'] = rng.beta(4, 4, n_samples).clip(0, 1)
    data['project_skill_overlap'] = rng.beta(2, 4, n_samples).clip(0, 1)

    # --- Ratio Features ---
    safe_total = np.maximum(total_solved, 1)
    data['leetcode_hard_ratio'] = data['leetcode_hard'] / safe_total
    data['leetcode_medium_ratio'] = data['leetcode_medium'] / safe_total

    # --- Text Features ---
    data['resume_word_count'] = rng.normal(350, 120, n_samples).astype(int).clip(50, 1000)
    data['resume_skills_count'] = rng.poisson(8, n_samples).clip(0, 30)
    data['jd_skills_count'] = rng.poisson(10, n_samples).clip(3, 25)

    df = pd.DataFrame(data)

    # --- Generate Labels ---
    # Simulate realistic match/no-match based on feature correlations
    match_score = (
        0.20 * np.clip(data['commit_consistency_score'], 0, 1)
        + 0.15 * np.clip(data['skill_keyword_density'], 0, 1)
        + 0.15 * np.clip(data['api_skill_validation_ratio'], 0, 1)
        + 0.15 * np.clip(data['project_skill_overlap'], 0, 1)
        + 0.10 * np.clip(data['leetcode_solved'] / 200, 0, 1)
        + 0.08 * np.clip(data['github_total_commits'] / 300, 0, 1)
        + 0.07 * np.clip(data['codeforces_rating'] / 2000, 0, 1)
        + 0.05 * np.clip(data['problem_solving_velocity'] / 10, 0, 1)
        + 0.05 * np.clip(data['leetcode_hard_ratio'], 0, 1)
    )

    # Add noise
    match_score += rng.normal(0, 0.08, n_samples)

    # Threshold for match (0.4 = 40% of the weighted score)
    threshold = 0.40
    labels = (match_score >= threshold).astype(int)

    return df, labels


def main():
    print("=" * 60)
    print("AI-Powered Student Profile Tracker - Model Training")
    print("=" * 60)

    # Generate synthetic data
    print("\n[1/4] Generating synthetic training data (500 samples)...")
    df, labels = generate_synthetic_data(n_samples=500)
    print(f"  → Dataset shape: {df.shape}")
    print(f"  → Class distribution: Match={sum(labels)}, No-Match={len(labels) - sum(labels)}")

    # Build feature matrix
    X = df[FEATURE_NAMES].values
    y = labels

    # Create and train pipeline
    print("\n[2/4] Training ensemble model (XGBoost + Random Forest)...")
    pipeline = ATSPipeline()
    pipeline.train(X, y)
    print("  → Model trained successfully!")

    # Evaluate
    print("\n[3/4] Evaluating with 5-fold stratified cross-validation...")
    # Need to refit after CV for final model
    metrics = evaluate_pipeline(pipeline, X, y)
    print(f"  → Accuracy:  {metrics['accuracy']:.3f}")
    print(f"  → F1 Score:  {metrics['f1_weighted']:.3f}")
    print(f"  → Precision: {metrics['precision']:.3f}")
    print(f"  → Recall:    {metrics['recall']:.3f}")

    # Retrain on full data for deployment
    pipeline.train(X, y)

    # Save model
    print("\n[4/4] Saving trained model...")
    pipeline.save()
    model_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"  → Model saved to: {os.path.join(model_dir, 'model.joblib')}")
    print(f"  → Scaler saved to: {os.path.join(model_dir, 'scaler.joblib')}")

    # Test prediction
    print("\n" + "=" * 60)
    print("Test Prediction:")
    print("=" * 60)

    test_features = {
        'github_total_commits': 150,
        'github_total_prs': 5,
        'github_total_repos': 12,
        'github_total_languages': 5,
        'leetcode_solved': 80,
        'leetcode_easy': 40,
        'leetcode_medium': 30,
        'leetcode_hard': 10,
        'leetcode_ranking': 45000,
        'codeforces_rating': 1400,
        'codeforces_max_rating': 1500,
        'codeforces_contests': 15,
        'commit_consistency_score': 0.65,
        'problem_solving_velocity': 4.5,
        'skill_keyword_density': 0.55,
        'api_skill_validation_ratio': 0.70,
        'project_skill_overlap': 0.45,
        'leetcode_hard_ratio': 0.125,
        'leetcode_medium_ratio': 0.375,
        'resume_word_count': 380,
        'resume_skills_count': 10,
        'jd_skills_count': 12,
    }

    explanation = pipeline.explain(test_features)
    print(f"\n  Job Match Score: {explanation['score']}%")
    print(f"\n  Top Positive Factors:")
    for label, value in explanation['top_positive'][:5]:
        print(f"    ✅ {label}: +{value:.3f}")
    print(f"\n  Top Negative Factors (Skill Gaps):")
    for label, value in explanation['top_negative'][:5]:
        print(f"    ❌ {label}: {value:.3f}")

    print("\n✅ Training complete! Model is ready for deployment.")


if __name__ == '__main__':
    main()
