# Living Docs 2.0

Living Docs keeps Markdown UI snapshots reproducible. Version 2.0 is an
installable, cross-platform Python package with one shared implementation
behind a human-friendly CLI and a typed stdio MCP server.

## Five-minute quick start

These steps take a new project from installation to a review capture that does
not replace an existing screenshot.

1. Install Living Docs and confirm that its command is available:

   ```bash
   uv tool install living-docs
   living-docs --version
   ```

2. Register it with your AI coding agent. Choose the command for your host:

   ```bash
   living-docs init                  # Claude Code, project scope
   living-docs init --codex          # Codex, project scope
   living-docs init --agent cursor   # Cursor, project scope
   living-docs init --agent antigravity
   ```

   Add `-g` to use the tool in every project for the current user. Restart the
   agent host or reload its MCP servers after registration.

3. Create `living-docs-config.json` in the project root and change the URL to
   the address of your development app:

   ```json
   {
     "schema_version": 1,
     "base_url": "http://localhost:3000",
     "security": {
       "allowed_origins": ["http://localhost:3000"],
       "output_root": "."
     }
   }
   ```

4. Put an image and its reproducible recipe in a Markdown file such as
   `docs/dashboard.md`:

   ```markdown
   ![Dashboard](./assets/dashboard.png)
   <!-- snapshot-recipe: {
     "prerequisites": [],
     "tasks": [
       {"action": "goto", "url": "/dashboard"},
       {"action": "wait_for_hidden", "selector": ".loading"},
       {"action": "snapshot_element", "selector": "#dashboard", "filename": "assets/dashboard.png"}
     ]
   } -->
   ```

   Image and recipe output paths are resolved relative to the Markdown file.
   The recipe must capture the image it immediately follows.

5. Start the development app using the project's normal command, then verify
   the setup without writing screenshots:

   ```bash
   living-docs doctor
   living-docs validate-recipes docs/dashboard.md
   living-docs plan-sync --only-file docs/dashboard.md
   ```

6. Open the registered agent and paste:

   > Use Living Docs to refresh the screenshots in `docs/dashboard.md` in
   > review mode. Preserve the existing images, show me the candidate and
   > visual-difference artifacts, and wait for my approval.

Review mode writes candidates under `.living-docs/review/` but leaves the
Markdown image unchanged. After inspecting the result, explicitly ask the
agent to apply the approved update.

## Install

Python 3.12 or newer and Chrome/Chromium are required. ChromeDriver is resolved
from explicit configuration, the operating system, or Selenium Manager.

```bash
uv tool install living-docs
living-docs --version
living-docs doctor --project-root .
```

