# Agent host integrations

Install `living-docs` first unless the template explicitly uses `uvx`. Every
host launches the same local stdio process:

```bash
uv tool install living-docs
living-docs --version
living-docs-mcp --project-root .
```

Then let Living Docs safely merge the shared Agent Skill and MCP registration:

```bash
living-docs init --agent cursor
living-docs init -g --codex
living-docs init --agent antigravity
```

Project scope is the default; `-g` selects user scope. `--dry-run` previews
the files without changing them. Templates remain under `integrations/` for
manual installation, but cloning this repository alone never activates them.

## Supported agents

| Agent | Selector | Project registration | User registration |
| --- | --- | --- | --- |
| Claude Code | default / `--agent claude` | `.mcp.json`, `.claude/skills/` | `~/.claude.json`, `~/.claude/skills/` |
| Gemini CLI | `--gemini` | `.gemini/settings.json`, `.gemini/skills/` | `~/.gemini/settings.json`, `~/.gemini/skills/` |
| Codex | `--codex` | `.codex/config.toml`, `.agents/skills/` | `~/.codex/config.toml`, `~/.codex/skills/` |
| GitHub Copilot | `--copilot` | `.github/mcp.json`, `.github/skills/` | `~/.copilot/mcp-config.json`, `~/.copilot/skills/` |
| Cursor | `--agent cursor` | `.cursor/mcp.json`, `.cursor/skills/` | `~/.cursor/mcp.json`, `~/.cursor/skills/` |
| Windsurf | `--agent windsurf` | workspace skill; CLI fallback | `~/.codeium/windsurf/mcp_config.json` and skill |
| Cline / Roo | `--agent cline` | `.cline/mcp.json`, `.cline/skills/` | `~/.cline/data/settings/cline_mcp_settings.json`, `~/.cline/skills/` |
| Kilo Code | `--agent kilocode` | `.kilo/kilo.json`, `.kilo/skills/` | `~/.config/kilo/kilo.json`, `~/.kilo/skills/` |
| Antigravity | `--agent antigravity` | `.agents/plugins/living-docs/` | `~/.gemini/config/plugins/living-docs/` |
| Kimi | `--agent kimi` | `.kimi-code/mcp.json`, `.kimi-code/skills/` | `~/.kimi-code/mcp.json`, `~/.kimi-code/skills/` |
| Pi | `--agent pi` | `.pi/skills/` CLI fallback | `~/.pi/agent/skills/` CLI fallback |
| Hermes | `--agent hermes` | user-scoped by Hermes | `~/.hermes/config.yaml`, `~/.hermes/skills/` |
| Factory Droid | `--agent droid` | `.factory/mcp.json`, `.factory/skills/` | `~/.factory/mcp.json`, `~/.factory/skills/` |

Pi intentionally has no built-in MCP client, so its skill uses the equivalent
`living-docs` CLI commands. Windsurf documents MCP configuration only at user
scope; use `-g --agent windsurf` for MCP plus skill. Hermes stores its native
skills and MCP configuration in user scope, so its selector reports that
scope even when `-g` is omitted.

## After registration

Restart the agent host or reload its MCP servers, open the configured project,
and confirm that Living Docs exposes seven tools. The first request can remain
entirely read-only:

> Use Living Docs to check whether this project is ready. Run diagnostic and
> read-only checks only. Explain anything I need to fix, and do not modify
> files or start a capture.

After readiness succeeds, continue with one of the copy-paste
[prompt examples](README.md#prompt-examples-for-ai-agents). Capture and apply
requests should state whether the agent may write review artifacts or replace
existing screenshots.

## Codex

```bash
living-docs init --codex
```

The installer writes a bounded managed block in `.codex/config.toml` and the
workflow under `.agents/skills/living-docs`. Global installation uses the
corresponding `~/.codex/` locations. It does not edit `AGENTS.md`: the native
skill is loaded only when Living Docs work is relevant.

## Claude Code

```bash
living-docs init
```

An equivalent repository `.mcp.json` template is under
`integrations/templates/claude-code/`.

## Cursor

Run `living-docs init --agent cursor`, then reload MCP servers from Cursor
settings.

## Gemini CLI

Run `living-docs init --gemini`. The extension template remains available for
teams that prefer a Gemini extension. It uses `${extensionPath}` as its
working directory, `${workspacePath}` as the bound project, and stdio:

```bash
gemini extensions install --path integrations/gemini-cli
```

Restart Gemini CLI after installation.

## GitHub Copilot

Run `living-docs init --copilot`. Review repository MCP configuration before
enabling it; workspace servers require a trusted folder and tool invocations
remain permissioned.

## Google Antigravity 2.0, IDE, and CLI

Install the complete workspace plugin:

```bash
living-docs init --agent antigravity
```

For all workspaces:

```bash
living-docs init -g --agent antigravity
```

The bundle contains `plugin.json`, `mcp_config.json`, and the shared Agent
Skill. Manual installers can still copy the checked-in template or replace
`mcp_config.json` with `mcp_config.uvx.json` for an `uvx` launch.

In Antigravity 2.0, open Settings → Customizations → Installed MCP Servers and
refresh. In the IDE, use Agent panel → MCP Servers → Manage MCP Servers. In the
CLI, run `/mcp` to view status, reload configuration, and inspect logs. The
same plugin layout is discoverable by Antigravity 2.0, IDE, and CLI.

Leave permissions in default Ask mode. Optional persistent grants should be
limited first to read-only `doctor`, `check_staleness`, `resolve_route`,
`validate_recipes`, and `plan_snapshot_sync`. Review `capture` and
`apply_snapshot_sync` separately because they navigate a site and write image
artifacts.

Living Docs starts an isolated Selenium Chrome session and never reuses the
Antigravity browser or user Chrome profile.

See the current [Antigravity MCP documentation](https://antigravity.google/docs/mcp)
and [plugin format](https://www.antigravity.google/docs/plugins).

## Smoke test

For every host:

1. Run `living-docs --version` to confirm the executable on `PATH`.
2. Confirm the server discovers exactly seven tools with no stdout noise.
3. Run `doctor`, `resolve_route`, and `validate_recipes`.
4. Confirm read-only and mutating permissions are presented as annotated.
5. Start the configured local app and capture one screenshot under the output
   root.
6. Reload/stop the MCP server and confirm Chrome and server processes exit.

If discovery or startup fails, see [Troubleshooting](TROUBLESHOOTING.md).
