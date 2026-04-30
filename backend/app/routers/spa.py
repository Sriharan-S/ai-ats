from __future__ import annotations

import os

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

from ..errors import structured_error
from ..paths import FRONTEND_DIST

router = APIRouter()


@router.get("/")
def serve_root():
    return _serve_path("")


@router.get("/{path:path}")
def serve_frontend(path: str):
    if path.startswith("api/"):
        return structured_error("API_NOT_FOUND", "API route not found.", status=404)
    return _serve_path(path)


def _serve_path(path: str):
    if path:
        candidate = os.path.join(FRONTEND_DIST, path)
        if os.path.exists(candidate) and os.path.isfile(candidate):
            return FileResponse(candidate)

    index_path = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)

    return JSONResponse(
        content={
            "status": "frontend_not_built",
            "message": "Run the TypeScript frontend with `npm run dev` or build it with `npm run build`.",
        },
        status_code=404,
    )
