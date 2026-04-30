from __future__ import annotations

import json
import os

from fastapi import APIRouter

from ..runtime import ML_AVAILABLE

router = APIRouter()


def _read_meta() -> dict:
    try:
        from ml.pipeline import META_PATH
    except Exception:
        return {}
    try:
        if os.path.exists(META_PATH):
            with open(META_PATH, "r", encoding="utf-8") as fp:
                return json.load(fp)
    except Exception:
        return {}
    return {}


def _model_present() -> bool:
    if not ML_AVAILABLE:
        return False
    try:
        from ml.pipeline import MODEL_PATH
        return os.path.exists(MODEL_PATH)
    except Exception:
        return False


@router.get("/api/health")
def get_health():
    meta = _read_meta() if ML_AVAILABLE else {}
    return {
        "status": "ok",
        "model_loaded": _model_present(),
        "model_version": meta.get("model_version"),
        "feature_version": meta.get("feature_version"),
        "dataset_version": meta.get("dataset_version"),
        "feature_count": meta.get("feature_count"),
        "trained_at": meta.get("trained_at"),
    }
