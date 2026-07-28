from __future__ import annotations

from pathlib import Path

from living_docs.errors import INVALID_RECIPE
from living_docs.recipes import scan_markdown

from conftest import write_recipe


def test_scanner_parses_complete_nested_json_and_locations(project: Path):
    markdown = write_recipe(
        project,
        recipe=r"""
{
  "prerequisites": [],
  "tasks": [
    {"action": "type", "selector": "input[name='q']", "text": "a } brace"},
    {"action": "snapshot_page", "filename": "docs/assets/page.png"}
  ]
}
""".strip(),
    )
    records, errors = scan_markdown(markdown, project)
    assert not errors
    assert len(records) == 1
    assert records[0].location.line == 2
    assert records[0].recipe_id.startswith("snapshot-")
    assert records[0].source_file == "docs/guide.md"
    assert records[0].recipe.tasks[0].text == "a } brace"


def test_scanner_requires_immediately_following_comment(project: Path):
    markdown = project / "guide.md"
    markdown.write_text(
        "![Page](page.png)\nSome prose.\n"
        '<!-- snapshot-recipe: {"tasks":[{"action":"goto","url":"/"}]} -->',
        encoding="utf-8",
    )
    records, errors = scan_markdown(markdown, project)
    assert records == []
    assert errors == []


def test_scanner_reports_malformed_object_with_source(project: Path):
    markdown = project / "guide.md"
    markdown.write_text(
        '![Page](page.png)\n<!-- snapshot-recipe: {"tasks": [} -->',
        encoding="utf-8",
    )
    records, errors = scan_markdown(markdown, project)
    assert not records
    assert errors[0].code == INVALID_RECIPE
    assert errors[0].details == {"line": 2, "column": 1}


def test_scanner_preserves_v1_default_login(project: Path):
    markdown = write_recipe(
        project,
        recipe='{"tasks":[{"action":"goto","url":"/"}]}',
    )
    records, errors = scan_markdown(markdown, project)
    assert not errors
    assert records[0].recipe.prerequisites == ["login"]


def test_recipe_id_is_stable_when_comment_moves(project: Path):
    markdown = write_recipe(project)
    first, _ = scan_markdown(markdown, project)
    updated = "\n\n" + markdown.read_text(encoding="utf-8")
    markdown.write_text(
        updated.replace("![Page](./assets/page.png)", "![Page](assets/page.png)"),
        encoding="utf-8",
    )
    second, _ = scan_markdown(markdown, project)
    assert first[0].recipe_id == second[0].recipe_id
