from __future__ import annotations

import logging
import os

from app import create_app

logger = logging.getLogger("aiats")

app = create_app()


if __name__ == "__main__":
    import uvicorn

    port_value = os.getenv("PORT")
    if not port_value:
        raise RuntimeError("PORT must be defined in backend/.env")
    host_value = os.getenv("HOST")
    if not host_value:
        raise RuntimeError("HOST must be defined in backend/.env")

    legacy_debug = os.getenv("FLASK_DEBUG")
    if legacy_debug is not None and os.getenv("APP_DEBUG") is None:
        logger.warning("FLASK_DEBUG is deprecated; use APP_DEBUG in backend/.env.")
    debug_enabled = os.getenv("APP_DEBUG", legacy_debug or "0") == "1"

    uvicorn.run(
        "main:app",
        host=host_value,
        port=int(port_value),
        reload=debug_enabled,
    )
