# Configuration

Living Docs reads `living-docs-config.json` under the bound project root unless
`--config` selects another project-relative file.

## Minimal configuration

For a local app running at `http://localhost:3000`, create
`living-docs-config.json` in the project root:

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

Change both origin values when the app uses a different scheme, host, or port.
The checked-in [full configuration example](living-docs-config.json.example)
also demonstrates reusable login flows, route mappings, browser settings, and
environment-backed credentials.

After creating the file and starting the app, run:

```bash
living-docs doctor
living-docs validate-recipes
living-docs plan-sync
```

## Top-level fields

| Field | Default | Purpose |
| --- | --- | --- |
| `schema_version` | `1` | Optional schema marker; existing files are version 1. |
| `base_url` | `null` | Base for recipe URLs beginning with `/`. |
| `flows` | `{}` | Named prerequisite action sequences. |
| `mappings` | `[]` | Regex mappings from source paths to route candidates. |
| `workers` | `1` | Browser workers for apply operations, from 1 to 16. |
| `reuse_session` | `true` | Reuse one isolated driver across a Markdown file's recipes. |
| `browser` | defaults below | Chrome and ChromeDriver policy. |
| `security` | defaults below | Navigation and output boundaries. |

Unknown top-level and mapping fields are preserved for version-1
compatibility. Unknown recipe actions and action fields are rejected.

## Browser

```json
{
  "browser": {
    "binary_path": null,
    "driver_path": null,
    "headless": true,
    "window_size": [1920, 1080],
    "offline": false
  }
}
```

Resolution order is explicit paths, operating-system/PATH discovery, then
Selenium Manager discovery/download/cache. Offline mode permits only explicit,
PATH, or already cached binaries. Use `living-docs doctor` for resolution
diagnostics.

## Security

```json
{
  "security": {
    "allowed_origins": ["http://localhost:3000"],
    "output_root": "docs"
  }
}
```

When omitted, `allowed_origins` is the origin of `base_url` and `output_root`
is the project root. Paths in recipes must be relative. Resolution through
`..`, symlinks, or absolute paths cannot escape the configured root.

Only HTTP and HTTPS navigation is accepted. Redirects and post-click
navigation are checked again against the allowlist.

## Secrets

Use environment references in any string:

```json
{"action": "type", "selector": "#password", "text": "${ENV:APP_PASSWORD}"}
```

Missing variables fail validation. Literal values remain compatible, but keys
that look like credentials produce a warning. Living Docs does not log typed
text, cookies, local storage, session storage, or query strings.

## Actions

| Action | Required fields | Optional fields | Purpose |
| --- | --- | --- | --- |
| `goto` | `url` | — | Navigate to an allowed absolute URL or a path relative to `base_url`. |
| `click` | `selector` | `timeout` | Wait for and click an element. |
| `type` | `selector`, `text` | `timeout` | Wait for an element and enter text. |
| `wait` | — | `seconds` (default `1`) | Pause for a fixed interval from 0 through 300 seconds. |
| `wait_for_selector` | `selector` | `timeout` | Wait until an element is present. |
| `wait_for_hidden` | `selector` | `timeout` | Wait until an element is hidden or removed. |
| `wait_for_text` | `selector`, `text` | `timeout` | Wait until an element contains text. |
| `highlight` | `selector` | `timeout`, `style`, `color` | Add an `outline`, `spotlight`, or `badge` annotation. |
| `clear_highlights` | — | — | Remove annotations added by prior highlight actions. |
| `snapshot_page` | — | `filename` | Capture the page viewport. `snapshot` is a compatible alias. |
| `snapshot_element` | `selector` | `timeout`, `filename` | Capture one element. |
| `extract_info` | `selector` | `timeout`, `key` | Return sanitized element metadata with the result. |
| `save_session` | — | `filename` | Save browser session state inside the output boundary. |
| `restore_session` | `filename` | — | Restore a previously saved session file. |

Selectors are CSS selectors. Selector actions accept a `timeout` greater than
0 through 300 seconds; the default is 10 seconds. Unknown actions, fields, or
malformed selectors fail validation before Chrome starts.

