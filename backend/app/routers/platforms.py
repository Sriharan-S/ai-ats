from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse

from services.platforms import (
    get_codeforces_data,
    get_github_data,
    get_leetcode_data,
)

from ..errors import http_status_for_fetch

router = APIRouter()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@router.get("/api/track/github/{username}")
def track_github(username: str):
    data = get_github_data(username)
    return JSONResponse(content=data, status_code=http_status_for_fetch(data.get("fetch_status", "error")))


@router.get("/api/track/leetcode/{username}")
def track_leetcode(username: str):
    data = get_leetcode_data(username)
    return JSONResponse(content=data, status_code=http_status_for_fetch(data.get("fetch_status", "error")))


@router.get("/api/track/codeforces/{username}")
def track_codeforces(username: str):
    data = get_codeforces_data(username)
    return JSONResponse(content=data, status_code=http_status_for_fetch(data.get("fetch_status", "error")))


@router.post("/api/profile")
def post_profile(payload: dict = Body(default={})):
    data = payload or {}
    out: dict = {}
    status_map: dict = {}

    if data.get("github"):
        github_data = get_github_data(data["github"])
        out["github"] = github_data
        status_map["github"] = github_data.get("fetch_status", "error")
    else:
        status_map["github"] = "not_requested"

    if data.get("leetcode"):
        leetcode_data = get_leetcode_data(data["leetcode"])
        out["leetcode"] = leetcode_data
        status_map["leetcode"] = leetcode_data.get("fetch_status", "error")
    else:
        status_map["leetcode"] = "not_requested"

    if data.get("codeforces"):
        cf_data = get_codeforces_data(data["codeforces"])
        out["codeforces"] = cf_data
        status_map["codeforces"] = cf_data.get("fetch_status", "error")
    else:
        status_map["codeforces"] = "not_requested"

    return {"data": out, "status": status_map, "fetched_at": _now_iso()}
