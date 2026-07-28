"""Cross-platform Living Docs command-line interface."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Sequence

from pydantic import ValidationError

from . import __version__
from .errors import (
    BROWSER_UNAVAILABLE,
    CONFIG_INVALID,
    CONFIG_NOT_FOUND,
    DUPLICATE_OUTPUT,
    INPUT_PATH_DENIED,
    INVALID_RECIPE,
    INIT_FAILED,
    NAVIGATION_DENIED,
    OUTPUT_PATH_DENIED,
    LivingDocsError,
)
from .integrations import SUPPORTED_AGENTS, init_agent
from .models import ErrorDetail, OperationResult, Recipe
from .runtime import LivingDocsRuntime
from .security import substitute_env


def _common_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False, prog="living-docs")
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root (default: current directory)",
    )
    parser.add_argument("--config", help="Configuration path relative to project root")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit structured JSON")
    parser.add_argument(
        "--log-level",
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    return parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="living-docs",
        description="Validate and synchronize Living Docs snapshots",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    init = subparsers.add_parser(
        "init",
        help="Install the Living Docs skill and MCP registration for an AI agent",
    )
    agent = init.add_mutually_exclusive_group()
    agent.add_argument(
        "--agent",
        choices=(*SUPPORTED_AGENTS, "roo", "kilo", "factory"),
        dest="agent",
    )
    agent.add_argument("--gemini", action="store_const", const="gemini", dest="agent")
    agent.add_argument("--codex", action="store_const", const="codex", dest="agent")
    agent.add_argument(
        "--copilot",
        action="store_const",
        const="copilot",
        dest="agent",
    )
    init.set_defaults(agent="claude")
    init.add_argument(
        "-g",
        "--global",
        action="store_true",
        dest="global_scope",
        help="Install into the current user's home directory",
    )
    init.add_argument(
        "--dry-run",
        action="store_true",
        help="Show files that would change without writing them",
    )
    subparsers.add_parser("doctor", help="Report runtime readiness")
    subparsers.add_parser("check-staleness", help="Find stale Markdown documents")

    route = subparsers.add_parser("resolve-route", help="Resolve a UI source file")
    route.add_argument("file")

    validate = subparsers.add_parser("validate-recipes", help="Validate Markdown recipes")
    validate.add_argument("files", nargs="*")

    capture = subparsers.add_parser("capture", help="Execute one JSON recipe")
    capture.add_argument("--recipe", required=True, help="JSON object or @relative-file.json")

    plan = subparsers.add_parser("plan-sync", help="Plan a snapshot sync without side effects")
    plan.add_argument("--only-file", action="append", dest="only_files")
    plan.add_argument("--only-image", action="append", dest="only_images")

    apply = subparsers.add_parser("apply-sync", help="Execute a snapshot sync")
    apply.add_argument("--only-file", action="append", dest="only_files")
    apply.add_argument("--only-image", action="append", dest="only_images")
    apply.add_argument("--workers", type=int)
    apply.add_argument(
        "--review",
        action="store_true",
        help="Capture candidates and visual diffs without replacing target screenshots",
    )
    return parser


def _parse_recipe(value: str, runtime: LivingDocsRuntime) -> Recipe:
    try:
        if value.startswith("@"):
            path = runtime.boundary.input_path(value[1:])
            raw = json.loads(path.read_text(encoding="utf-8"))
        else:
            raw = json.loads(value)
        return Recipe.model_validate(substitute_env(raw))
    except (OSError, json.JSONDecodeError, ValidationError, ValueError) as exc:
        raise LivingDocsError(INVALID_RECIPE, f"invalid capture recipe: {exc}") from exc


def _execute(args: argparse.Namespace, runtime: LivingDocsRuntime) -> OperationResult:
    if args.command == "doctor":
        return runtime.doctor()
    if args.command == "check-staleness":
        return runtime.check_staleness()
    if args.command == "resolve-route":
        return runtime.resolve_route(args.file)
    if args.command == "validate-recipes":
        return runtime.validate_recipes(args.files or None)
    if args.command == "capture":
        return runtime.capture(_parse_recipe(args.recipe, runtime))
    if args.command == "plan-sync":
        return runtime.plan_snapshot_sync(args.only_files, args.only_images)
    if args.command == "apply-sync":
        return runtime.apply_snapshot_sync(
            args.only_files,
            args.only_images,
            args.workers,
            args.review,
        )
    raise AssertionError(f"unsupported command: {args.command}")


def _render_human(result: OperationResult) -> None:
    print(result.summary)
    for warning in result.warnings:
        location = f" ({warning.path})" if warning.path else ""
        print(f"warning [{warning.code}]{location}: {warning.message}", file=sys.stderr)
    for error in result.errors:
        location = f" ({error.path})" if error.path else ""
        print(f"error [{error.code}]{location}: {error.message}", file=sys.stderr)
    for artifact in result.artifacts:
        print(f"artifact: {artifact.path}")
    if result.data:
        print(json.dumps(result.data, indent=2, ensure_ascii=False))


def _exit_code(result: OperationResult) -> int:
    if result.ok:
        return 0
    codes = {error.code for error in result.errors}
    validation = {
        INVALID_RECIPE,
        DUPLICATE_OUTPUT,
        CONFIG_INVALID,
        CONFIG_NOT_FOUND,
        INPUT_PATH_DENIED,
        OUTPUT_PATH_DENIED,
        NAVIGATION_DENIED,
        INIT_FAILED,
    }
    if codes & validation:
        return 2
    if BROWSER_UNAVAILABLE in codes:
        return 3
    return 4


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(argv) if argv is not None else sys.argv[1:]
    common, remaining = _common_parser().parse_known_args(raw_args)
    args = build_parser().parse_args(remaining)
    for key, value in vars(common).items():
        setattr(args, key, value)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        stream=sys.stderr,
        format="%(levelname)s %(name)s: %(message)s",
    )

    try:
        if args.command == "init":
            result = init_agent(
                args.project_root,
                agent=args.agent,
                global_scope=args.global_scope,
                dry_run=args.dry_run,
            )
        else:
            runtime = LivingDocsRuntime(args.project_root, args.config)
            result = _execute(args, runtime)
    except LivingDocsError as exc:
        result = LivingDocsRuntime.failure(exc)
    except (OSError, ValueError, ValidationError) as exc:
        result = OperationResult(
            ok=False,
            summary=str(exc),
            errors=[ErrorDetail(code=CONFIG_INVALID, message=str(exc))],
        )

    if args.as_json:
        print(result.model_dump_json(indent=2))
    else:
        _render_human(result)
    return _exit_code(result)


if __name__ == "__main__":
    raise SystemExit(main())
