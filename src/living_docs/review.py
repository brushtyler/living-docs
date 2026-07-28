"""Non-destructive screenshot review artifacts and provenance manifests."""

from __future__ import annotations

import hashlib
import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageOps

from .errors import CAPTURE_FAILED, LivingDocsError
from .models import Artifact, ReviewDetail, SyncOutcome
from .security import ProjectBoundary, project_relative


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ReviewWorkspace:
    """Maps target screenshots to safe candidates and creates visual comparisons."""

    def __init__(self, project_root: Path, boundary: ProjectBoundary) -> None:
        self.project_root = project_root
        self.boundary = boundary
        self.root = boundary.output_root / ".living-docs" / "review"

    def _relative_target(self, target: Path) -> Path:
        return target.resolve().relative_to(self.boundary.output_root)

    def candidate_for(self, target: Path) -> Path:
        return self.root / "candidates" / self._relative_target(target)

    def diff_for(self, target: Path) -> Path:
        relative = self._relative_target(target)
        return self.root / "diffs" / relative.with_suffix(".diff.png")

    @staticmethod
    def _panel(image: Image.Image, size: tuple[int, int]) -> Image.Image:
        panel = Image.new("RGB", size, "white")
        rendered = ImageOps.contain(image.convert("RGB"), size)
        panel.paste(
            rendered,
            ((size[0] - rendered.width) // 2, (size[1] - rendered.height) // 2),
        )
        return panel

    def _write_diff(self, current: Path, candidate: Path, destination: Path) -> None:
        with Image.open(current) as before_image, Image.open(candidate) as after_image:
            width = min(max(before_image.width, after_image.width), 900)
            height = min(max(before_image.height, after_image.height), 900)
            size = (width, height)
            before = self._panel(before_image, size)
            after = self._panel(after_image, size)
            delta = ImageChops.difference(before, after).convert("L")
            delta = ImageOps.autocontrast(delta)
            highlighted = ImageOps.colorize(delta, black="#111827", white="#ff2d87")

            title_height = 36
            sheet = Image.new("RGB", (width * 3, height + title_height), "#111827")
            draw = ImageDraw.Draw(sheet)
            for index, label in enumerate(("CURRENT", "CANDIDATE", "DIFFERENCE")):
                draw.text((index * width + 12, 11), label, fill="white")
            sheet.paste(before, (0, title_height))
            sheet.paste(after, (width, title_height))
            sheet.paste(highlighted, (width * 2, title_height))
            destination.parent.mkdir(parents=True, exist_ok=True)
            sheet.save(destination, format="PNG")

    def compare(self, target: Path, candidate: Path) -> tuple[ReviewDetail, list[Artifact]]:
        try:
            candidate_hash = sha256_file(candidate)
            current_hash = sha256_file(target) if target.is_file() else None
            status = (
                "new"
                if current_hash is None
                else "unchanged"
                if current_hash == candidate_hash
                else "changed"
            )
            diff_path: Path | None = None
            artifacts = [self._artifact(candidate)]
            if status == "changed":
                diff_path = self.diff_for(target)
                self._write_diff(target, candidate, diff_path)
                artifacts.append(self._artifact(diff_path))
            else:
                stale_diff = self.diff_for(target)
                if stale_diff.is_file():
                    stale_diff.unlink()
        except (OSError, ValueError) as exc:
            raise LivingDocsError(
                CAPTURE_FAILED,
                "could not create screenshot review for "
                f"{project_relative(target, self.project_root)}",
            ) from exc
        return (
            ReviewDetail(
                status=status,
                target_path=project_relative(target, self.project_root),
                candidate_path=project_relative(candidate, self.project_root),
                diff_path=(
                    project_relative(diff_path, self.project_root)
                    if diff_path is not None
                    else None
                ),
                current_sha256=current_hash,
                candidate_sha256=candidate_hash,
            ),
            artifacts,
        )

    def _artifact(self, path: Path) -> Artifact:
        with Image.open(path) as image:
            width, height = image.size
        return Artifact(
            path=project_relative(path, self.project_root),
            kind="image",
            media_type="image/png",
            width=width,
            height=height,
        )


def write_provenance_manifest(
    project_root: Path,
    boundary: ProjectBoundary,
    outcomes: list[SyncOutcome],
    *,
    review: bool,
) -> Artifact | None:
    successful = [item for item in outcomes if item.ok and item.provenance is not None]
    if not successful:
        return None
    manifest = boundary.output_root / ".living-docs"
    if review:
        manifest = manifest / "review"
    manifest = manifest / "provenance.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)

    existing: dict[str, object] = {}
    if manifest.is_file():
        try:
            loaded = json.loads(manifest.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                existing = loaded
        except (OSError, json.JSONDecodeError):
            existing = {}
    captures = existing.get("captures")
    if not isinstance(captures, dict):
        captures = {}
    for outcome in successful:
        entry = outcome.provenance.model_dump(mode="json")
        entry["recipe_id"] = outcome.recipe_id
        entry["owner"] = outcome.source_file
        entry["review"] = [item.model_dump(mode="json") for item in outcome.reviews]
        captures[outcome.target_path] = entry

    payload = {
        "schema_version": 1,
        "updated_at": datetime.now(UTC).isoformat(),
        "captures": captures,
    }
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=manifest.parent,
            prefix=".provenance-",
            suffix=".tmp",
            delete=False,
        ) as stream:
            json.dump(payload, stream, indent=2, ensure_ascii=False, sort_keys=True)
            stream.write("\n")
            temporary = Path(stream.name)
        temporary.replace(manifest)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return Artifact(
        path=project_relative(manifest, project_root),
        kind="metadata",
        media_type="application/json",
    )
