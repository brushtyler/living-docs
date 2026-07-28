from __future__ import annotations

import json
from pathlib import Path

import pytest

from living_docs.cli import main
from living_docs.integrations import AgentInstaller, SUPPORTED_AGENTS
from living_docs.mcp_server import build_parser as build_mcp_parser


def _installer(project: Path, home: Path) -> AgentInstaller:
    return AgentInstaller(project, home=home)


def test_cli_version_does_not_require_a_project_config(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])
    assert exit_info.value.code == 0
    assert capsys.readouterr().out == "living-docs 2.0.0\n"


def test_mcp_version_does_not_start_the_server(capsys):
    with pytest.raises(SystemExit) as exit_info:
        build_mcp_parser().parse_args(["--version"])
    assert exit_info.value.code == 0
    assert capsys.readouterr().out == "living-docs-mcp 2.0.0\n"


def test_cli_init_does_not_require_living_docs_config(
    tmp_path: Path,
    capsys,
):
    project = tmp_path / "project"
    project.mkdir()

    code = main(
        [
            "--project-root",
            str(project),
            "--json",
            "init",
            "--agent",
            "cursor",
            "--dry-run",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert code == 0
    assert payload["ok"] is True
    assert payload["data"]["agent"] == "cursor"
    assert not (project / ".cursor").exists()


def test_cursor_project_install_merges_config_and_is_idempotent(
    tmp_path: Path,
):
    project = tmp_path / "project"
    home = tmp_path / "home"
    config = project / ".cursor/mcp.json"
    config.parent.mkdir(parents=True)
    config.write_text(
        json.dumps({"theme": "dark", "mcpServers": {"existing": {"url": "x"}}}),
        encoding="utf-8",
    )

    first = _installer(project, home).install("cursor")
    second = _installer(project, home).install("cursor")

    assert first.ok
    assert first.data["scope"] == "project"
    assert (project / ".cursor/skills/living-docs/SKILL.md").is_file()
    merged = json.loads(config.read_text(encoding="utf-8"))
    assert merged["theme"] == "dark"
    assert merged["mcpServers"]["existing"] == {"url": "x"}
    assert merged["mcpServers"]["living-docs"]["command"] == "living-docs-mcp"
    assert second.data["changed"] == 0
    assert {item["action"] for item in second.data["files"]} == {"unchanged"}


def test_codex_global_install_uses_skill_and_managed_mcp_block(
    tmp_path: Path,
):
    project = tmp_path / "project"
    home = tmp_path / "home"
    config = home / ".codex/config.toml"
    config.parent.mkdir(parents=True)
    config.write_text('model = "example"\n', encoding="utf-8")

    result = _installer(project, home).install("codex", global_scope=True)
    repeated = _installer(project, home).install("codex", global_scope=True)

    assert result.ok
    assert (home / ".codex/skills/living-docs/SKILL.md").is_file()
    assert not (home / ".codex/AGENTS.md").exists()
    contents = config.read_text(encoding="utf-8")
    assert 'model = "example"' in contents
    assert contents.count("[mcp_servers.living-docs]") == 1
    assert repeated.data["changed"] == 0


def test_antigravity_installs_a_complete_plugin_bundle(tmp_path: Path):
    project = tmp_path / "project"
    home = tmp_path / "home"

    result = _installer(project, home).install("antigravity")
    plugin = project / ".agents/plugins/living-docs"

    assert result.ok
    assert (plugin / "plugin.json").is_file()
    assert (plugin / "mcp_config.json").is_file()
    assert (plugin / "skills/living-docs/SKILL.md").is_file()
    mcp = json.loads((plugin / "mcp_config.json").read_text(encoding="utf-8"))
    assert mcp["mcpServers"]["living-docs"]["command"] == "living-docs-mcp"


def test_dry_run_reports_targets_without_writing(tmp_path: Path):
    project = tmp_path / "project"
    home = tmp_path / "home"

    result = _installer(project, home).install("gemini", dry_run=True)

    assert result.ok
    assert result.data["dry_run"] is True
    assert {item["action"] for item in result.data["files"]} == {"would_create"}
    assert not (project / ".gemini").exists()


def test_invalid_existing_json_is_not_overwritten(tmp_path: Path):
    project = tmp_path / "project"
    home = tmp_path / "home"
    config = project / ".cursor/mcp.json"
    config.parent.mkdir(parents=True)
    config.write_text("{broken", encoding="utf-8")

    with pytest.raises(Exception) as error:
        _installer(project, home).install("cursor")

    assert "cannot safely merge invalid JSON" in str(error.value)
    assert config.read_text(encoding="utf-8") == "{broken"


def test_pi_installs_cli_fallback_skill(tmp_path: Path):
    project = tmp_path / "project"
    result = _installer(project, tmp_path / "home").install("pi")

    assert result.ok
    assert (project / ".pi/skills/living-docs/SKILL.md").is_file()
    assert [warning.code for warning in result.warnings] == ["MCP_NOT_CONFIGURED"]


def test_hermes_merges_existing_yaml_and_uses_user_scope(tmp_path: Path):
    project = tmp_path / "project"
    home = tmp_path / "home"
    config = home / ".hermes/config.yaml"
    config.parent.mkdir(parents=True)
    config.write_text(
        'model: "example"\nmcp_servers:\n  existing:\n    command: "other"\n',
        encoding="utf-8",
    )

    first = _installer(project, home).install("hermes")
    second = _installer(project, home).install("hermes")

    assert first.ok
    assert first.data["scope"] == "global"
    assert first.warnings[0].code == "GLOBAL_SCOPE_REQUIRED"
    contents = config.read_text(encoding="utf-8")
    assert 'model: "example"' in contents
    assert contents.count("  living-docs:") == 1
    assert second.data["changed"] == 0


def test_kilo_uses_native_command_array_schema(tmp_path: Path):
    project = tmp_path / "project"
    result = _installer(project, tmp_path / "home").install("kilocode")
    config = json.loads(
        (project / ".kilo/kilo.json").read_text(encoding="utf-8")
    )

    assert result.ok
    assert config["mcp"]["living-docs"] == {
        "type": "local",
        "command": ["living-docs-mcp", "--project-root", "."],
        "enabled": True,
    }


@pytest.mark.parametrize("agent", SUPPORTED_AGENTS)
def test_every_supported_agent_can_be_previewed(agent: str, tmp_path: Path):
    project = tmp_path / "project"
    home = tmp_path / "home"

    result = _installer(project, home).install(agent, dry_run=True)

    assert result.ok
    assert result.data["agent"] == agent
    assert result.data["files"]
