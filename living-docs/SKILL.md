---
name: living-docs
description: The complete Living Docs toolkit for discovery, technical synchronization, and automated UI snapshots.
---

# Living Docs Toolkit

The `living-docs` skill is a comprehensive suite for keeping your documentation in sync with your codebase. It handles technical staleness detection, UI route resolution, and automated screenshot synchronization.

## Actions

### `check_staleness`
Checks which Markdown files are out of sync with recent code changes. This helps you identify where documentation needs a technical refresh.

### `take_snapshot`
Captures a screenshot of a specific URL or UI element. This is the low-level tool for generating visual assets.
- **tasks**: Path to a JSON file defining actions (goto, click, snapshot_element, etc.).

### `sync_ui_docs`
The primary tool for visual synchronization. It scans your Markdown files for `snapshot-recipe` comments and automatically updates the associated images by running the browser bot.

### `regen_all`
The master orchestrator. It runs the full pipeline:
1.  Identifies stale documentation.
2.  Scans for modified snapshot recipes.
3.  Triggers a full UI synchronization if needed.

### `resolve_route`
Maps a UI component source file (e.g., `src/components/Login.tsx`) to its live web route (URL) to help you create snapshot recipes.

## Screenshot Recipes

To automate a screenshot, add a `snapshot-recipe` comment immediately after an image link in your Markdown:

```markdown
![Login Form](./assets/login.png)
<!-- snapshot-recipe: {
  "tasks": [
    {"action": "goto", "url": "/login"},
    {"action": "snapshot_element", "selector": "#login-form", "filename": "assets/login.png"}
  ]
} -->
```

## Setup & Prerequisites

- **Virtual Environment**: The skill automatically manages its own `venv` in the skill directory.
- **Local Server**: For UI snapshots to work, your local development server must be running (usually on port 3000 or as configured in `living-docs-config.json`).
- **Chrome**: Requires a local Chrome/Chromium installation for the Selenium bot.
