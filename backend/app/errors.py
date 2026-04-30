from __future__ import annotations

from fastapi.responses import JSONResponse


def structured_error(code: str, message: str, *, details: dict | None = None, status: int = 400) -> JSONResponse:
    return JSONResponse(
        {"error": {"code": code, "message": message, "details": details or {}}},
        status_code=status,
    )


def http_status_for_fetch(status: str) -> int:
    if status == "success":
        return 200
    if status == "not_found":
        return 404
    if status in ("rate_limited", "timeout"):
        return 503
    if status == "unauthorized":
        return 401
    return 200
