# Migrating from Living Docs 1.x

Version 2.0 is a clean command migration. Existing
`living-docs-config.json` files and Markdown `snapshot-recipe` comments remain
compatible, but the Python and Bash script entrypoints are removed.

| 1.x command | 2.0 command |
| --- | --- |
| `python living-docs/scripts/git_helper.py staleness` | `living-docs check-staleness` |
| `python living-docs/scripts/resolver.py FILE` | `living-docs resolve-route FILE` |
| `python living-docs/scripts/updater.py` | `living-docs apply-sync` |
| `python living-docs/scripts/orchestrator.py --force-sync` | `living-docs apply-sync` |
| `bash living-docs/scripts/run_bot.sh --tasks ...` | `living-docs capture --recipe ...` |

There is no activation script, managed virtual environment, or first-use
dependency installation. Install the package once with `uv tool install
living-docs`, or use `uvx --from living-docs`.

Confirm the installed command with `living-docs --version`, then register it
with an agent using `living-docs init`. For example:

```bash
living-docs init --agent antigravity
living-docs init -g --codex
```

`init` merges native skill and MCP configuration; it does not install the
Python package.

Recommended migration:

1. Install version 2.0.
2. Run `living-docs doctor --project-root .`.
3. Run `living-docs validate-recipes --project-root .`.
4. Review `living-docs plan-sync --project-root . --json`.
5. Update agent-host MCP configuration to run `living-docs-mcp`.
6. Remove any automation that invokes files under the old `living-docs/`
   script directory.

Omitted `schema_version` is interpreted as version 1. New browser and security
sections are optional; their defaults preserve local `base_url` navigation and
project-root output while enforcing traversal checks.
