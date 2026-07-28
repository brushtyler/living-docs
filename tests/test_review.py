from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from living_docs.review import ReviewWorkspace
from living_docs.runtime import LivingDocsRuntime

from conftest import write_recipe


class ScreenshotDriver:
    current_url = "http://localhost:5050/"
    capabilities = {
        "browserName": "chrome",
        "browserVersion": "123.0",
        "chrome": {"chromedriverVersion": "123.0 test"},
    }

    def __init__(self) -> None:
        self.quit_called = False

    def get(self, url: str) -> None:
        self.current_url = url

    def save_screenshot(self, filename: str) -> bool:
        Image.new("RGB", (24, 16), "blue").save(filename)
        return True

    def delete_all_cookies(self) -> None:
        return None

    def quit(self) -> None:
        self.quit_called = True


def test_review_workspace_creates_candidate_and_visual_diff(project: Path):
    target = project / "docs/assets/page.png"
    target.parent.mkdir(parents=True)
    Image.new("RGB", (24, 16), "red").save(target)
    workspace = ReviewWorkspace(project, LivingDocsRuntime(project).boundary)
    candidate = workspace.candidate_for(target)
    candidate.parent.mkdir(parents=True)
    Image.new("RGB", (24, 16), "blue").save(candidate)

    review, artifacts = workspace.compare(target, candidate)

    assert review.status == "changed"
    assert review.target_path == "docs/assets/page.png"
    assert review.diff_path is not None
    assert (project / review.diff_path).is_file()
    assert len(artifacts) == 2
    with Image.open(target) as current:
        assert current.getpixel((0, 0)) == (255, 0, 0)

    Image.new("RGB", (24, 16), "red").save(candidate)
    unchanged, unchanged_artifacts = workspace.compare(target, candidate)
    assert unchanged.status == "unchanged"
    assert unchanged.diff_path is None
    assert len(unchanged_artifacts) == 1
    assert not (project / artifacts[1].path).exists()

    target.unlink()
    new, _ = workspace.compare(target, candidate)
    assert new.status == "new"


def test_apply_review_does_not_replace_target_and_writes_provenance(
    project: Path,
    monkeypatch,
):
    write_recipe(
        project,
        recipe="""
{
  "prerequisites": [],
  "tasks": [
    {"action": "goto", "url": "/?token=not-returned#private"},
    {"action": "snapshot_page", "filename": "assets/page.png"}
  ]
}
""".strip(),
    )
    target = project / "docs/assets/page.png"
    target.parent.mkdir(parents=True)
    Image.new("RGB", (24, 16), "red").save(target)
    runtime = LivingDocsRuntime(project)
    driver = ScreenshotDriver()
    monkeypatch.setattr(runtime.snapshots.runner.factory, "create", lambda: driver)
    monkeypatch.setattr(
        runtime.snapshots.runner,
        "_network_idle",
        lambda *_args, **_kwargs: None,
    )

    result = runtime.apply_snapshot_sync(review=True)

    assert result.ok
    assert result.data["review_mode"] is True
    assert result.data["replaced_targets"] is False
    outcome = result.data["outcomes"][0]
    assert outcome["reviews"][0]["status"] == "changed"
    assert outcome["provenance"]["browser_version"] == "123.0"
    assert outcome["provenance"]["final_url"] == "http://localhost:5050/"
    with Image.open(target) as current:
        assert current.getpixel((0, 0)) == (255, 0, 0)
    manifest = project / ".living-docs/review/provenance.json"
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["captures"]["docs/assets/page.png"]["owner"] == "docs/guide.md"
    assert driver.quit_called


def test_review_reports_invalid_existing_image_as_structured_failure(
    project: Path,
    monkeypatch,
):
    write_recipe(project)
    target = project / "docs/assets/page.png"
    target.parent.mkdir(parents=True)
    target.write_text("not an image", encoding="utf-8")
    runtime = LivingDocsRuntime(project)
    monkeypatch.setattr(
        runtime.snapshots.runner.factory,
        "create",
        ScreenshotDriver,
    )
    monkeypatch.setattr(
        runtime.snapshots.runner,
        "_network_idle",
        lambda *_args, **_kwargs: None,
    )

    result = runtime.apply_snapshot_sync(review=True)

    assert not result.ok
    assert result.errors[0].code == "CAPTURE_FAILED"
    assert target.read_text(encoding="utf-8") == "not an image"
