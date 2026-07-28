"""Configuration loading with version-1 compatibility."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from .errors import CONFIG_INVALID, CONFIG_NOT_FOUND, LivingDocsError
from .models import LivingDocsConfig, WarningDetail
from .security import literal_secret_paths, substitute_env

DEFAULT_CONFIG_NAME = "living-docs-config.json"


def resolve_config_path(project_root: Path, explicit: str | Path | None = None) -> Path:
    root = project_root.expanduser().resolve()
    candidate = Path(explicit) if explicit is not None else Path(DEFAULT_CONFIG_NAME)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.expanduser().resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise LivingDocsError(
            CONFIG_INVALID,
            "configuration path must remain under the project root",
        ) from exc
    return candidate


def load_config(
    project_root: Path,
    explicit: str | Path | None = None,
    *,
    required: bool = False,
) -> tuple[LivingDocsConfig, Path, list[WarningDetail]]:
    path = resolve_config_path(project_root, explicit)
    if not path.exists():
        if required:
            raise LivingDocsError(CONFIG_NOT_FOUND, f"configuration not found: {path.name}")
        return (
            LivingDocsConfig(),
            path,
            [
                WarningDetail(
                    code=CONFIG_NOT_FOUND,
                    message=f"{path.name} was not found; configuration-dependent operations may fail",
                    path=path.name,
                )
            ],
        )

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("configuration root must be an object")
        secret_paths = literal_secret_paths(raw)
        substituted = substitute_env(raw)
        config = LivingDocsConfig.model_validate(substituted)
    except (OSError, json.JSONDecodeError, ValidationError, ValueError) as exc:
        raise LivingDocsError(CONFIG_INVALID, f"invalid configuration: {exc}") from exc

    warnings = [
        WarningDetail(
            code="LITERAL_SECRET",
            message="possible credential is stored literally; prefer ${ENV:NAME}",
            path=secret_path,
        )
        for secret_path in secret_paths
    ]
    return config, path, warnings
