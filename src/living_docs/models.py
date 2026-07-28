"""Pydantic contracts for configuration, recipes, and public results."""

from __future__ import annotations

import re
from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)


def _validate_selector(value: str) -> str:
    """Catch malformed CSS selectors without requiring a browser process."""
    value = value.strip()
    if not value:
        raise ValueError("selector must not be empty")
    if any(ord(char) < 32 for char in value):
        raise ValueError("selector contains control characters")

    pairs = {"]": "[", ")": "("}
    stack: list[str] = []
    quote: str | None = None
    escaped = False
    for char in value:
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if quote:
            if char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
        elif char in {"[", "("}:
            stack.append(char)
        elif char in pairs:
            if not stack or stack.pop() != pairs[char]:
                raise ValueError("selector has unbalanced delimiters")
    if quote or stack:
        raise ValueError("selector has unbalanced quotes or delimiters")
    return value


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SelectorAction(StrictModel):
    selector: str
    timeout: float = Field(default=10, gt=0, le=300)

    @field_validator("selector")
    @classmethod
    def selector_is_valid(cls, value: str) -> str:
        return _validate_selector(value)


class GotoAction(StrictModel):
    action: Literal["goto"]
    url: str = Field(min_length=1)


class ClickAction(SelectorAction):
    action: Literal["click"]


class TypeAction(SelectorAction):
    action: Literal["type"]
    text: str


class WaitAction(StrictModel):
    action: Literal["wait"]
    seconds: float = Field(default=1, ge=0, le=300)


class WaitForSelectorAction(SelectorAction):
    action: Literal["wait_for_selector"]


class WaitForHiddenAction(SelectorAction):
    action: Literal["wait_for_hidden"]


class WaitForTextAction(SelectorAction):
    action: Literal["wait_for_text"]
    text: str = Field(min_length=1)


class HighlightAction(SelectorAction):
    action: Literal["highlight"]
    style: Literal["outline", "spotlight", "badge"] = "outline"
    color: str = Field(default="#ff3366", min_length=1, max_length=128)


class ClearHighlightsAction(StrictModel):
    action: Literal["clear_highlights"]


class SnapshotPageAction(StrictModel):
    action: Literal["snapshot_page", "snapshot"]
    filename: str = Field(default="screenshot.png", min_length=1)


class SnapshotElementAction(SelectorAction):
    action: Literal["snapshot_element"]
    filename: str = Field(default="element.png", min_length=1)


class ExtractInfoAction(SelectorAction):
    action: Literal["extract_info"]
    key: str | None = Field(default=None, min_length=1)


class SaveSessionAction(StrictModel):
    action: Literal["save_session"]
    filename: str = Field(default=".living-docs-session.json", min_length=1)


class RestoreSessionAction(StrictModel):
    action: Literal["restore_session"]
    filename: str = Field(min_length=1)


Action = Annotated[
    GotoAction
    | ClickAction
    | TypeAction
    | WaitAction
    | WaitForSelectorAction
    | WaitForHiddenAction
    | WaitForTextAction
    | HighlightAction
    | ClearHighlightsAction
    | SnapshotPageAction
    | SnapshotElementAction
    | ExtractInfoAction
    | SaveSessionAction
    | RestoreSessionAction,
    Field(discriminator="action"),
]


class Recipe(StrictModel):
    prerequisites: list[str] = Field(default_factory=list)
    tasks: list[Action] = Field(min_length=1)

    @field_validator("prerequisites")
    @classmethod
    def prerequisite_names_are_valid(cls, values: list[str]) -> list[str]:
        for value in values:
            if not value or value.strip() != value:
                raise ValueError("prerequisite names must be non-empty and trimmed")
        if len(values) != len(set(values)):
            raise ValueError("prerequisites must not contain duplicates")
        return values


