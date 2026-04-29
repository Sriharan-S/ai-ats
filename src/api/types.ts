export interface ApiError {
  error: string | {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

export interface GitHubProfile {
  total_commits: number;
  total_pull_requests: number;
  total_repos: number;
  total_languages: number;
  languages: string[];
  language_stats: Record<string, number>;
  commit_timestamps: string[];
  repos: string[];
}

export interface LeetCodeProfile {
  solved: number;
  easy: number;
  medium: number;
  hard: number;
  ranking: number;
  total_languages: number;
  recent_submissions: unknown[];
}

export interface CodeforcesProfile {
  rating: number;
  max_rating: number;
  rank: string;
  max_rank: string;
  contests: number;
  contest_history: Array<{
    name: string;
    rating: number;
    rank: number;
  }>;
}

export interface RecommendationGap {
  skill: string;
  advice: string;
  action: string;
  topic: string | null;
  shap_impact: number;
  feature_label: string;
  roadmap_available: boolean;
  roadmap_url: string | null;
}

export interface RecommendationSummary {
  score: number;
  summary: string;
  priority: "low" | "medium" | "high" | "critical";
  gaps: RecommendationGap[];
  total_gaps: number;
}

export interface AtsAnalysisResponse {
  score: number;
  shap_values: Record<string, number>;
  top_positive: Array<[string, number]>;
  top_negative: Array<[string, number]>;
  missing_keywords: string[];
  recommendations: RecommendationSummary;
  platform_data: {
    github: {
      total_commits: number;
      total_repos: number;
      languages: string[];
    };
    leetcode: {
      solved: number;
      ranking: number;
    };
    codeforces: {
      rating: number;
    };
  };
}
