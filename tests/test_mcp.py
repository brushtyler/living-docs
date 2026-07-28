from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from living_docs.mcp_server import create_server
from living_docs.runtime import LivingDocsRuntime

from conftest import write_recipe


@pytest.mark.asyncio
async def test_all_tools_have_structured_schemas_and_annotations(project: Path):
    write_recipe(project)
    runtime = LivingDocsRuntime(project)
    server = create_server(runtime)
    tools = await server.list_tools()
    assert [tool.name for tool in tools] == [
        "doctor",
        "check_staleness",
        "resolve_route",
        "validate_recipes",
        "capture",
        "plan_snapshot_sync",
        "apply_snapshot_sync",
    ]
    assert all(tool.outputSchema for tool in tools)
    by_name = {tool.name: tool for tool in tools}
    assert by_name["plan_snapshot_sync"].annotations.readOnlyHint is True
    assert by_name["capture"].annotations.readOnlyHint is False
    assert by_name["capture"].annotations.destructiveHint is False
    assert "review" in by_name["apply_snapshot_sync"].inputSchema["properties"]
    server._living_docs_executor.shutdown()


@pytest.mark.asyncio
async def test_stdio_initializes_without_protocol_noise(project: Path):
    write_recipe(project)
    repository = Path(__file__).parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [str(repository / ".deps"), str(repository / "src")]
    )
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[
            "-m",
            "living_docs.mcp_server",
            "--project-root",
            str(project),
        ],
        env=env,
    )
    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as session:
            initialized = await session.initialize()
            tools = await session.list_tools()
            result = await session.call_tool("plan_snapshot_sync", {})
            assert initialized.serverInfo.name == "living-docs"
            assert len(tools.tools) == 7
            assert result.isError is False
            assert result.structuredContent["ok"] is True
