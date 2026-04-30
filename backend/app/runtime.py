from __future__ import annotations


def _probe() -> bool:
    try:
        import sklearn  # noqa: F401
        import xgboost  # noqa: F401
        import shap  # noqa: F401
        import pdfplumber  # noqa: F401
        import numpy  # noqa: F401
        import pandas  # noqa: F401
        from docx import Document  # noqa: F401
        return True
    except Exception:
        return False


ML_AVAILABLE: bool = _probe()
