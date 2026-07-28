---
name: living-docs
description: Validate, plan, and update Markdown documentation snapshots when code or UI changes may make docs stale.
---

# Living Docs

Use the Living Docs MCP tools when they are available. If MCP is unavailable,
run the equivalent `living-docs` CLI command from the project root.
Use `living-docs --version` to verify that the executable is installed and on
`PATH`; do not probe the MCP server with `living-docs-mcp --help`.

## Workflow

1. Run `doctor` and explain any failed readiness checks before capture work.
2. Run `check_staleness` to identify affected Markdown and changed source files.
3. Update documentation text surgically from the relevant code changes.
4. For UI changes, run `resolve_route` with a project-relative source path.
5. Add or update an image followed immediately by a complete
   `snapshot-recipe` JSON comment.
6. Run `validate_recipes` before starting a browser.
7. Run `plan_snapshot_sync` and review its selected files and images.
8. Use `apply_snapshot_sync` only when the requested screenshots should be
   written. Use `capture` for one supplied recipe.

CLI fallbacks are:

- `living-docs doctor`
- `living-docs check-staleness`
- `living-docs resolve-route FILE`
- `living-docs validate-recipes [FILES...]`
- `living-docs plan-sync [--only-file FILE] [--only-image IMAGE]`
- `living-docs apply-sync [--only-file FILE] [--only-image IMAGE] [--review]`
- `living-docs capture --recipe RECIPE_JSON`

## Safety

- Treat every path as relative to the project root.
- Preserve existing configuration keys, flows, and mappings.
- Prefer `${ENV:NAME}` in configuration actions that type credentials.
- Never include passwords, tokens, cookies, or session files in messages.
- Treat `doctor`, staleness, route resolution, validation, and planning as
  read-only.
- Ask before `capture` or `apply_snapshot_sync` when the host has not already
  obtained permission to write images or interact with the configured site.
- Do not broaden `security.allowed_origins` or `security.output_root` without
  explicit user approval.
- Living Docs uses a new isolated Selenium Chrome session. It does not reuse
  the user's browser profile or an agent host's Chrome session.
