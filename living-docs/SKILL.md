---
name: living-docs
description: The complete Living Docs toolkit for discovery, technical synchronization, and automated UI snapshots.
---

# Living Docs Toolkit

The `living-docs` skill is a comprehensive suite for keeping your documentation in sync with your codebase. It handles technical staleness detection, UI route resolution, and automated screenshot synchronization.

## When to Use

Use this skill when you need to update any documentation in the project, especially if it involves technical details or UI screenshots.
- "Update documentation with latest changes"
- "Sync all documentation"
- "Update the user-guide document"
- "Regen technical and user docs"
- "Check if documentation is stale"

## Actions

### `regen_all` (Main Orchestrator)
**Trigger**: "Update documentation", "Sync documentation", "Regen docs"
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

When tasked with updating documentation, you MUST follow this sequence to ensure both technical and visual accuracy:

1.  **Discovery & Staleness**: 
    - Identify stale documents and relevant changed files using the `check_staleness` action (or `scripts/git_helper.py staleness`).
    - Fetch the specific code diffs for the affected document.

2.  **Text Synchronization**: 
    - Surgically update the Markdown text to reflect the new code logic, API changes, and variable names based on the diffs.

3.  **Visual Sync Preparation (Recipe Generation)**:
    If the modified files involve UI components (e.g., `.tsx`, `.jsx`, `.html`):
    - **Resolve Route**: Use the `resolve_route` action (or `scripts/resolver.py`) to find where the component can be viewed.
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

4.  **Pipeline Execution**:
    After you have updated the text and modified the recipes in the `.md` file, you MUST trigger the final synchronization to apply the visual changes.
    - Run the `regen_all` action with `force=true` (or `scripts/orchestrator.py --force-sync`).

## Best Practices

- **Virtual Environment**: The skill automatically manages its own `venv` in the skill directory.
- **Local Server**: For UI snapshots to work, your local development server must be running (usually on port 3000 or as configured in `living-docs-config.json`).
- **Chrome**: Requires a local Chrome/Chromium installation for the Selenium bot.
