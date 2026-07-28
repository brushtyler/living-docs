"""Project boundary, origin, secret-substitution, and redaction helpers."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit

from .errors import (
    INPUT_PATH_DENIED,
    NAVIGATION_DENIED,
    OUTPUT_PATH_DENIED,
    LivingDocsError,
)

_ENV_REF = re.compile(r"\$\{ENV:([A-Za-z_][A-Za-z0-9_]*)\}")
_SENSITIVE_KEY = re.compile(
    r"(?:pass(?:word)?|secret|token|api[_-]?key|credential|cookie|session)",
    re.IGNORECASE,
)


def project_relative(path: Path, project_root: Path) -> str:
    return path.resolve().relative_to(project_root.resolve()).as_posix()


def _contained(candidate: Path, root: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


class ProjectBoundary:
    def __init__(self, project_root: Path, output_root: str = ".") -> None:
        self.project_root = project_root.expanduser().resolve()
        if Path(output_root).is_absolute():
            raise LivingDocsError(
                OUTPUT_PATH_DENIED,
                "security.output_root must be relative to the project root",
            )
        self.output_root = (self.project_root / output_root).resolve()
        if not _contained(self.output_root, self.project_root):
            raise LivingDocsError(
                OUTPUT_PATH_DENIED,
                "security.output_root escapes the project root",
            )

    def input_path(self, value: str, *, must_exist: bool = True) -> Path:
        raw = Path(value)
        if raw.is_absolute():
            raise LivingDocsError(INPUT_PATH_DENIED, "absolute input paths are not allowed")
        candidate = (self.project_root / raw).resolve()
        if not _contained(candidate, self.project_root):
            raise LivingDocsError(INPUT_PATH_DENIED, "input path escapes the project root")
        if must_exist and not candidate.exists():
            raise LivingDocsError(INPUT_PATH_DENIED, f"input path does not exist: {value}")
        return candidate

    def output_path(self, value: str, *, relative_to: Path | None = None) -> Path:
        raw = Path(value)
        if raw.is_absolute():
            raise LivingDocsError(OUTPUT_PATH_DENIED, "absolute output paths are not allowed")
        base = relative_to.resolve() if relative_to else self.project_root
        candidate = (base / raw).resolve()
        if not _contained(candidate, self.output_root):
            raise LivingDocsError(
                OUTPUT_PATH_DENIED,
                f"output path must remain under {project_relative(self.output_root, self.project_root)}",
            )
        return candidate


def origin_of(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise LivingDocsError(NAVIGATION_DENIED, "only http and https navigation is allowed")
    try:
        parsed_port = parsed.port
    except ValueError as exc:
        raise LivingDocsError(NAVIGATION_DENIED, "navigation URL has an invalid port") from exc
    default_port = (parsed.scheme == "http" and parsed_port == 80) or (
        parsed.scheme == "https" and parsed_port == 443
    )
    port = "" if parsed_port is None or default_port else f":{parsed_port}"
    return f"{parsed.scheme.lower()}://{parsed.hostname.lower()}{port}"


def resolve_navigation_url(
    value: str,
    *,
    base_url: str | None,
    allowed_origins: list[str],
) -> str:
    if value.startswith("/") and not value.startswith("//"):
        if not base_url:
            raise LivingDocsError(
                NAVIGATION_DENIED,
                "relative navigation requires base_url in living-docs-config.json",
            )
        resolved = urljoin(base_url.rstrip("/") + "/", value.lstrip("/"))
    else:
        resolved = value

    actual = origin_of(resolved)
    allowed = {origin_of(item) for item in allowed_origins}
    if actual not in allowed:
        raise LivingDocsError(
            NAVIGATION_DENIED,
            f"navigation origin {actual} is not allowed",
            {"allowed_origins": sorted(allowed)},
        )
    return resolved


def substitute_env(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: substitute_env(item) for key, item in value.items()}
    if isinstance(value, list):
        return [substitute_env(item) for item in value]
    if not isinstance(value, str):
        return value

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in os.environ:
            raise ValueError(f"environment variable {name} is not set")
        return os.environ[name]

    return _ENV_REF.sub(replace, value)


def literal_secret_paths(value: Any, prefix: str = "") -> list[str]:
    results: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if (
                _SENSITIVE_KEY.search(str(key))
                and isinstance(item, str)
                and item
                and not _ENV_REF.search(item)
            ):
                results.append(path)
            results.extend(literal_secret_paths(item, path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            results.extend(literal_secret_paths(item, f"{prefix}[{index}]"))
    return results


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: ("<redacted>" if _SENSITIVE_KEY.search(str(key)) else redact(item))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value
