"""Framework and configuration-based UI route resolution."""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from urllib.parse import urljoin

from .models import LivingDocsConfig


def _expand_groups(template: str, match: re.Match[str]) -> str:
    value = template
    for index, group in enumerate(match.groups(), start=1):
        value = value.replace(f"{{{index}}}", group or "")
    return value


def _next_app_route(path: PurePosixPath) -> str | None:
    parts = list(path.parts)
    try:
        app_index = parts.index("app")
    except ValueError:
        return None
    tail = parts[app_index + 1 :]
    if not tail or tail[-1] not in {"page.tsx", "page.ts", "page.jsx", "page.js"}:
        return None
    segments = [
        segment
        for segment in tail[:-1]
        if not (segment.startswith("(") and segment.endswith(")"))
        and not segment.startswith("@")
    ]
    return "/" + "/".join(segments) if segments else "/"


def _next_pages_route(path: PurePosixPath) -> str | None:
    parts = list(path.parts)
    try:
        pages_index = parts.index("pages")
    except ValueError:
        return None
    tail = parts[pages_index + 1 :]
    if not tail:
        return None
    filename = tail[-1]
    suffix = PurePosixPath(filename).suffix
    if suffix not in {".tsx", ".ts", ".jsx", ".js"}:
        return None
    tail[-1] = filename[: -len(suffix)]
    if tail[-1] == "index":
        tail.pop()
    return "/" + "/".join(tail) if tail else "/"


def resolve_route(file_path: str, config: LivingDocsConfig) -> list[dict[str, str]]:
    normalized = file_path.replace("\\", "/").lstrip("./")
    candidates: set[str] = set()
    for mapping in config.mappings:
        match = re.search(mapping.pattern, normalized)
        if match:
            candidates.update(_expand_groups(url, match) for url in mapping.urls)

    posix_path = PurePosixPath(normalized)
    for candidate in (_next_app_route(posix_path), _next_pages_route(posix_path)):
        if candidate:
            candidates.add(candidate)

    base_url = str(config.base_url) if config.base_url else None
    return [
        {
            "route": route,
            "url": (
                urljoin(base_url.rstrip("/") + "/", route.lstrip("/"))
                if base_url and route.startswith("/")
                else route
            ),
        }
        for route in sorted(candidates)
    ]
