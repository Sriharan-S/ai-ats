from __future__ import annotations

import json
import os
from typing import Any

from fastapi import APIRouter

from ..errors import structured_error
from ..paths import ROADMAP_DIR

router = APIRouter()

ROLE_KEYWORDS = {
    "frontend", "backend", "devops", "full-stack", "data-analyst",
    "android", "ios", "blockchain", "qa", "software-architect",
    "cyber-security", "ux-design", "game-developer", "mlops",
    "ai-engineer", "ai-data-scientist", "engineering-manager",
    "product-manager", "technical-writer", "devrel",
}

_LISTING_CACHE: list[dict] | None = None
_DETAIL_CACHE: dict[str, dict] = {}


def _load_roadmap_data(slug: str) -> dict:
    if slug in _DETAIL_CACHE:
        return _DETAIL_CACHE[slug]
    path = os.path.join(ROADMAP_DIR, f"{slug}.json")
    with open(path, "r", encoding="utf-8") as fp:
        data = json.load(fp)
    _DETAIL_CACHE[slug] = data
    return data


def _list_slugs() -> list[str]:
    try:
        return sorted(
            f[:-5] for f in os.listdir(ROADMAP_DIR) if f.endswith(".json")
        )
    except FileNotFoundError:
        return []


@router.get("/api/roadmaps")
def list_roadmaps():
    global _LISTING_CACHE
    if _LISTING_CACHE is not None:
        return _LISTING_CACHE

    roadmaps: list[dict] = []
    for slug in _list_slugs():
        try:
            data = _load_roadmap_data(slug)
        except Exception:
            data = {}

        topics = data.get("nodes") or data.get("topics") or data.get("items")
        if topics is None and isinstance(data, dict):
            topics = data
        if topics is None:
            topics = []
        topic_count = len(topics) if isinstance(topics, (list, dict)) else 0

        roadmaps.append(
            {
                "slug": slug,
                "name": slug.replace("-", " ").title(),
                "category": "Role Based" if slug in ROLE_KEYWORDS else "Skill Based",
                "topicsCount": topic_count,
                "description": f"Curated learning roadmap for {slug.replace('-', ' ')}.",
            }
        )

    _LISTING_CACHE = roadmaps
    return roadmaps


@router.get("/api/roadmaps/{slug:path}")
def get_roadmap(slug: str):
    try:
        data = _load_roadmap_data(slug)
    except FileNotFoundError:
        return structured_error("ROADMAP_NOT_FOUND", "Roadmap not found.", status=404)

    raw_topics: Any = data.get("nodes") or data.get("topics") or data.get("items")
    if raw_topics is None and isinstance(data, dict):
        raw_topics = data
    if raw_topics is None:
        raw_topics = []

    if isinstance(raw_topics, dict):
        iterable = raw_topics.values()
    elif isinstance(raw_topics, list):
        iterable = raw_topics
    else:
        iterable = []

    topics = []
    for index, item in enumerate(iterable, start=1):
        if not isinstance(item, dict):
            continue
        title = item.get("title") or item.get("label") or item.get("name") or f"Topic {index}"
        description = item.get("description") or item.get("content") or ""
        links = item.get("links") or item.get("resources") or []
        resources = []
        if isinstance(links, list):
            for link in links:
                if isinstance(link, dict):
                    resources.append(
                        {
                            "title": link.get("title")
                            or link.get("label")
                            or link.get("url")
                            or "Resource",
                            "url": link.get("url") or link.get("href") or "#",
                            "type": link.get("type") or "resource",
                        }
                    )
        topics.append(
            {
                "id": index,
                "title": title,
                "status": "not-started",
                "description": description,
                "resources": resources,
            }
        )

    return {
        "slug": slug,
        "title": slug.replace("-", " ").title(),
        "summary": f"A curated learning path for {slug.replace('-', ' ')}.",
        "topics": topics,
    }