Recipe `filename` values and Markdown image paths are resolved relative to the
Markdown file containing the recipe. For example, both
`![Dashboard](./assets/dashboard.png)` and
`"filename": "assets/dashboard.png"` in `docs/dashboard.md` resolve to
`docs/assets/dashboard.png`. Absolute paths and paths that escape
`security.output_root` are rejected.

## Recipe cookbook

Every recipe comment must immediately follow the Markdown image it owns. A
recipe can run reusable prerequisite flows first, followed by its own tasks.
Set `"prerequisites": []` when no flow is needed. For version-1 compatibility,
an embedded Markdown recipe that omits `prerequisites` is interpreted as
`["login"]`.

### Capture a public page element

```markdown
![Pricing table](./assets/pricing.png)
<!-- snapshot-recipe: {
  "prerequisites": [],
  "tasks": [
    {"action": "goto", "url": "/pricing"},
    {"action": "wait_for_selector", "selector": "[data-testid='pricing-table']"},
    {"action": "snapshot_element", "selector": "[data-testid='pricing-table']", "filename": "assets/pricing.png"}
  ]
} -->
```

### Log in with environment-backed credentials

Define the reusable flow in `living-docs-config.json`:

```json
{
  "base_url": "http://localhost:3000",
  "flows": {
    "login": [
      {"action": "goto", "url": "/login"},
      {"action": "type", "selector": "#email", "text": "${ENV:LIVING_DOCS_EMAIL}"},
      {"action": "type", "selector": "#password", "text": "${ENV:LIVING_DOCS_PASSWORD}"},
      {"action": "click", "selector": "button[type='submit']"},
      {"action": "wait_for_selector", "selector": "[data-testid='account-menu']"}
    ]
  }
}
```

Then reference it from one or more Markdown recipes:

```markdown
![Account dashboard](./assets/account-dashboard.png)
<!-- snapshot-recipe: {
  "prerequisites": ["login"],
  "tasks": [
    {"action": "goto", "url": "/account"},
    {"action": "wait_for_hidden", "selector": ".loading"},
    {"action": "snapshot_page", "filename": "assets/account-dashboard.png"}
  ]
} -->
```

Set the variables in the environment that starts the CLI or agent host. For
example:

```bash
export LIVING_DOCS_EMAIL="docs-user@example.test"
export LIVING_DOCS_PASSWORD="..."
```

```powershell
$env:LIVING_DOCS_EMAIL = "docs-user@example.test"
$env:LIVING_DOCS_PASSWORD = "..."
```

### Highlight a feature and collect metadata

```markdown
![Export control](./assets/export-control.png)
<!-- snapshot-recipe: {
  "prerequisites": ["login"],
  "tasks": [
    {"action": "goto", "url": "/reports"},
    {"action": "wait_for_text", "selector": "h1", "text": "Reports"},
    {"action": "highlight", "selector": "[data-testid='export']", "style": "spotlight"},
    {"action": "extract_info", "selector": "[data-testid='export']", "key": "export-control"},
    {"action": "snapshot_page", "filename": "assets/export-control.png"},
    {"action": "clear_highlights"}
  ]
} -->
```

`extract_info` returns sanitized text, tag, and attribute metadata alongside
the screenshot artifacts. It does not expose cookies, browser storage, or
typed secret values.

### Review before replacing an existing screenshot

Validate and plan first; neither command starts Chrome or writes files:

```bash
living-docs validate-recipes docs/dashboard.md
living-docs plan-sync --only-file docs/dashboard.md
```

Then prepare a candidate and visual difference without replacing the image:

```bash
living-docs apply-sync --review --only-file docs/dashboard.md
```

Inspect the artifacts under `.living-docs/review/`. To accept the current UI
state, run the same command without `--review`.

Session files remain inside the output boundary, are written with restrictive
permissions where the operating system supports them, and are never included
in MCP results.

## Review and provenance output

`apply-sync --review` redirects screenshot actions into
`<output_root>/.living-docs/review/candidates/` and creates comparison images
under `diffs/`. It never replaces the recipe's target screenshot. Review
artifacts are still filesystem writes, so MCP hosts correctly present the
operation as mutating.

Normal and review syncs write separate provenance manifests:

```text
<output_root>/.living-docs/provenance.json
<output_root>/.living-docs/review/provenance.json
```

Provenance contains hashes and browser diagnostics, not recipe contents,
typed values, cookies, storage, URL queries, or URL fragments.