`uv tool install` creates a dedicated virtual environment for Living Docs and
links its executables into the `uv` tool binary directory. It does not add
Living Docs dependencies to the current project environment or the system
Python installation. If the command is not on `PATH`, run `uv tool
update-shell`, restart the shell, and try `living-docs --version` again. See
the [`uv` tools documentation](https://docs.astral.sh/uv/concepts/tools/).

From a source checkout, pass the package path to `uv`:

```bash
uv tool install --force .
```

`uv tool install --force` by itself is incomplete because `uv` still needs a
package name or path.

Run without a persistent installation:

```bash
uvx --from living-docs living-docs-mcp --project-root .
```

Start the MCP server from a host, not an interactive terminal:

```bash
living-docs-mcp --project-root .
```

The server uses stdout only for JSON-RPC. Diagnostics and application logs go
to stderr. Chrome starts lazily for capture/apply calls and always closes after
the invocation.

## CLI

```text
living-docs --version
living-docs init [-g] [--agent AGENT | --gemini | --codex | --copilot] [--dry-run]
living-docs doctor
living-docs check-staleness
living-docs resolve-route FILE
living-docs validate-recipes [FILES...]
living-docs capture --recipe RECIPE_JSON
living-docs plan-sync [--only-file FILE] [--only-image IMAGE]
living-docs apply-sync [--only-file FILE] [--only-image IMAGE] [--workers N] [--review]
```

Register the installed tool with an AI coding agent:

```bash
living-docs init -g                     # Claude Code (default)
living-docs init -g --gemini            # Gemini CLI
living-docs init -g --codex             # Codex
living-docs init -g --copilot           # GitHub Copilot
living-docs init --agent cursor
living-docs init --agent windsurf
living-docs init --agent cline          # Cline / Roo Code
living-docs init --agent kilocode
living-docs init --agent antigravity
living-docs init --agent kimi
living-docs init --agent pi
living-docs init --agent hermes
living-docs init -g --agent droid
```

Without `-g`, configuration is written inside the project. With `-g`, it is
written under the current user's home directory. Existing host configuration
is merged rather than replaced. Use `--dry-run` to inspect target files first.
`init` registers the already-installed executable; it does not install the
Python package.

Global `--project-root`, `--config`, `--log-level`, and `--json` options may
appear before or after the subcommand. Human-readable output is the default;
`--json` returns the same result envelope used by MCP:

```json
{
  "ok": true,
  "summary": "Planned 1 snapshot(s)",
  "data": {},
  "artifacts": [],
  "warnings": [],
  "errors": []
}
```

## Prompt examples for AI agents

The installed Agent Skill teaches supported hosts when and how to use Living
Docs. These prompts give the agent an explicit goal and permission boundary.

### Diagnose without changing files

> Use Living Docs to check whether this project is ready. Run diagnostic and
> read-only checks only. Explain anything I need to fix, and do not modify
> files or start a capture.

### Find stale documentation

> Use Living Docs to determine whether my documentation or screenshots are
> stale. Resolve affected UI routes, validate the recipes, and show me the
> synchronization plan. Do not write any files.

### Investigate one UI change

> Use Living Docs to inspect the changes to
> `src/components/Dashboard.tsx`. Tell me which documentation pages,
> routes, and screenshots may be affected. Do not update them yet.

### Add a recipe without capturing

> Add a reproducible Living Docs snapshot recipe for the dashboard image in
> `docs/dashboard.md`. Reuse existing prerequisite flows where possible,
> validate the recipe, and show me the synchronization plan without starting
> a browser or writing a screenshot.

### Prepare screenshots for review

> Use Living Docs to refresh the screenshots in `docs/dashboard.md` in review
> mode. Preserve the existing images, show me the candidate and
> visual-difference artifacts, and wait for my approval.

### Apply an approved update

> Apply the approved Living Docs screenshot updates for
> `docs/dashboard.md`. Then summarize the generated artifacts, per-image
> outcomes, and provenance.

The first four prompts authorize read-only analysis or documentation editing
without browser output. The review prompt writes candidate and difference
artifacts but does not replace current screenshots. The final prompt
explicitly authorizes replacement.

## Recipes

A recipe comment must immediately follow its Markdown image, as shown in the
[quick-start example](#five-minute-quick-start). Paths are relative to the
Markdown file, and the snapshot action must write the image it follows. The
[recipe cookbook](CONFIGURATION.md#recipe-cookbook) covers public pages,
authenticated flows, loading states, highlights, element metadata, viewport
captures, and review mode.

Existing version-1 configuration and recipes remain data-compatible. See
[Configuration](CONFIGURATION.md), [agent integrations](INTEGRATIONS.md), and
the [2.0 migration guide](MIGRATION.md).

## Review before replacement

Use review mode after a UI change to capture proposed screenshots without
replacing the images referenced by Markdown:

```bash
living-docs apply-sync --review --only-file docs/dashboard.md
```

For changed screenshots, Living Docs writes a three-panel
current/candidate/difference image under
`<output_root>/.living-docs/review/`. The result reports each candidate as
`new`, `changed`, or `unchanged`. Inspect the review artifacts, then run the
same `apply-sync` command without `--review` to accept the current UI state.
The MCP `apply_snapshot_sync` tool provides the same `review` option.

Every successful sync also updates a sanitized provenance manifest under
`<output_root>/.living-docs/provenance.json`; review captures use the review
directory instead. It records the inferred Markdown owner, stable recipe ID,
recipe fingerprint, source revision, viewport, browser/driver versions, and a
final URL with query strings and fragments removed.

## Impact and ownership

`check-staleness` now includes a `snapshot_impact` section. It combines source
route mappings with recipe navigation steps to show which screenshots are
likely affected by each changed UI file. Dynamic routes such as `[id]` and
catch-all segments are supported.

Ownership requires no extra configuration: the Markdown file containing a
recipe owns that recipe, and its stable ID is derived from the owner and image
path. Validation rejects recipes that do not capture their immediately
preceding image and rejects multiple recipes that resolve to the same output.

## Security model

- MCP is bound to one resolved project root.
- Tool paths must be relative and cannot traverse outside that root.
- Outputs must remain inside `security.output_root`.
- Navigation is limited to `security.allowed_origins`, which defaults to the
  configured `base_url` origin.
- `${ENV:NAME}` resolves secrets at runtime; likely literal credentials produce
  warnings and are redacted from diagnostics.
- Cookies and browser storage are never returned by tools or logged.
- Each browser call uses an isolated Selenium Chrome session, not a user's or
  agent host's Chrome profile.

## Troubleshooting

Run `living-docs doctor` first when capture work fails. It checks Python,
configuration, output permissions, the base URL, Chrome, and ChromeDriver.
See [Troubleshooting](TROUBLESHOOTING.md) for common installation, MCP,
navigation, browser, and recipe errors.

## Development

```bash
python -m pip install -e ".[test]"
python -m pytest
python -m build
```

Set `LIVING_DOCS_REAL_BROWSER=1` to include the real-Chrome smoke test.

## License

MIT
