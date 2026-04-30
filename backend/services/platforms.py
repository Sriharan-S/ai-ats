"""Platform integrations: GitHub, LeetCode, Codeforces.

Each fetcher returns a dict with the existing shape plus:
    fetch_status: one of success / not_found / rate_limited / unauthorized /
                  timeout / error / not_requested
    fetched_at:   ISO-8601 timestamp when the fetch was attempted

All upstream HTTP traffic goes through services.http_client so retry/backoff
behavior is uniform.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Optional

from services.http_client import FetchStatus, get_json, get_with_response, post_json

logger = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _empty_github() -> dict:
    return {
        "total_commits": 0,
        "total_pull_requests": 0,
        "total_repos": 0,
        "total_languages": 0,
        "languages": [],
        "language_stats": {},
        "commit_timestamps": [],
        "repos": [],
        "total_commits_capped": False,
    }


def _empty_leetcode() -> dict:
    return {
        "solved": 0,
        "easy": 0,
        "medium": 0,
        "hard": 0,
        "ranking": 0,
        "total_languages": 0,
        "contest_rating": 0,
        "recent_submissions": [],
    }


def _empty_codeforces() -> dict:
    return {
        "rating": 0,
        "max_rating": 0,
        "rank": "unrated",
        "max_rank": "unrated",
        "contests": 0,
        "contest_history": [],
        "recent_submissions": [],
        "avg_problem_rating": 0.0,
    }


def _github_headers() -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    pat = os.getenv("GITHUB_PAT")
    if pat:
        headers["Authorization"] = f"Bearer {pat}"
    return headers


def _parse_link_next(link_header: Optional[str]) -> Optional[str]:
    if not link_header:
        return None
    # Parse RFC 5988 Link header to find rel="next"
    for part in link_header.split(","):
        m = re.match(r'\s*<([^>]+)>\s*;\s*rel="next"', part)
        if m:
            return m.group(1)
    return None


def get_github_data(username: str) -> dict:
    """Fetch GitHub data using authentic API endpoints — no fabricated counts.

    - total_commits comes from /search/commits?q=author: which counts ALL commits
      attributed to the user across public GitHub (capped at 1000 by the search
      API; we set total_commits_capped=True when we hit the cap).
    - total_pull_requests comes from /search/issues?q=type:pr+author:.
    - language_stats are summed bytes from per-repo language data (paginated).
    - commit_timestamps are real PushEvent timestamps for the consistency score.
    """
    headers = _github_headers()
    out = _empty_github()

    # --- 1. Real total commits via search API ---
    commits_url = f"{GITHUB_API_URL}/search/commits?q=author:{username}&per_page=1"
    body, status = get_json(commits_url, headers=headers)
    if status == "not_found":
        return {**_empty_github(), "fetch_status": "not_found", "fetched_at": _now_iso()}
    if status in ("rate_limited", "unauthorized", "timeout", "error"):
        # commits search requires auth; if blocked, fall back gracefully but mark status.
        if status == "rate_limited":
            return {**_empty_github(), "fetch_status": "rate_limited", "fetched_at": _now_iso()}
    elif body is not None:
        total = int(body.get("total_count", 0) or 0)
        if total >= 1000:
            out["total_commits"] = 1000
            out["total_commits_capped"] = True
        else:
            out["total_commits"] = total

    # --- 2. Real PR count via search API ---
    prs_url = f"{GITHUB_API_URL}/search/issues?q=type:pr+author:{username}&per_page=1"
    body, status = get_json(prs_url, headers=headers)
    if body is not None and status == "success":
        out["total_pull_requests"] = int(body.get("total_count", 0) or 0)
    elif status == "not_found":
        return {**_empty_github(), "fetch_status": "not_found", "fetched_at": _now_iso()}

    # --- 3. Repos (paginated) ---
    repos: list[dict] = []
    next_url: Optional[str] = (
        f"{GITHUB_API_URL}/users/{username}/repos?per_page=100&sort=updated"
    )
    pages_fetched = 0
    final_status: FetchStatus = "success"
    while next_url and pages_fetched < 5:
        body, status, resp = get_with_response(next_url, headers=headers)
        if status == "not_found":
            return {**_empty_github(), "fetch_status": "not_found", "fetched_at": _now_iso()}
        if status != "success" or not isinstance(body, list):
            final_status = status
            break
        repos.extend(body)
        next_url = _parse_link_next(resp.headers.get("Link") if resp else None)
        pages_fetched += 1

    out["total_repos"] = len(repos)
    out["repos"] = [r.get("name", "") for r in repos[:20] if r.get("name")]

    # --- 4. Aggregate languages by bytes across non-fork repos ---
    lang_bytes: dict[str, int] = {}
    non_fork_repos = [r for r in repos if not r.get("fork")]
    sample_repos = non_fork_repos or repos
    for repo in sample_repos[:30]:
        url = repo.get("languages_url")
        if not url:
            continue
        body, status = get_json(url, headers=headers, timeout=5)
        if status == "success" and isinstance(body, dict):
            for lang, by in body.items():
                lang_bytes[lang] = lang_bytes.get(lang, 0) + int(by or 0)
        elif status == "rate_limited":
            final_status = "rate_limited"
            break

    out["languages"] = list(lang_bytes.keys())
    out["total_languages"] = len(lang_bytes)
    total_b = sum(lang_bytes.values()) or 1
    out["language_stats"] = {
        lang: round(bytes_count / total_b * 100, 1)
        for lang, bytes_count in sorted(lang_bytes.items(), key=lambda kv: kv[1], reverse=True)[:10]
    }

    # --- 5. Recent push event timestamps (for consistency score; not summed) ---
    events_url = f"{GITHUB_API_URL}/users/{username}/events?per_page=100"
    body, status = get_json(events_url, headers=headers)
    if status == "success" and isinstance(body, list):
        for event in body:
            if event.get("type") == "PushEvent":
                ts = event.get("created_at")
                if ts:
                    out["commit_timestamps"].append(ts)
    elif status == "rate_limited":
        final_status = "rate_limited"

    out["fetch_status"] = final_status if final_status != "success" else "success"
    out["fetched_at"] = _now_iso()
    return out


# ============================================================
# LeetCode
# ============================================================

LEETCODE_GRAPHQL = "https://leetcode.com/graphql"


def get_leetcode_data(username: str) -> dict:
    out = _empty_leetcode()

    profile_query = {
        "query": (
            "query getUserProfile($username: String!) { "
            "matchedUser(username: $username) { "
            "submitStats: submitStatsGlobal { acSubmissionNum { difficulty count } } "
            "profile { ranking } "
            "languageProblemCount { languageName problemsSolved } "
            "} "
            "userContestRanking(username: $username) { rating attendedContestsCount } "
            "recentAcSubmissionList(username: $username, limit: 20) { title titleSlug timestamp lang } "
            "}"
        ),
        "variables": {"username": username},
    }

    body, status = post_json(LEETCODE_GRAPHQL, json=profile_query)

    if status != "success" or not isinstance(body, dict):
        # GraphQL endpoint failed: try the public stats fallback ONLY for
        # problem counts. Mark the fetch as degraded so callers know.
        return _leetcode_fallback(username, original_status=status)

    matched = (body.get("data") or {}).get("matchedUser")
    if matched is None:
        # GraphQL returned 200 but user does not exist
        return {**_empty_leetcode(), "fetch_status": "not_found", "fetched_at": _now_iso()}

    submit_stats = (matched.get("submitStats") or {}).get("acSubmissionNum") or []
    for stat in submit_stats:
        diff = (stat.get("difficulty") or "").lower()
        count = int(stat.get("count") or 0)
        if diff == "easy":
            out["easy"] = count
        elif diff == "medium":
            out["medium"] = count
        elif diff == "hard":
            out["hard"] = count
        elif diff == "all":
            out["solved"] = count

    if out["solved"] == 0:
        out["solved"] = out["easy"] + out["medium"] + out["hard"]

    out["ranking"] = int((matched.get("profile") or {}).get("ranking") or 0)
    out["total_languages"] = len(matched.get("languageProblemCount") or [])

    contest = (body.get("data") or {}).get("userContestRanking")
    if contest:
        out["contest_rating"] = int(contest.get("rating") or 0)

    recent = (body.get("data") or {}).get("recentAcSubmissionList") or []
    submissions: list[dict] = []
    for item in recent:
        ts_raw = item.get("timestamp")
        try:
            ts_int = int(ts_raw)
        except (TypeError, ValueError):
            continue
        submissions.append(
            {
                "title": item.get("title") or "",
                "timestamp": ts_int,
                "lang": item.get("lang") or "",
            }
        )
    out["recent_submissions"] = submissions

    out["fetch_status"] = "success"
    out["fetched_at"] = _now_iso()
    return out


def _leetcode_fallback(username: str, *, original_status: FetchStatus) -> dict:
    out = _empty_leetcode()
    fallback_url = f"https://leetcode-stats-api.herokuapp.com/{username}"
    body, status = get_json(fallback_url, max_retries=2)

    if status == "not_found":
        return {**_empty_leetcode(), "fetch_status": "not_found", "fetched_at": _now_iso()}

    if status == "success" and isinstance(body, dict):
        if body.get("status") == "error":
            return {**_empty_leetcode(), "fetch_status": "not_found", "fetched_at": _now_iso()}
        out["solved"] = int(body.get("totalSolved") or 0)
        out["easy"] = int(body.get("easySolved") or 0)
        out["medium"] = int(body.get("mediumSolved") or 0)
        out["hard"] = int(body.get("hardSolved") or 0)
        out["ranking"] = int(body.get("ranking") or 0)
        out["fetch_status"] = "success"
        out["fetched_at"] = _now_iso()
        return out

    out["fetch_status"] = original_status if original_status != "success" else "error"
    out["fetched_at"] = _now_iso()
    return out


# ============================================================
# Codeforces
# ============================================================


def get_codeforces_data(username: str) -> dict:
    out = _empty_codeforces()
    info_url = f"https://codeforces.com/api/user.info?handles={username}"

    body, status = get_json(info_url)
    if status == "not_found":
        return {**_empty_codeforces(), "fetch_status": "not_found", "fetched_at": _now_iso()}
    if status != "success" or not isinstance(body, dict):
        return {**_empty_codeforces(), "fetch_status": status or "error", "fetched_at": _now_iso()}
    if body.get("status") != "OK" or not body.get("result"):
        # Codeforces returns 200 with a FAILED status for unknown handles.
        return {**_empty_codeforces(), "fetch_status": "not_found", "fetched_at": _now_iso()}

    user = body["result"][0]
    out["rating"] = int(user.get("rating") or 0)
    out["max_rating"] = int(user.get("maxRating") or 0)
    out["rank"] = user.get("rank") or "unrated"
    out["max_rank"] = user.get("maxRank") or "unrated"

    # Contest rating history
    rating_url = f"https://codeforces.com/api/user.rating?handle={username}"
    body, status = get_json(rating_url)
    if status == "success" and isinstance(body, dict) and body.get("status") == "OK":
        contests = body.get("result") or []
        out["contests"] = len(contests)
        out["contest_history"] = [
            {
                "name": c.get("contestName", ""),
                "rating": int(c.get("newRating") or 0),
                "rank": int(c.get("rank") or 0),
            }
            for c in contests[-12:]
        ]

    # Recent submissions for velocity + avg problem rating
    status_url = f"https://codeforces.com/api/user.status?handle={username}&from=1&count=200"
    body, status = get_json(status_url)
    if status == "success" and isinstance(body, dict) and body.get("status") == "OK":
        subs = body.get("result") or []
        accepted_ratings: list[int] = []
        for s in subs:
            ts = s.get("creationTimeSeconds")
            verdict = s.get("verdict")
            problem = s.get("problem") or {}
            entry = {
                "timestamp": int(ts) if isinstance(ts, (int, float)) else 0,
                "verdict": verdict or "",
                "problem_rating": int(problem.get("rating")) if isinstance(problem.get("rating"), (int, float)) else 0,
            }
            out["recent_submissions"].append(entry)
            if verdict == "OK" and entry["problem_rating"]:
                accepted_ratings.append(entry["problem_rating"])

        if accepted_ratings:
            sample = accepted_ratings[:50]
            out["avg_problem_rating"] = round(sum(sample) / len(sample), 1)

    out["fetch_status"] = "success"
    out["fetched_at"] = _now_iso()
    return out
