---
name: living-docs
description: Automates documentation updates, synchronization, and UI snapshots. Use this whenever you need to update or check documentation, especially if it involves screenshots or technical sync.
---

# Living Docs Toolkit

The `living-docs` skill is a comprehensive suite for keeping your documentation in sync with your codebase. It handles technical staleness detection, UI route resolution, and automated screenshot synchronization.

## Prerequisites

To function correctly, this skill requires:
1.  **Git Repository**: The project must be a git repository for staleness detection.
2.  **Configuration**: A `living-docs-config.json` file in the project root.
    - At minimum, it must contain a `"base_url"` (e.g., `"http://localhost:3000"`).
    - If missing, you MUST identify the frontend base URL from documentation (e.g., `README.md`, `package.json` scripts, or `.env` files) and create it or ask the user for it.
3.  **Running Server**: The local development server MUST be running at the `base_url`.
4.  **Chrome/Chromium**: Installed on the system for the Selenium bot.

## When to Use

Use this skill whenever documentation needs a refresh or when visual changes in the UI need to be reflected in the docs.
- "Update documentation"
- "Sync all documentation"
- "Update the user-guide"
- "Regen technical and user docs"
- "Check if documentation is stale"
- "Capture screenshots of the UI"
- "The UI has changed, update the docs"

## Actions

### `regen_all` (Main Orchestrator)
**Trigger**: "Update documentation", "Sync documentation", "Regen docs", "Update my docs"
The master orchestrator. It runs the full pipeline:
1.  Identifies stale documentation.
2.  Scans for modified snapshot recipes.
3.  Triggers a full UI synchronization if needed.

### `sync_ui_docs`
**Trigger**: "Update screenshots", "Sync visuals", "Regen user documentation"
The primary tool for visual synchronization. It scans your Markdown files for `snapshot-recipe` comments and automatically updates the associated images by running the browser bot.

### `check_staleness`
**Trigger**: "Which docs are stale?", "Check staleness"
Identifies which documentation files are out of sync with recent code changes. This helps you identify where documentation needs a technical refresh.

### `take_snapshot`
**Trigger**: "Take a screenshot", "Capture this page"
Captures a screenshot of a specific URL or UI element. This is the low-level tool for generating visual assets.
- **tasks**: Path to a JSON file defining actions (goto, click, snapshot_element, etc.).

### `resolve_route`
**Trigger**: "Find the route for this file", "Where is this component?"
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

## Agent Workflow Instructions

When tasked with updating documentation, you MUST follow this sequence:

1.  **Configuration Check**: 
    - Check if `living-docs-config.json` exists in the root.
    - If it doesn't, or if `base_url` is missing, SEARCH the project (README, package.json, etc.) for the development server URL.
    - Propose creating/updating the config if needed.

2.  **Discovery & Staleness**: 
    - Identify stale documents and relevant changed files using the `check_staleness` action.
    - Fetch the specific code diffs for the affected document.

3.  **Text Synchronization**: 
    - Surgically update the Markdown text to reflect the new code logic, API changes, and variable names based on the diffs.

4.  **Visual Sync Preparation (Recipe Generation)**:
    If the modified files involve UI components (e.g., `.tsx`, `.jsx`, `.html`):
    - **Resolve Route**: Use the `resolve_route` action to find where the component can be viewed.
    - **Suggest Selectors**: Use `scripts/discovery_helper.py` to suggest CSS selectors for the component.
    - **Update Recipes**: Search the documentation for existing images related to this component. If visuals need updating or adding, you MUST add/update a `snapshot-recipe` comment immediately after the Markdown image link.
      ```markdown
      ![Component Name](./assets/filename.png)
      <!-- snapshot-recipe: {
        "tasks": [
          {"action": "goto", "url": "RESOLVED_URL"},
          {"action": "snapshot_element", "selector": "SUGGESTED_SELECTOR", "filename": "assets/filename.png"}
        ]
      } -->
      ```

5.  **Pipeline Execution**:
    After updating text and recipes, you MUST trigger the final synchronization.
    - Run the `regen_all` action with `force=true`.

## Best Practices

- **Virtual Environment**: The skill automatically manages its own `venv` in the skill directory.
- **Local Server**: Visual sync will fail if the server is not running at the `base_url`.
