"""Seven-tool FastMCP stdio server."""

from __future__ import annotations

import asyncio
import argparse
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Callable

from mcp.server.fastmcp import Context, FastMCP
from mcp.types import ToolAnnotations
from pydantic import ValidationError

from . import __version__
from .browser import CancellationToken
from .errors import CONFIG_INVALID, INVALID_RECIPE, LivingDocsError
from .models import ErrorDetail, OperationResult, Recipe
from .runtime import LivingDocsRuntime

LOGGER = logging.getLogger(__name__)

READ_ONLY_LOCAL = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)
READ_ONLY_OPEN = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=True,
)
MUTATING_OPEN = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=True,
)


def _unexpected(exc: Exception) -> OperationResult:
    LOGGER.error("unexpected Living Docs tool failure: %s", type(exc).__name__)
    return OperationResult(
        ok=False,
        summary="Living Docs operation failed",
        errors=[
            ErrorDetail(
                code=CONFIG_INVALID,
                message="Unexpected internal failure",
            )
        ],
    )


def create_server(
    runtime: LivingDocsRuntime,
    *,
    max_workers: int = 4,
) -> FastMCP:
    server = FastMCP(
        name="living-docs",
        instructions=(
            "Validate, plan, and update Markdown snapshot recipes within the bound "
            "project root. All tool paths must be project-relative."
        ),
        log_level="WARNING",
    )
    executor = ThreadPoolExecutor(
        max_workers=max(1, min(max_workers, 8)),
        thread_name_prefix="living-docs-mcp",
    )

    async def run_blocking(
        operation: Callable[[CancellationToken, Callable | None], OperationResult],
        ctx: Context | None = None,
        *,
        with_progress: bool = False,
    ) -> OperationResult:
        token = CancellationToken()
        loop = asyncio.get_running_loop()

        def progress(done: int, total: int, message: str) -> None:
            if ctx is None:
                return
            asyncio.run_coroutine_threadsafe(
                ctx.report_progress(done, total, message),
                loop,
            )

        future = loop.run_in_executor(
            executor,
            partial(operation, token, progress if with_progress else None),
        )
        try:
            return await asyncio.shield(future)
        except asyncio.CancelledError:
            token.cancel()
            try:
                await asyncio.wait_for(asyncio.shield(future), timeout=15)
            except Exception:
                LOGGER.warning("browser worker did not stop within cancellation grace period")
            raise
        except LivingDocsError as exc:
            return runtime.failure(exc)
        except ValidationError as exc:
            return OperationResult(
                ok=False,
                summary="Invalid recipe input",
                errors=[
                    ErrorDetail(
                        code=INVALID_RECIPE,
                        message="Invalid recipe input",
                        details={"validation": exc.errors(include_input=False)},
                    )
                ],
            )
        except Exception as exc:
            return _unexpected(exc)

    @server.tool(
        name="doctor",
        annotations=READ_ONLY_OPEN,
        structured_output=True,
    )
    async def doctor() -> OperationResult:
        """Report Python, Chrome, driver, config, output, and base-URL readiness."""
        return await run_blocking(lambda _token, _progress: runtime.doctor())

    @server.tool(
        name="check_staleness",
        annotations=READ_ONLY_LOCAL,
        structured_output=True,
    )
    async def check_staleness() -> OperationResult:
        """Return stale Markdown documents and the code files changed since each."""
        return await run_blocking(lambda _token, _progress: runtime.check_staleness())

    @server.tool(
        name="resolve_route",
        annotations=READ_ONLY_LOCAL,
        structured_output=True,
    )
    async def resolve_route(file: str) -> OperationResult:
        """Resolve a project-relative UI source file to candidate routes and URLs."""
        return await run_blocking(
            lambda _token, _progress: runtime.resolve_route(file)
        )

    @server.tool(
        name="validate_recipes",
        annotations=READ_ONLY_LOCAL,
        structured_output=True,
    )
    async def validate_recipes(files: list[str] | None = None) -> OperationResult:
        """Validate selected project-relative Markdown files, or every recipe."""
        return await run_blocking(
            lambda _token, _progress: runtime.validate_recipes(files)
        )

    @server.tool(
        name="capture",
        annotations=MUTATING_OPEN,
        structured_output=True,
    )
    async def capture(recipe: Recipe, ctx: Context) -> OperationResult:
        """Execute one validated recipe and write its declared image artifacts."""
        return await run_blocking(
            lambda token, _progress: runtime.capture(recipe, token=token),
            ctx,
        )

    @server.tool(
        name="plan_snapshot_sync",
        annotations=READ_ONLY_LOCAL,
        structured_output=True,
    )
    async def plan_snapshot_sync(
        only_files: list[str] | None = None,
        only_images: list[str] | None = None,
    ) -> OperationResult:
        """Report selected recipes without starting Chrome or writing files."""
        return await run_blocking(
            lambda _token, _progress: runtime.plan_snapshot_sync(
                only_files,
                only_images,
            )
        )

    @server.tool(
        name="apply_snapshot_sync",
        annotations=MUTATING_OPEN,
        structured_output=True,
    )
    async def apply_snapshot_sync(
        ctx: Context,
        only_files: list[str] | None = None,
        only_images: list[str] | None = None,
        workers: int | None = None,
        review: bool = False,
    ) -> OperationResult:
        """Execute a sync; review mode writes candidates/diffs without replacing targets."""
        return await run_blocking(
            lambda token, progress: runtime.apply_snapshot_sync(
                only_files,
                only_images,
                workers,
                review,
                token=token,
                progress=progress,
            ),
            ctx,
            with_progress=True,
        )

    # Keep the bounded executor reachable for test teardown and process cleanup.
    setattr(server, "_living_docs_executor", executor)
    return server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="living-docs-mcp",
        description="Living Docs stdio MCP server",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--config", help="Configuration path relative to project root")
    parser.add_argument(
        "--log-level",
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        stream=sys.stderr,
        format="%(levelname)s %(name)s: %(message)s",
    )
    try:
        runtime = LivingDocsRuntime(args.project_root, args.config)
    except Exception as exc:
        LOGGER.error("cannot start Living Docs MCP server: %s", exc)
        return 2
    server = create_server(runtime, max_workers=runtime.config.workers)
    try:
        server.run(transport="stdio")
    finally:
        server._living_docs_executor.shutdown(wait=True, cancel_futures=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
