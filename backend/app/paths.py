from __future__ import annotations

import os

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
FRONTEND_DIST = os.path.abspath(os.path.join(BACKEND_DIR, os.pardir, "frontend", "dist"))
ROADMAP_DIR = os.path.join(BACKEND_DIR, "roadmap-content")
