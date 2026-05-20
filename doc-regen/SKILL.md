---
name: doc-regen
description: Master orchestrator to update all documentation with the latest codebase changes. Coordinates text updates, visual UI snapshots, and documentation discovery.
---

# Documentation Regeneration Pipeline

This is the primary entry point for keeping the entire documentation ecosystem in sync with the codebase. It coordinates several specialized skills to ensure both technical accuracy and visual fidelity.

## Core Capabilities

- **Full Ecosystem Sync**: Orchestrates `doc-sync` for text and `ui-doc-sync` for visuals.
- **Change-Driven Automation**: Automatically detects where documentation is stale and what UI recipes need refreshing.
- **Comprehensive Updates**: Handles everything from simple technical README updates to complex UI screenshot synchronization.

## When to Use

Trigger this skill for any general request to update or synchronize documentation.
- "Update documentation with latest changes"
- "Sync all documentation"
- "Update the user-guide document"
- "Regen technical and user docs"
- "Is my documentation up to date?"

## Agent Workflow Instructions

When tasked with updating documentation, you MUST follow this sequence:

1.  **Discovery & Staleness**: 
    - Identify stale documents and relevant changed files using the `doc-discovery` skill.
    ```bash
    python3 doc-discovery/scripts/git_helper.py staleness
    ```
    - Fetch the specific code diffs for the affected document.

2.  **Text Synchronization**: 
    - Surgically update the Markdown text to reflect the new code logic, API changes, and variable names based on the diffs.

3.  **Visual Sync Preparation (Recipe Generation)**:
    If the modified files involve UI components (e.g., `.tsx`, `.jsx`, `.html`):
    - Use the Route Resolver to find where the component can be viewed:
      ```bash
      python3 doc-discovery/scripts/resolver.py <ui_file_path>
      ```
    - Use the Discovery Helper to suggest selectors and names:
      ```bash
      python3 doc-discovery/scripts/discovery_helper.py <ui_file_path>
      ```
    - **Crucial Step**: Search the documentation for existing images related to this component. If visuals need updating or adding, you MUST add/update a `snapshot-recipe` comment immediately after the Markdown image link.
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
    After you have updated the text and modified the recipes in the `.md` file, you MUST trigger the final orchestrator script to apply the visual synchronization.
    ```bash
    python3 doc-regen/scripts/orchestrator.py --force-sync
    ```

## Best Practices

- **Dev Server**: Ensure your local development server is running if UI snapshots are expected.
- **Holistic Review**: Use the pipeline for a complete sweep of the project, especially before a release or after major refactoring.
