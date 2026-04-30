export type FetchStatus =
  | "success"
  | "not_found"
  | "rate_limited"
  | "unauthorized"
  | "timeout"
  | "error"
  | "not_requested";

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
  total_commits_capped?: boolean;
  fetch_status: FetchStatus;
  fetched_at: string;
}

export interface LeetCodeSubmission {
  title: string;
  timestamp: number;
  lang: string;
}

export interface LeetCodeProfile {
  solved: number;
  easy: number;
  medium: number;
  hard: number;
  ranking: number;
  total_languages: number;
  contest_rating: number;
  recent_submissions: LeetCodeSubmission[];
  fetch_status: FetchStatus;
  fetched_at: string;
}

export interface CodeforcesSubmission {
  timestamp: number;
  verdict: string;
  problem_rating: number;
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
  recent_submissions: CodeforcesSubmission[];
  avg_problem_rating: number;
  fetch_status: FetchStatus;
  fetched_at: string;
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
  analysis_id: string;
  model_version: string | null;
  feature_version: string | null;
  score: number;
  shap_values: Record<string, number>;
  top_positive: Array<[string, number]>;
  top_negative: Array<[string, number]>;
  missing_keywords: string[];
  recommendations: RecommendationSummary;
  platform_status: {
    github: FetchStatus;
    leetcode: FetchStatus;
    codeforces: FetchStatus;
  };
  platform_data: {
    github: {
      total_commits: number;
      total_repos: number;
      languages: string[];
      fetch_status: FetchStatus;
    };
    leetcode: {
      solved: number;
      ranking: number;
      fetch_status: FetchStatus;
    };
    codeforces: {
      rating: number;
      avg_problem_rating: number;
      fetch_status: FetchStatus;
    };
  };
}
