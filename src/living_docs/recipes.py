"""Markdown snapshot-recipe scanner."""

from __future__ import annotations

import hashlib
import json
import posixpath
import re
from pathlib import Path

from pydantic import ValidationError

from .errors import INVALID_RECIPE
from .models import ErrorDetail, Recipe, RecipeRecord, SourceLocation
from .security import project_relative

_IMAGE = re.compile(r"!\[(?P<alt>[^\]\r\n]*)\]\((?P<path>[^)\r\n]+)\)")
_MARKER = re.compile(r"<!--\s*snapshot-recipe\s*:\s*", re.IGNORECASE)


def recipe_id(source_file: str, image_path: str) -> str:
    normalized_image = posixpath.normpath(
        posixpath.join(
            posixpath.dirname(source_file),
            image_path.strip().replace("\\", "/"),
        )
    )
    identity = f"{source_file}\0{normalized_image}".encode()
    return f"snapshot-{hashlib.sha256(identity).hexdigest()[:16]}"


def _position(content: str, offset: int) -> tuple[int, int]:
    line = content.count("\n", 0, offset) + 1
    last_newline = content.rfind("\n", 0, offset)
    column = offset + 1 if last_newline < 0 else offset - last_newline
    return line, column


def _location(content: str, start: int, end: int) -> SourceLocation:
    line, column = _position(content, start)
    end_line, end_column = _position(content, end)
    return SourceLocation(
        line=line,
        column=column,
        end_line=end_line,
        end_column=end_column,
    )


def _scan_json_object(content: str, start: int) -> int:
    if start >= len(content) or content[start] != "{":
        raise ValueError("recipe must begin with a JSON object")
    depth = 0
    quoted = False
    escaped = False
    for index in range(start, len(content)):
        char = content[index]
        if escaped:
            escaped = False
            continue
        if quoted:
            if char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            quoted = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index + 1
            if depth < 0:
                break
    raise ValueError("recipe JSON object is incomplete")


def scan_markdown(
    markdown_path: Path,
    project_root: Path,
) -> tuple[list[RecipeRecord], list[ErrorDetail]]:
    content = markdown_path.read_text(encoding="utf-8")
    records: list[RecipeRecord] = []
    errors: list[ErrorDetail] = []
    source_file = project_relative(markdown_path, project_root)

    for image in _IMAGE.finditer(content):
        cursor = image.end()
        while cursor < len(content) and content[cursor].isspace():
            cursor += 1
        marker = _MARKER.match(content, cursor)
        if marker is None:
            continue

        recipe_start = marker.end()
        try:
            recipe_end = _scan_json_object(content, recipe_start)
            closing = content.find("-->", recipe_end)
            if closing < 0 or content[recipe_end:closing].strip():
                raise ValueError("recipe comment must end immediately after the JSON object")
            raw = json.loads(content[recipe_start:recipe_end])
            if not isinstance(raw, dict):
                raise ValueError("recipe must be a JSON object")
            # Version 1 extraction defaulted omitted prerequisites to login.
            raw.setdefault("prerequisites", ["login"])
            recipe = Recipe.model_validate(raw)
            records.append(
                RecipeRecord(
                    recipe_id=recipe_id(source_file, image.group("path")),
                    source_file=source_file,
                    image_path=image.group("path").strip(),
                    alt=image.group("alt"),
                    location=_location(content, cursor, closing + 3),
                    recipe=recipe,
                )
            )
        except (ValueError, json.JSONDecodeError, ValidationError) as exc:
            line, column = _position(content, cursor)
            errors.append(
                ErrorDetail(
                    code=INVALID_RECIPE,
                    message=f"{source_file}:{line}:{column}: {exc}",
                    path=source_file,
                    details={"line": line, "column": column},
                )
            )
    return records, errors


def find_markdown_files(project_root: Path) -> list[Path]:
    ignored = {".git", ".venv", "venv", "node_modules", ".codegraph"}
    return sorted(
        path
        for path in project_root.rglob("*.md")
        if not any(part in ignored for part in path.relative_to(project_root).parts)
    )


def scan_project(
    project_root: Path,
    files: list[Path] | None = None,
) -> tuple[list[RecipeRecord], list[ErrorDetail]]:
    records: list[RecipeRecord] = []
    errors: list[ErrorDetail] = []
    for path in files if files is not None else find_markdown_files(project_root):
        found, scan_errors = scan_markdown(path, project_root)
        records.extend(found)
        errors.extend(scan_errors)
    return records, errors
