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
    - It may contain `"flows"` (e.g., login sequences) and `"mappings"`. **IMPORTANT**: `flows` often contain non-recoverable credentials. You MUST NEVER drop or overwrite these without explicit user consent.
    - If missing, you MUST identify the frontend base URL from documentation and propose a new configuration to the user.
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

1.  **Configuration Check (Non-Destructive)**: 
    - You MUST read the existing `living-docs-config.json` if it exists. NEVER assume it is empty or missing.
    - **Preservation Policy**: You MUST PRESERVE all existing keys. `flows` and `mappings` often contain irreplaceable manual configurations (credentials, custom routes for unsupported frameworks). 
    - **Mapping Intelligence**:
        - If the project uses a supported framework (e.g., Next.js), you may suggest adding *new* mappings for new files.
        - If the project technology is unknown/unsupported, or if a mapping already exists for a file, you MUST NOT change the existing mapping.
        - Treat existing mappings without an `"origin": "auto"` tag as **user-defined** and immutable.
    - **MANDATORY**: If you need to propose any change to the config, you MUST use `ask_user` to present the proposed full JSON content. Explicitly highlight what is being added and confirm that all existing data is preserved.
    - Only create a new file if it is absolutely missing and after obtaining user approval.

2.  **Discovery & Staleness**: 
    - Identify stale documents and relevant changed files using the `check_staleness` action.
    - Fetch the specific code diffs for the affected document.

3.  **Text Synchronization**: 
    - Surgically update the Markdown text to reflect the new code logic, API changes, and variable names based on the diffs.

4.  **Visual Sync Preparation (Recipe Generation)**:
    If the modified files involve UI components (e.g., `.tsx`, `.jsx`, `.html`):
    - **Resolve Route**: Use the `resolve_route` action to find where the component can be viewed.
    - **Handle Dynamic Routes**: If the resolved URL contains dynamic segments (e.g., `/courses/[id]`), you MUST search the codebase for sample data (e.g., in tests or mock data files) to find a valid ID and replace the segment (e.g., `/courses/123`).
    - **Suggest Selectors**: Use `scripts/discovery_helper.py` to suggest CSS selectors for the component.
    - **Update Recipes**: Search the documentation for existing images related to this component. If visuals need updating or adding, you MUST add/update a `snapshot-recipe` comment immediately after the Markdown image link.
      ```markdown
      ![Component Name](./assets/filename.png)
      <!-- snapshot-recipe: {
        "tasks": [
          {"action": "goto", "url": "RESOLVED_URL_WITH_REAL_IDS"},
          {"action": "wait_for_hidden", "selector": ".loading-spinner"},
          {"action": "snapshot_element", "selector": "SUGGESTED_SELECTOR", "filename": "assets/filename.png"}
        ]
      } -->
      ```

5.  **Stabilization**:
    If a snapshot results in a "Loading..." state or missing data:
    - Identify the loading element's selector or the "Loading" text.
    - Add a `wait_for_hidden` (for the selector) or `wait_for_text` (waiting for the real content to appear) task before the `snapshot_element` action.

6.  **Pipeline Execution**:
    After updating text and recipes, you MUST trigger the final synchronization.
    - Run the `regen_all` action with `force=true`.

## Best Practices

- **Virtual Environment**: The skill automatically manages its own `venv` in the skill directory.
- **Local Server**: Visual sync will fail if the server is not running at the `base_url`.

## Manual Retries & Troubleshooting

### Handling "Loading..." States
If a snapshot captures a "Loading..." placeholder, the browser bot likely executed the snapshot before the content finished loading.
1.  **Stabilize**: Update the `snapshot-recipe` in the Markdown file to include a `wait_for_hidden` (for the spinner) or `wait_for_text` (for the final content) action before the `snapshot_element` or `snapshot_page` action.
2.  **Targeted Retry**: Instead of running `sync_ui_docs` or `regen_all`, which syncs everything, use the `take_snapshot` action to regenerate ONLY the affected image by passing the updated tasks.

### Targeted Regeneration
If you only need to update a single image, you do not need to run the full pipeline. You can manually execute the browser bot tasks for that specific image using the `take_snapshot` action.

