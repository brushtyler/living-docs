from __future__ import annotations

import json
from pathlib import Path

from living_docs.browser import DriverFactory
from living_docs.cli import main
from living_docs.errors import DUPLICATE_OUTPUT, INVALID_RECIPE
from living_docs.runtime import LivingDocsRuntime

from conftest import write_recipe


def test_invalid_recipe_fails_before_chrome(project: Path, monkeypatch):
    markdown = write_recipe(
        project,
        recipe="""
{
  "prerequisites": [],
  "tasks": [
    {"action": "goto", "url": "https://denied.example"},
    {"action": "snapshot_page", "filename": "docs/assets/page.png"}
  ]
}
""".strip(),
    )
    started = False

    def create(_self):
        nonlocal started
        started = True
        raise AssertionError("Chrome must not start")

    monkeypatch.setattr(DriverFactory, "create", create)
    result = LivingDocsRuntime(project).apply_snapshot_sync(
        only_files=[markdown.relative_to(project).as_posix()]
    )
    assert not result.ok
    assert result.errors[0].code == "NAVIGATION_DENIED"
    assert not started


def test_cli_json_success_and_validation_exit_codes(project: Path, capsys):
    write_recipe(project)
    code = main(["--project-root", str(project), "plan-sync", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["ok"] is True
    assert payload["data"]["count"] == 1

    bad = project / "bad.md"
    bad.write_text(
        '![x](x.png)\n<!-- snapshot-recipe: {"tasks":[{"action":"wat"}]} -->',
        encoding="utf-8",
    )
    code = main(
        [
            "--project-root",
            str(project),
            "validate-recipes",
            "bad.md",
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == 2
    assert payload["errors"][0]["code"] == "INVALID_RECIPE"


def test_markdown_image_path_is_inside_output_boundary(project: Path):
    markdown = project / "docs/escape.md"
    markdown.parent.mkdir()
    markdown.write_text(
        """
![Escape](../../outside.png)
<!-- snapshot-recipe: {
  "prerequisites": [],
  "tasks": [{"action": "goto", "url": "/"}]
} -->
""".strip(),
        encoding="utf-8",
    )
    result = LivingDocsRuntime(project).plan_snapshot_sync(
        only_files=["docs/escape.md"]
    )
    assert not result.ok
    assert result.errors[0].code == "OUTPUT_PATH_DENIED"


def test_duplicate_image_owners_are_rejected(project: Path):
    write_recipe(project, filename="docs/one.md")
    write_recipe(project, filename="docs/two.md")
    result = LivingDocsRuntime(project).plan_snapshot_sync()
    assert not result.ok
    assert result.errors[0].code == DUPLICATE_OUTPUT
    assert result.errors[0].details["target_path"] == "docs/assets/page.png"


def test_duplicate_image_owners_use_validation_exit_code(
    project: Path,
    capsys,
):
    write_recipe(project, filename="docs/one.md")
    write_recipe(project, filename="docs/two.md")
    code = main(["--project-root", str(project), "plan-sync", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 2
    assert payload["errors"][0]["code"] == DUPLICATE_OUTPUT


def test_recipe_must_capture_its_markdown_image(project: Path):
    write_recipe(
        project,
        recipe="""
{
  "prerequisites": [],
  "tasks": [
    {"action": "goto", "url": "/"},
    {"action": "snapshot_page", "filename": "assets/different.png"}
  ]
}
""".strip(),
    )
    result = LivingDocsRuntime(project).validate_recipes()
    assert not result.ok
    assert result.errors[0].code == INVALID_RECIPE


def test_source_change_reports_impacted_snapshot(project: Path):
    config = json.loads((project / "living-docs-config.json").read_text(encoding="utf-8"))
    config["mappings"] = [
        {
            "pattern": r"src/components/(.*)\.tsx",
            "urls": ["/preview/{1}"],
        }
    ]
    (project / "living-docs-config.json").write_text(
        json.dumps(config),
        encoding="utf-8",
    )
    write_recipe(
        project,
        recipe="""
{
  "prerequisites": [],
  "tasks": [
    {"action": "goto", "url": "/preview/Card"},
    {"action": "snapshot_page", "filename": "assets/page.png"}
  ]
}
""".strip(),
    )
    impact = LivingDocsRuntime(project).snapshots.impacts(
        ["src/components/Card.tsx"]
    )
    assert impact["impacted_snapshots"] == 1
    snapshot = impact["impacts"][0]["snapshots"][0]
    assert snapshot["owner"] == "docs/guide.md"
    assert snapshot["target_path"] == "docs/assets/page.png"


def test_dynamic_source_route_matches_concrete_recipe_url(project: Path):
    write_recipe(
        project,
        recipe="""
{
  "prerequisites": [],
  "tasks": [
    {"action": "goto", "url": "/users/42"},
    {"action": "snapshot_page", "filename": "assets/page.png"}
  ]
}
""".strip(),
    )
    impact = LivingDocsRuntime(project).snapshots.impacts(
        ["src/app/users/[id]/page.tsx"]
    )
    snapshot = impact["impacts"][0]["snapshots"][0]
    assert snapshot["matched_routes"] == ["/users/[id]"]
