"""Recipe validation, sync planning, and bounded parallel application."""

from __future__ import annotations

import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlsplit

from .browser import BrowserRunner, CancellationToken, ProgressCallback
from .errors import DUPLICATE_OUTPUT, INVALID_RECIPE, LivingDocsError
from .git_analysis import GitAnalyzer
from .models import (
    ErrorDetail,
    OperationResult,
    RecipeRecord,
    SyncPlanItem,
    WarningDetail,
)
from .recipes import scan_project
from .review import write_provenance_manifest
from .routes import resolve_route
from .security import ProjectBoundary, project_relative


def _route_pattern_matches(pattern: str, route: str) -> bool:
    pattern_parts = [part for part in pattern.strip("/").split("/") if part]
    route_parts = [part for part in route.strip("/").split("/") if part]
    expression: list[str] = []
    for part in pattern_parts:
        if part.startswith("[[...") and part.endswith("]]"):
            expression.append("(?:.+)?")
        elif part.startswith("[...") and part.endswith("]"):
            expression.append(".+")
        elif part.startswith("[") and part.endswith("]"):
            expression.append("[^/]+")
        else:
            expression.append(re.escape(part))
    return bool(re.fullmatch("/".join(expression), "/".join(route_parts)))


class SnapshotService:
    def __init__(
        self,
        project_root: Path,
        config,
        boundary: ProjectBoundary,
        config_warnings: list[WarningDetail] | None = None,
    ) -> None:
        self.project_root = project_root
        self.config = config
        self.boundary = boundary
        self.runner = BrowserRunner(project_root, config, boundary)
        self.config_warnings = config_warnings or []

    @staticmethod
    def _matches(value: str, filters: list[str] | None) -> bool:
        if not filters:
            return True
        normalized = value.replace("\\", "/")
        name = Path(normalized).name
        choices = {item.replace("\\", "/") for item in filters}
        return normalized in choices or name in choices

    def _selected_files(self, only_files: list[str] | None) -> list[Path] | None:
        if not only_files:
            return None
        selected: list[Path] = []
        for value in only_files:
            selected.append(self.boundary.input_path(value))
        return selected

    def _scan(
        self,
        only_files: list[str] | None = None,
        only_images: list[str] | None = None,
    ) -> tuple[list[RecipeRecord], list[ErrorDetail]]:
        records, errors = scan_project(
            self.project_root,
            self._selected_files(only_files),
        )
        records = [
            record
            for record in records
            if self._matches(record.image_path, only_images)
        ]
        owners: dict[str, list[RecipeRecord]] = defaultdict(list)
        for record in records:
            try:
                owners[self._target_path(record)].append(record)
            except LivingDocsError:
                # Boundary failures are reported with their source location later.
                continue
        for target, owned_records in owners.items():
            if len(owned_records) < 2:
                continue
            owner_names = sorted({item.source_file for item in owned_records})
            errors.append(
                ErrorDetail(
                    code=DUPLICATE_OUTPUT,
                    message=f"multiple snapshot recipes write {target}",
                    path=owner_names[0],
                    details={
                        "target_path": target,
                        "owners": owner_names,
                        "recipe_ids": [item.recipe_id for item in owned_records],
                    },
                )
            )
        return records, errors

    def _target_path(self, record: RecipeRecord) -> str:
        source_directory = (self.project_root / record.source_file).parent
        target = self.boundary.output_path(
            record.image_path,
            relative_to=source_directory,
        )
        return project_relative(target, self.project_root)

    def _prepare_record(self, record: RecipeRecord):
        source_directory = (self.project_root / record.source_file).parent
        target = self.boundary.output_path(
            record.image_path,
            relative_to=source_directory,
        )
        tasks = self.runner.prepare_recipe(record.recipe, source_directory)
        snapshot_targets = {
            self.boundary.output_path(task.filename, relative_to=source_directory)
            for task in tasks
            if task.action in {"snapshot", "snapshot_page", "snapshot_element"}
        }
        if target not in snapshot_targets:
            raise LivingDocsError(
                INVALID_RECIPE,
                "the recipe must capture the image it immediately follows",
                {
                    "image_path": record.image_path,
                    "target_path": project_relative(target, self.project_root),
                },
            )
        return tasks

    def validate(
        self,
        only_files: list[str] | None = None,
    ) -> OperationResult:
        records, errors = self._scan(only_files)
        for record in records:
            try:
                self._prepare_record(record)
            except LivingDocsError as exc:
                errors.append(
                    ErrorDetail(
                        code=exc.code,
                        message=exc.message,
                        path=record.source_file,
                        details={
                            "line": record.location.line,
                            "column": record.location.column,
                            **(exc.details or {}),
                        },
                    )
                )
        ok = not errors
        return OperationResult(
            ok=ok,
            summary=(
                f"Validated {len(records)} snapshot recipe(s)"
                if ok
                else f"Found {len(errors)} recipe validation error(s)"
            ),
            data={
                "recipe_count": len(records),
                "recipes": [record.model_dump(mode="json") for record in records],
            },
            warnings=self.config_warnings,
            errors=errors,
        )

    def plan(
        self,
        only_files: list[str] | None = None,
        only_images: list[str] | None = None,
    ) -> OperationResult:
        records, errors = self._scan(only_files, only_images)
        items: list[SyncPlanItem] = []
        for record in records:
            try:
                tasks = self._prepare_record(record)
                items.append(
                    SyncPlanItem(
                        recipe_id=record.recipe_id,
                        owner=record.source_file,
                        source_file=record.source_file,
                        image_path=record.image_path,
                        target_path=self._target_path(record),
                        action_count=len(tasks),
                        prerequisites=record.recipe.prerequisites,
                    )
                )
            except LivingDocsError as exc:
                errors.append(
                    ErrorDetail(
                        code=exc.code,
                        message=exc.message,
                        path=record.source_file,
                        details=exc.details,
                    )
                )
        return OperationResult(
            ok=not errors,
            summary=(
                f"Planned {len(items)} snapshot(s)"
                if not errors
                else f"Sync plan has {len(errors)} error(s)"
            ),
            data={
                "count": len(items),
                "items": [item.model_dump(mode="json") for item in items],
                "starts_browser": False,
                "writes_files": False,
            },
            warnings=self.config_warnings,
            errors=errors,
        )

    def apply(
        self,
        only_files: list[str] | None = None,
        only_images: list[str] | None = None,
        workers: int | None = None,
        review: bool = False,
        *,
        token: CancellationToken | None = None,
        progress: ProgressCallback | None = None,
    ) -> OperationResult:
        token = token or CancellationToken()
        records, scan_errors = self._scan(only_files, only_images)
        if scan_errors:
            return OperationResult(
                ok=False,
                summary=f"Sync rejected with {len(scan_errors)} recipe error(s)",
                warnings=self.config_warnings,
                errors=scan_errors,
            )
        if not records:
            return OperationResult(
                ok=True,
                summary="No snapshot recipes matched",
                data={"count": 0, "outcomes": []},
                warnings=self.config_warnings,
            )

        validation_errors: list[ErrorDetail] = []
        for record in records:
            try:
                self._prepare_record(record)
            except LivingDocsError as exc:
                validation_errors.append(
                    ErrorDetail(
                        code=exc.code,
                        message=exc.message,
                        path=record.source_file,
                        details=exc.details,
                    )
                )
        if validation_errors:
            return OperationResult(
                ok=False,
                summary=f"Sync rejected with {len(validation_errors)} validation error(s)",
                warnings=self.config_warnings,
                errors=validation_errors,
            )

        grouped: dict[str, list[RecipeRecord]] = defaultdict(list)
        for record in records:
            grouped[record.source_file].append(record)
        units = list(grouped.values())
        worker_count = max(1, min(workers or self.config.workers, 16, len(units)))
        outcomes = []
        completed_offset = 0
        source_revision = self._source_revision()

        def execute(unit: list[RecipeRecord], offset: int):
            return self.runner.capture_records(
                unit,
                token=token,
                progress=progress,
                progress_offset=offset,
                progress_total=len(records),
                review=review,
                source_revision=source_revision,
            )

        if worker_count == 1:
            for unit in units:
                outcomes.extend(execute(unit, completed_offset))
                completed_offset += len(unit)
        else:
            with ThreadPoolExecutor(
                max_workers=worker_count,
                thread_name_prefix="living-docs-browser",
            ) as pool:
                futures = {}
                for unit in units:
                    futures[pool.submit(execute, unit, completed_offset)] = unit
                    completed_offset += len(unit)
                for future in as_completed(futures):
                    outcomes.extend(future.result())

        failures = [outcome for outcome in outcomes if not outcome.ok]
        artifacts = [
            artifact
            for outcome in outcomes
            for artifact in outcome.artifacts
        ]
        errors = [
            outcome.error
            for outcome in failures
            if outcome.error is not None
        ]
        manifest = write_provenance_manifest(
            self.project_root,
            self.boundary,
            outcomes,
            review=review,
        )
        if manifest is not None:
            artifacts.append(manifest)
        return OperationResult(
            ok=not failures,
            summary=(
                (
                    f"Prepared {len(outcomes)} snapshot review(s)"
                    if review
                    else f"Updated {len(outcomes)} snapshot(s)"
                )
                if not failures
                else (
                    f"Prepared {len(outcomes) - len(failures)} of "
                    f"{len(outcomes)} snapshot review(s)"
                    if review
                    else f"Updated {len(outcomes) - len(failures)} of {len(outcomes)} snapshot(s)"
                )
            ),
            data={
                "count": len(outcomes),
                "failed": len(failures),
                "workers": worker_count,
                "review_mode": review,
                "replaced_targets": not review,
                "outcomes": [outcome.model_dump(mode="json") for outcome in outcomes],
            },
            artifacts=artifacts,
            warnings=self.config_warnings,
            errors=errors,
        )

    def _source_revision(self) -> str | None:
        try:
            return GitAnalyzer(self.project_root).head_revision()
        except LivingDocsError:
            return None

    def impacts(self, changed_files: list[str]) -> dict[str, object]:
        records, errors = self._scan()
        impact_errors = list(errors)
        recipes: list[tuple[RecipeRecord, list[str], str]] = []
        for record in records:
            try:
                target_path = self._target_path(record)
            except LivingDocsError as exc:
                impact_errors.append(
                    ErrorDetail(
                        code=exc.code,
                        message=exc.message,
                        path=record.source_file,
                        details=exc.details,
                    )
                )
                continue
            routes: list[str] = []
            tasks = []
            for prerequisite in record.recipe.prerequisites:
                tasks.extend(self.config.flows.get(prerequisite, []))
            tasks.extend(record.recipe.tasks)
            for task in tasks:
                if task.action != "goto" or "${ENV:" in task.url:
                    continue
                parsed = urlsplit(task.url)
                route = parsed.path or "/"
                routes.append(route)
            recipes.append((record, routes, target_path))

        impacts: list[dict[str, object]] = []
        for changed_file in sorted(set(changed_files)):
            candidates = resolve_route(changed_file, self.config)
            route_patterns = [str(item["route"]) for item in candidates]
            snapshots: list[dict[str, object]] = []
            for record, recipe_routes, target_path in recipes:
                matched = sorted(
                    {
                        pattern
                        for pattern in route_patterns
                        for recipe_route in recipe_routes
                        if _route_pattern_matches(pattern, recipe_route)
                    }
                )
                direct = changed_file == record.source_file
                if not matched and not direct:
                    continue
                snapshots.append(
                    {
                        "recipe_id": record.recipe_id,
                        "owner": record.source_file,
                        "image_path": record.image_path,
                        "target_path": target_path,
                        "reason": "owner_changed" if direct else "route_match",
                        "matched_routes": matched,
                    }
                )
            impacts.append(
                {
                    "changed_file": changed_file,
                    "route_candidates": candidates,
                    "snapshots": snapshots,
                }
            )
        return {
            "changed_files": len(impacts),
            "impacted_snapshots": sum(len(item["snapshots"]) for item in impacts),
            "impacts": impacts,
            "recipe_errors": [
                error.model_dump(mode="json")
                for error in impact_errors
            ],
        }