class BrowserConfig(StrictModel):
    binary_path: str | None = None
    driver_path: str | None = None
    headless: bool = True
    window_size: tuple[int, int] = (1920, 1080)
    offline: bool = False

    @field_validator("window_size")
    @classmethod
    def window_size_is_sensible(cls, value: tuple[int, int]) -> tuple[int, int]:
        if not all(100 <= item <= 16_384 for item in value):
            raise ValueError("window_size values must be between 100 and 16384")
        return value


class SecurityConfig(StrictModel):
    allowed_origins: list[str] = Field(default_factory=list)
    output_root: str = "."


class RouteMapping(BaseModel):
    model_config = ConfigDict(extra="allow")

    pattern: str = Field(min_length=1)
    urls: list[str] = Field(default_factory=list)
    description: str | None = None

    @field_validator("pattern")
    @classmethod
    def pattern_is_valid(cls, value: str) -> str:
        try:
            re.compile(value)
        except re.error as exc:
            raise ValueError(f"invalid mapping regular expression: {exc}") from exc
        return value


class LivingDocsConfig(BaseModel):
    """Version-1 files remain valid; unknown top-level keys are preserved."""

    model_config = ConfigDict(extra="allow")

    schema_version: int = Field(default=1, ge=1)
    base_url: HttpUrl | None = None
    flows: dict[str, list[Action]] = Field(default_factory=dict)
    mappings: list[RouteMapping] = Field(default_factory=list)
    workers: int = Field(default=1, ge=1, le=16)
    reuse_session: bool = True
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    @model_validator(mode="after")
    def default_origin_from_base_url(self) -> "LivingDocsConfig":
        if not self.security.allowed_origins and self.base_url is not None:
            url = self.base_url
            port = f":{url.port}" if url.port else ""
            self.security.allowed_origins = [f"{url.scheme}://{url.host}{port}"]
        return self


class SourceLocation(StrictModel):
    line: int = Field(ge=1)
    column: int = Field(ge=1)
    end_line: int = Field(ge=1)
    end_column: int = Field(ge=1)


class RecipeRecord(StrictModel):
    recipe_id: str
    source_file: str
    image_path: str
    alt: str
    location: SourceLocation
    recipe: Recipe


class WarningDetail(StrictModel):
    code: str
    message: str
    path: str | None = None


class ErrorDetail(StrictModel):
    code: str
    message: str
    path: str | None = None
    details: dict[str, Any] | None = None


class Artifact(StrictModel):
    path: str
    kind: Literal["image", "metadata", "session"]
    media_type: str | None = None
    width: int | None = None
    height: int | None = None


class ElementMetadata(StrictModel):
    key: str | None = None
    selector: str
    text: str
    tag: str
    attributes: dict[str, str] = Field(default_factory=dict)


class CaptureProvenance(StrictModel):
    captured_at: str
    recipe_sha256: str
    target_path: str | None = None
    source_revision: str | None = None
    browser_name: str | None = None
    browser_version: str | None = None
    driver_version: str | None = None
    viewport: tuple[int, int]
    final_url: str | None = None


class ReviewDetail(StrictModel):
    status: Literal["new", "changed", "unchanged"]
    target_path: str
    candidate_path: str
    diff_path: str | None = None
    current_sha256: str | None = None
    candidate_sha256: str


class OperationResult(StrictModel):
    ok: bool
    summary: str
    data: dict[str, Any] = Field(default_factory=dict)
    artifacts: list[Artifact] = Field(default_factory=list)
    warnings: list[WarningDetail] = Field(default_factory=list)
    errors: list[ErrorDetail] = Field(default_factory=list)


class SyncPlanItem(StrictModel):
    recipe_id: str
    owner: str
    source_file: str
    image_path: str
    target_path: str
    action_count: int = Field(ge=1)
    prerequisites: list[str] = Field(default_factory=list)


class SyncOutcome(StrictModel):
    recipe_id: str
    source_file: str
    image_path: str
    target_path: str
    ok: bool
    error: ErrorDetail | None = None
    artifacts: list[Artifact] = Field(default_factory=list)
    provenance: CaptureProvenance | None = None
    reviews: list[ReviewDetail] = Field(default_factory=list)
