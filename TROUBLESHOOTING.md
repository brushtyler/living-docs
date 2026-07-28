# Troubleshooting

Start with:

```bash
living-docs --version
living-docs doctor --project-root .
```

`doctor` is read-only. It reports Python, configuration, output-directory,
base-URL, Chrome, and ChromeDriver readiness without starting a browser
capture.

## `living-docs` is not found

Confirm that `uv` installed the package:

```bash
uv tool list
uv tool dir --bin
```

If the tool binary directory is not on `PATH`, run:

```bash
uv tool update-shell
```

Restart the terminal and run `living-docs --version` again. `uv tool install`
uses an isolated tool environment; it does not install Living Docs into the
current project's virtual environment.

From a Living Docs source checkout, include the package path:

```bash
uv tool install --force .
```

The command `uv tool install --force` alone is incomplete because `uv` still
needs a package name or path.

## The AI agent cannot see Living Docs tools

First confirm that the executable is available in the environment that starts
the agent:

```bash
living-docs --version
```

Preview and repeat registration for the selected host:

```bash
living-docs init --agent antigravity --dry-run
living-docs init --agent antigravity
```

Replace `antigravity` with the relevant selector. Project registration is
visible only when the agent opens that project. User registration with `-g`
applies to all projects for the current user.

Restart the host or reload its MCP configuration after registration. In
Antigravity CLI use `/mcp`; in Antigravity IDE refresh the MCP Servers panel.
Cursor exposes reload controls in MCP settings. See
[Agent host integrations](INTEGRATIONS.md) for host-specific locations.

Do not test the stdio server by running `living-docs-mcp` interactively. It is
intended to be launched by an MCP host and reserves stdout for JSON-RPC.

## `CONFIG_NOT_FOUND` or configuration is not ready

Create `living-docs-config.json` in the project root. At minimum it needs the
development app URL:

```json
{
  "base_url": "http://localhost:3000",
  "security": {
    "allowed_origins": ["http://localhost:3000"],
    "output_root": "."
  }
}
```

Use `--config PATH` when the file has another project-relative name.

## The base URL is not ready

`doctor` makes a short TCP connection to the host and port in `base_url`.
Start the development app and verify that the configured scheme, host, and
port are correct. A service listening only inside a container may need a
published host port that the Living Docs process can reach.

## `BROWSER_UNAVAILABLE`

Install Chrome or Chromium, then rerun `living-docs doctor`. By default,
Living Docs looks for the operating-system browser and driver before allowing
Selenium Manager to discover, download, and cache compatible binaries.

For restricted machines, configure explicit paths:

```json
{
  "browser": {
    "binary_path": "/path/to/chrome",
    "driver_path": "/path/to/chromedriver",
    "headless": true,
    "window_size": [1920, 1080],
    "offline": false
  }
}
```

Windows JSON paths must escape backslashes, for example
`"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"`.

With `"offline": true`, both Chrome and ChromeDriver must be explicit, on
`PATH`, or already present in Selenium's cache. Living Docs will not allow
Selenium Manager network activity in offline mode.

## `NAVIGATION_DENIED`

Every initial navigation, redirect, and post-click destination must match an
entry in `security.allowed_origins`. Origins include the scheme, hostname, and
port. For example, `http://localhost:3000` and `http://localhost:5173` are
different origins.

Add only origins the recipe genuinely needs. Do not add a wildcard or broaden
the allowlist simply to bypass the error.

## `OUTPUT_PATH_DENIED` or `INPUT_PATH_DENIED`

Use project-relative paths. Absolute paths and `..` traversal outside the
bound project are rejected. Screenshot and session outputs must also remain
under `security.output_root`.

Recipe output paths are relative to their Markdown file. In
`docs/guide.md`, the pair below writes `docs/assets/page.png`:

```markdown
![Page](./assets/page.png)
<!-- snapshot-recipe: {
  "prerequisites": [],
  "tasks": [
    {"action": "goto", "url": "/"},
    {"action": "snapshot_page", "filename": "assets/page.png"}
  ]
} -->
```

## `INVALID_RECIPE` or `DUPLICATE_OUTPUT`

Run validation before capture:

```bash
living-docs validate-recipes
living-docs plan-sync
```

Check that:

- the recipe comment immediately follows its Markdown image;
- the comment contains one complete JSON object;
- `tasks` contains at least one supported action;
- selectors are non-empty, balanced CSS selectors;
- every prerequisite names a flow in `living-docs-config.json`;
- a snapshot action writes the image immediately preceding the recipe; and
- no other recipe resolves to the same output image.

Validation failures are reported before Chrome starts.

## `ELEMENT_TIMEOUT`

Confirm the selector against the isolated page state reached by the recipe.
Prefer stable attributes such as `data-testid` over generated classes. Add a
specific readiness action such as `wait_for_selector`, `wait_for_hidden`, or
`wait_for_text` instead of relying on a large fixed `wait`.

Selector actions accept a `timeout` greater than 0 through 300 seconds:

```json
{"action": "wait_for_selector", "selector": "#dashboard", "timeout": 30}
```

## A review capture did not replace the screenshot

That is expected. `--review` writes candidate and visual-difference artifacts
under `<output_root>/.living-docs/review/`. After inspecting and approving
them, run the same selection without `--review`:

```bash
living-docs apply-sync --only-file docs/dashboard.md
```

Normal apply operations also update the sanitized provenance manifest at
`<output_root>/.living-docs/provenance.json`.

## Get structured diagnostics

Add `--json` when reporting a problem or consuming results in automation:

```bash
living-docs doctor --json
living-docs validate-recipes --json
living-docs plan-sync --json
```

Failures include stable codes and details while logs remain on stderr.
