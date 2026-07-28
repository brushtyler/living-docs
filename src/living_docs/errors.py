"""Stable application errors shared by the CLI and MCP server."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


INVALID_RECIPE = "INVALID_RECIPE"
DUPLICATE_OUTPUT = "DUPLICATE_OUTPUT"
BROWSER_UNAVAILABLE = "BROWSER_UNAVAILABLE"
NAVIGATION_DENIED = "NAVIGATION_DENIED"
ELEMENT_TIMEOUT = "ELEMENT_TIMEOUT"
OUTPUT_PATH_DENIED = "OUTPUT_PATH_DENIED"
INPUT_PATH_DENIED = "INPUT_PATH_DENIED"
CONFIG_INVALID = "CONFIG_INVALID"
CONFIG_NOT_FOUND = "CONFIG_NOT_FOUND"
GIT_UNAVAILABLE = "GIT_UNAVAILABLE"
CAPTURE_FAILED = "CAPTURE_FAILED"
CANCELLED = "CANCELLED"
INIT_FAILED = "INIT_FAILED"


@dataclass(slots=True)
class LivingDocsError(Exception):
    """An expected failure with a stable machine-readable code."""

    code: str
    message: str
    details: dict[str, Any] | None = None

    def __str__(self) -> str:
        return self.message
