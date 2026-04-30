"""Bootstrap training script for the ATS regression scorer.

IMPORTANT — this generator produces *rule-based bootstrap data*, not real
student outcomes. The target score is a hand-coded rubric that mirrors
common ATS keyword-matching expectations: text alignment dominates,
public-profile evidence is a bonus, and resume-only users are not
penalised into the floor. Replace this with a labelled dataset of real
student-job pairs before quoting metrics anywhere outside this codebase.

Usage:
    python -m ml.train_model
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.pipeline import (
    ATSPipeline,
    FEATURE_NAMES,
    evaluate_pipeline,
    write_meta,
)

MODEL_VERSION = "ats-v2.0.0"
FEATURE_VERSION = "features-v2.0.0"
DATASET_VERSION = "synthetic-bootstrap-v2"


def _compute_target_score(row: pd.Series) -> float:
    """Rule-based target score in [0, 100].

    The formula reflects how recruiters actually skim ATS results:
      - Text alignment with the JD is the dominant signal.
      - Platform evidence (GitHub commits, LeetCode solved, Codeforces
        rating) is a bonus when present, never a hard penalty when absent.
      - A baseline so a clean, well-keyworded resume scores well even with
        no public coding profiles.
    """
    # --- Text alignment (max contribution: ~60 points) ---
    text_component = (
        0.55 * row['skill_keyword_density']
        + 0.25 * row['project_skill_overlap']
        + 0.10 * min(row['resume_skills_count'] / 8.0, 1.0)
        + 0.10 * min(row['jd_skills_count'] / 8.0, 1.0)
    )  # 0..1

    # --- Platform evidence (max contribution: ~30 points) ---
    evidence = 0.0
    if row['has_github_profile']:
        evidence += 0.30 * row['commit_consistency_score']
        evidence += 0.30 * row['api_skill_validation_ratio']
        evidence += 0.20 * min(row['github_total_commits'] / 200.0, 1.0)
        evidence += 0.10 * min(row['github_total_prs'] / 20.0, 1.0)
        evidence += 0.10 * min(row['github_total_languages'] / 5.0, 1.0)
    if row['has_leetcode_profile']:
        evidence += 0.20 * min(row['leetcode_solved'] / 150.0, 1.0)
        evidence += 0.10 * row['leetcode_hard_ratio']
        evidence += 0.05 * row['leetcode_medium_ratio']
        evidence += 0.05 * min(row['problem_solving_velocity'] / 5.0, 1.0)
    if row['has_codeforces_profile']:
        evidence += 0.15 * min(row['codeforces_rating'] / 1800.0, 1.0)
        evidence += 0.10 * min(row['codeforces_avg_problem_rating'] / 1800.0, 1.0)
        evidence += 0.05 * min(row['codeforces_contests'] / 10.0, 1.0)
    evidence = min(evidence, 1.0)  # 0..1

    n_platforms = int(
        row['has_github_profile']
        + row['has_leetcode_profile']
        + row['has_codeforces_profile']
    )

    # --- Composite: weight text vs evidence based on what the user provided ---
    if n_platforms == 0:
        # Resume-only path: text plus a baseline so good text wins.
        score_unit = 0.30 + 0.65 * text_component
    elif n_platforms == 1:
        score_unit = 0.20 + 0.55 * text_component + 0.30 * evidence
    elif n_platforms == 2:
        score_unit = 0.15 + 0.55 * text_component + 0.35 * evidence
    else:  # all three platforms
        score_unit = 0.10 + 0.55 * text_component + 0.40 * evidence

    # Light penalties for fetch failures (the user tried to provide a profile
    # but we couldn't reach the upstream API).
    score_unit -= 0.03 * row['github_fetch_failed']
    score_unit -= 0.02 * row['leetcode_fetch_failed']
    score_unit -= 0.02 * row['codeforces_fetch_failed']

    score_unit = float(np.clip(score_unit, 0.0, 1.0))
    return score_unit * 100.0


def generate_bootstrap_data(n_samples: int = 800, random_state: int = 42):
    rng = np.random.RandomState(random_state)
    data: dict[str, np.ndarray] = {}

    # --- Raw GitHub ---
    data['github_total_commits'] = rng.exponential(120, n_samples).astype(int).clip(0, 1000)
    data['github_total_prs'] = rng.poisson(8, n_samples).clip(0, 100)
    data['github_total_repos'] = rng.poisson(10, n_samples).clip(0, 80)
    data['github_total_languages'] = rng.poisson(4, n_samples).clip(1, 15)

    # --- Raw LeetCode ---
    data['leetcode_solved'] = rng.exponential(60, n_samples).astype(int).clip(0, 500)
    total_solved = data['leetcode_solved']
    data['leetcode_easy'] = (total_solved * rng.beta(5, 3, n_samples)).astype(int)
    data['leetcode_medium'] = (total_solved * rng.beta(4, 5, n_samples)).astype(int)
    data['leetcode_hard'] = np.clip(
        total_solved - data['leetcode_easy'] - data['leetcode_medium'], 0, None
    ).astype(int)
    data['leetcode_ranking'] = rng.exponential(80000, n_samples).astype(int).clip(100, 500000)

    # --- Raw Codeforces ---
    data['codeforces_rating'] = rng.normal(1200, 400, n_samples).clip(0, 3000)
    data['codeforces_max_rating'] = (
        data['codeforces_rating'] + rng.exponential(100, n_samples)
    ).clip(0, 3500)
    data['codeforces_contests'] = rng.poisson(10, n_samples).clip(0, 100)
    data['codeforces_avg_problem_rating'] = (
        data['codeforces_rating'] + rng.normal(-50, 200, n_samples)
    ).clip(0, 3500)

    # --- Engineered ---
    data['commit_consistency_score'] = rng.beta(3, 3, n_samples).clip(0, 1)
    data['problem_solving_velocity'] = rng.exponential(3, n_samples).clip(0, 30)

    # Skill keyword density biased a bit higher — most users with a real
    # tech resume do hit half the JD's keywords.
    data['skill_keyword_density'] = rng.beta(4, 3, n_samples).clip(0, 1)
    data['api_skill_validation_ratio'] = rng.beta(4, 4, n_samples).clip(0, 1)
    data['project_skill_overlap'] = rng.beta(3, 4, n_samples).clip(0, 1)

    safe_total = np.maximum(total_solved, 1)
    data['leetcode_hard_ratio'] = data['leetcode_hard'] / safe_total
    data['leetcode_medium_ratio'] = data['leetcode_medium'] / safe_total

    # --- Resume / JD ---
    data['resume_word_count'] = rng.normal(350, 120, n_samples).astype(int).clip(50, 1000)
    data['resume_skills_count'] = rng.poisson(8, n_samples).clip(0, 30)
    data['jd_skills_count'] = rng.poisson(10, n_samples).clip(3, 25)

    # --- Missingness flags ---
    # Mix of platform patterns so the model learns all four combinations
    # well: 25% resume-only, 30% github-only, 20% github+leetcode, 25% all.
    pattern = rng.choice([0, 1, 2, 3], size=n_samples, p=[0.25, 0.30, 0.20, 0.25])
    has_github = (pattern >= 1).astype(int)
    has_leetcode = (pattern >= 2).astype(int)
    has_codeforces = (pattern >= 3).astype(int)
    data['has_github_profile'] = has_github
    data['has_leetcode_profile'] = has_leetcode
    data['has_codeforces_profile'] = has_codeforces

    data['github_fetch_failed'] = (rng.rand(n_samples) < 0.04).astype(int) * has_github
    data['leetcode_fetch_failed'] = (rng.rand(n_samples) < 0.04).astype(int) * has_leetcode
    data['codeforces_fetch_failed'] = (rng.rand(n_samples) < 0.04).astype(int) * has_codeforces

    # Zero out platform signals when the corresponding profile is "absent",
    # so the bootstrap row matches what a real "no profile" request looks like.
    no_gh = has_github == 0
    for key in ('github_total_commits', 'github_total_prs',
                'github_total_repos', 'github_total_languages',
                'commit_consistency_score', 'api_skill_validation_ratio'):
        data[key] = np.where(no_gh, 0, data[key])

    no_lc = has_leetcode == 0
    for key in ('leetcode_solved', 'leetcode_easy', 'leetcode_medium',
                'leetcode_hard', 'leetcode_ranking',
                'leetcode_hard_ratio', 'leetcode_medium_ratio',
                'problem_solving_velocity'):
        data[key] = np.where(no_lc, 0, data[key])

    no_cf = has_codeforces == 0
    for key in ('codeforces_rating', 'codeforces_max_rating',
                'codeforces_contests', 'codeforces_avg_problem_rating'):
        data[key] = np.where(no_cf, 0, data[key])

    df = pd.DataFrame(data)

    # Compute the target via the rubric, with a small noise term so the
    # learned model is robust to feature-order pertubation.
    targets = df.apply(_compute_target_score, axis=1).to_numpy(dtype=float)
    targets = targets + rng.normal(0.0, 3.0, n_samples)
    targets = np.clip(targets, 0.0, 100.0)

    return df, targets


def main():
    print("=" * 60)
    print("AIATS Pipeline - Bootstrap Training (Regression)")
    print(f"  model_version={MODEL_VERSION}")
    print(f"  feature_version={FEATURE_VERSION}")
    print(f"  dataset_version={DATASET_VERSION}")
    print("=" * 60)

    print("\n[1/4] Generating rule-based bootstrap data (800 samples)...")
    df, targets = generate_bootstrap_data(n_samples=800)
    target_summary = {
        'mean': float(np.mean(targets)),
        'p10': float(np.percentile(targets, 10)),
        'p50': float(np.percentile(targets, 50)),
        'p90': float(np.percentile(targets, 90)),
        'min': float(np.min(targets)),
        'max': float(np.max(targets)),
    }
    print(f"  -> Dataset shape: {df.shape}")
    print(f"  -> Target score distribution: "
          f"p10={target_summary['p10']:.1f} "
          f"p50={target_summary['p50']:.1f} "
          f"p90={target_summary['p90']:.1f} "
          f"(mean={target_summary['mean']:.1f})")

    missing = [name for name in FEATURE_NAMES if name not in df.columns]
    if missing:
        raise RuntimeError(f"Bootstrap dataset is missing features: {missing}")

    X = df[FEATURE_NAMES].values
    y = targets

    print("\n[2/4] 5-fold CV on the regression voting model...")
    metrics = evaluate_pipeline(X, y)
    print(f"  -> R^2:  {metrics['r2']:.3f}")
    print(f"  -> MAE:  {metrics['mae']:.2f}")
    print(f"  -> RMSE: {metrics['rmse']:.2f}")

    print("\n[3/4] Training pipeline on full dataset...")
    pipeline = ATSPipeline()
    pipeline.train(X, y)
    print("  -> Voting regressor + SHAP estimator fit successfully.")

    print("\n[4/4] Saving model bundle + metadata...")
    pipeline.save()
    write_meta(
        model_version=MODEL_VERSION,
        feature_version=FEATURE_VERSION,
        dataset_version=DATASET_VERSION,
        sample_size=int(len(y)),
        target_summary=target_summary,
        metrics=metrics,
    )
    print("  -> Saved model.joblib and model_meta.json")

    print("\n" + "=" * 60)
    print("Score sanity checks (expectation -> predicted):")
    print("=" * 60)

    scenarios = [
        ("Resume-only, strong text match", _scenario_resume_only_strong()),
        ("Resume-only, moderate text match", _scenario_resume_only_moderate()),
        ("Resume-only, weak text match", _scenario_resume_only_weak()),
        ("Resume + GitHub, moderate", _scenario_resume_github_moderate()),
        ("All platforms, strong overall", _scenario_all_platforms_strong()),
    ]
    for label, features in scenarios:
        score = pipeline.predict_score(features)
        print(f"  {label:<40} -> {score:5.1f}")

    print("\nDone. Model is ready.")


def _zero_features() -> dict:
    return {name: 0 for name in FEATURE_NAMES}


def _scenario_resume_only_strong() -> dict:
    f = _zero_features()
    f.update({
        'skill_keyword_density': 0.80,
        'project_skill_overlap': 0.45,
        'resume_word_count': 450,
        'resume_skills_count': 12,
        'jd_skills_count': 14,
    })
    return f


def _scenario_resume_only_moderate() -> dict:
    f = _zero_features()
    f.update({
        'skill_keyword_density': 0.50,
        'project_skill_overlap': 0.25,
        'resume_word_count': 350,
        'resume_skills_count': 8,
        'jd_skills_count': 10,
    })
    return f


def _scenario_resume_only_weak() -> dict:
    f = _zero_features()
    f.update({
        'skill_keyword_density': 0.20,
        'project_skill_overlap': 0.10,
        'resume_word_count': 200,
        'resume_skills_count': 3,
        'jd_skills_count': 12,
    })
    return f


def _scenario_resume_github_moderate() -> dict:
    f = _scenario_resume_only_moderate()
    f.update({
        'has_github_profile': 1,
        'github_total_commits': 150,
        'github_total_prs': 5,
        'github_total_repos': 8,
        'github_total_languages': 4,
        'commit_consistency_score': 0.55,
        'api_skill_validation_ratio': 0.50,
    })
    return f


def _scenario_all_platforms_strong() -> dict:
    f = _zero_features()
    f.update({
        'github_total_commits': 400,
        'github_total_prs': 15,
        'github_total_repos': 20,
        'github_total_languages': 6,
        'leetcode_solved': 200,
        'leetcode_easy': 80,
        'leetcode_medium': 90,
        'leetcode_hard': 30,
        'leetcode_ranking': 30000,
        'codeforces_rating': 1700,
        'codeforces_max_rating': 1750,
        'codeforces_contests': 20,
        'codeforces_avg_problem_rating': 1500,
        'commit_consistency_score': 0.75,
        'problem_solving_velocity': 6.0,
        'skill_keyword_density': 0.75,
        'api_skill_validation_ratio': 0.80,
        'project_skill_overlap': 0.45,
        'leetcode_hard_ratio': 0.15,
        'leetcode_medium_ratio': 0.45,
        'resume_word_count': 450,
        'resume_skills_count': 14,
        'jd_skills_count': 14,
        'has_github_profile': 1,
        'has_leetcode_profile': 1,
        'has_codeforces_profile': 1,
    })
    return f


if __name__ == '__main__':
    main()
