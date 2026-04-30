"""Shared HTTP client with retries, timeouts, and a FetchStatus contract.

Every external-API helper in the backend funnels through here so error
classification (not_found vs rate_limited vs timeout vs unknown) is consistent
and the platform endpoints can return a truthful `fetch_status` instead of
silently returning zeros.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)

FetchStatus = str  # one of: success not_found rate_limited unauthorized timeout error not_requested

_BACKOFF_SECONDS = (0.5, 1.0, 2.0)
_MAX_RETRY_SLEEP = 5.0


def _classify_response(resp: requests.Response) -> FetchStatus:
    if resp.status_code == 200:
        return "success"
    if resp.status_code == 404:
        return "not_found"
    if resp.status_code == 401:
        return "unauthorized"
    if resp.status_code == 403:
        # GitHub uses 403 for rate-limit exhaustion
        if resp.headers.get("X-RateLimit-Remaining") == "0":
            return "rate_limited"
        if "rate limit" in (resp.text or "").lower():
            return "rate_limited"
        return "unauthorized"
    if resp.status_code == 429:
        return "rate_limited"
    return "error"


def _retry_after_seconds(resp: requests.Response) -> Optional[float]:
    raw = resp.headers.get("Retry-After")
    if not raw:
        return None
    try:
        return min(float(raw), _MAX_RETRY_SLEEP)
    except ValueError:
        return None


def _request(
    method: str,
    url: str,
    *,
    headers: Optional[dict] = None,
    json: Any = None,
    timeout: float = 10.0,
    max_retries: int = 3,
) -> tuple[Optional[Any], FetchStatus, Optional[requests.Response]]:
    last_status: FetchStatus = "error"
    last_resp: Optional[requests.Response] = None

    for attempt in range(max_retries):
        try:
            resp = requests.request(
                method, url, headers=headers, json=json, timeout=timeout
            )
        except requests.Timeout:
            logger.info("HTTP timeout on %s (attempt %s)", url, attempt + 1)
            last_status = "timeout"
            time.sleep(_BACKOFF_SECONDS[min(attempt, len(_BACKOFF_SECONDS) - 1)])
            continue
        except requests.RequestException as exc:
            logger.info("HTTP error on %s (attempt %s): %s", url, attempt + 1, exc)
            last_status = "error"
            time.sleep(_BACKOFF_SECONDS[min(attempt, len(_BACKOFF_SECONDS) - 1)])
            continue

        last_resp = resp
        status = _classify_response(resp)
        last_status = status

        if status == "success":
            try:
                return resp.json(), status, resp
            except ValueError:
                return None, "error", resp

        if status == "rate_limited" and attempt + 1 < max_retries:
            sleep_s = _retry_after_seconds(resp) or _BACKOFF_SECONDS[
                min(attempt, len(_BACKOFF_SECONDS) - 1)
            ]
            logger.info("Rate limited on %s; sleeping %.2fs", url, sleep_s)
            time.sleep(sleep_s)
            continue

        # not_found / unauthorized / unknown error: no point retrying
        return None, status, resp

    return None, last_status, last_resp


def get_json(
    url: str,
    *,
    headers: Optional[dict] = None,
    timeout: float = 10.0,
    max_retries: int = 3,
) -> tuple[Optional[Any], FetchStatus]:
    body, status, _resp = _request(
        "GET", url, headers=headers, timeout=timeout, max_retries=max_retries
    )
    return body, status


def post_json(
    url: str,
    *,
    json: Any,
    headers: Optional[dict] = None,
    timeout: float = 10.0,
    max_retries: int = 3,
) -> tuple[Optional[Any], FetchStatus]:
    body, status, _resp = _request(
        "POST",
        url,
        headers=headers,
        json=json,
        timeout=timeout,
        max_retries=max_retries,
    )
    return body, status


def get_with_response(
    url: str,
    *,
    headers: Optional[dict] = None,
    timeout: float = 10.0,
    max_retries: int = 3,
) -> tuple[Optional[Any], FetchStatus, Optional[requests.Response]]:
    """GET that also returns the underlying response, for callers that need
    Link headers (pagination) or rate-limit headers."""
    return _request(
        "GET", url, headers=headers, timeout=timeout, max_retries=max_retries
    )
