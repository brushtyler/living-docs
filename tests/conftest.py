from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def project(tmp_path: Path) -> Path:
    (tmp_path / "living-docs-config.json").write_text(
        json.dumps(
            {
                "base_url": "http://localhost:5050",
                "flows": {},
                "browser": {"offline": True},
                "security": {"output_root": "."},
            }
        ),
        encoding="utf-8",
    )
    return tmp_path


def write_recipe(
    project: Path,
    *,
    filename: str = "docs/guide.md",
    recipe: str | None = None,
) -> Path:
    path = project / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    body = recipe or """
{
  "prerequisites": [],
  "tasks": [
    {"action": "goto", "url": "/"},
    {"action": "snapshot_page", "filename": "assets/page.png"}
  ]
}
""".strip()
    path.write_text(
        f"![Page](./assets/page.png)\n<!-- snapshot-recipe: {body} -->\n",
        encoding="utf-8",
    )
    return path
