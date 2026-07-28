"""Composition root used by both public front ends."""

from __future__ import annotations

from pathlib import Path

from .browser import BrowserRunner, CancellationToken
from .config import load_config
from .doctor import diagnostics
from .errors import LivingDocsError
from .git_analysis import GitAnalyzer
from .models import ErrorDetail, OperationResult, Recipe
from .routes import resolve_route
from .security import ProjectBoundary
from .sync import SnapshotService


class LivingDocsRuntime:
    def __init__(
        self,
        project_root: str | Path = ".",
        config_path: str | Path | None = None,
    ) -> None:
        self.project_root = Path(project_root).expanduser().resolve()
        if not self.project_root.is_dir():
            raise ValueError(f"project root is not a directory: {project_root}")
        self.config, self.config_path, self.warnings = load_config(
            self.project_root,
            config_path,
        )
        self.boundary = ProjectBoundary(
            self.project_root,
            self.config.security.output_root,
        )
        self.snapshots = SnapshotService(
            self.project_root,
            self.config,
            self.boundary,
            self.warnings,
        )

    @staticmethod
    def failure(exc: LivingDocsError) -> OperationResult:
        return OperationResult(
            ok=False,
            summary=exc.message,
            errors=[
                ErrorDetail(
                    code=exc.code,
                    message=exc.message,
                    details=exc.details,
                )
            ],
        )

    def doctor(self) -> OperationResult:
        data = diagnostics(
            self.project_root,
            self.config_path,
            self.config,
            self.boundary.output_root,
        )
        essential = (
            data["python"]["supported"]
            and data["configuration"]["ready"]
            and data["output_directory"]["ready"]
            and data["browser"]["ready"]
            and data["driver"]["ready"]
            and data["base_url"]["ready"]
        )
        return OperationResult(
            ok=bool(essential),
            summary="Living Docs is ready" if essential else "Living Docs has readiness issues",
            data=data,
            warnings=self.warnings,
        )

    def check_staleness(self) -> OperationResult:
        stale = GitAnalyzer(self.project_root).staleness()
        changed = sorted(
            {
                path
                for document in stale
                for path in document["changed_files"]
            }
        )
        return OperationResult(
            ok=True,
            summary=f"Found {len(stale)} stale document(s)",
            data={
                "stale_documents": stale,
                "changed_files": changed,
                "snapshot_impact": self.snapshots.impacts(changed),
            },
            warnings=self.warnings,
        )

    def resolve_route(self, file: str) -> OperationResult:
        path = self.boundary.input_path(file, must_exist=False)
        relative = path.relative_to(self.project_root).as_posix()
        candidates = resolve_route(relative, self.config)
        return OperationResult(
            ok=True,
            summary=f"Resolved {len(candidates)} route candidate(s)",
            data={"file": relative, "candidates": candidates},
            warnings=self.warnings,
        )

    def validate_recipes(self, files: list[str] | None = None) -> OperationResult:
        return self.snapshots.validate(files)

    def plan_snapshot_sync(
        self,
        only_files: list[str] | None = None,
        only_images: list[str] | None = None,
    ) -> OperationResult:
        return self.snapshots.plan(only_files, only_images)

    def capture(
        self,
        recipe: Recipe,
        *,
        token: CancellationToken | None = None,
    ) -> OperationResult:
        captured = BrowserRunner(
            self.project_root,
            self.config,
            self.boundary,
        ).capture(recipe, token=token)
        return OperationResult(
            ok=True,
            summary=f"Capture produced {len(captured.artifacts)} artifact(s)",
            data={
                "metadata": [
                    item.model_dump(mode="json")
                    for item in captured.metadata
                ],
                "provenance": captured.provenance.model_dump(mode="json"),
            },
            artifacts=captured.artifacts,
            warnings=self.warnings,
        )

    def apply_snapshot_sync(
        self,
        only_files: list[str] | None = None,
        only_images: list[str] | None = None,
        workers: int | None = None,
        review: bool = False,
        *,
        token: CancellationToken | None = None,
        progress=None,
    ) -> OperationResult:
        return self.snapshots.apply(
            only_files,
            only_images,
            workers,
            review,
            token=token,
            progress=progress,
        )
