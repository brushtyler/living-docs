---
name: doc-regen
description: Automatically regenerate or update documentation (Markdown files) based on recent codebase changes. Uses Git history to identify stale documents and synchronizes them with current code.
---

# Documentation Regeneration Skill

This skill helps maintain documentation accuracy by identifying which parts of your codebase have changed since a documentation file was last updated.

## Core Capabilities

- **Staleness Detection**: Identifies `.md` files that are older than the latest code changes.
- **Change Analysis**: Retrieves the specific code diffs that occurred since a document was last touched.
- **Surgical Updates**: Updates documentation while preserving style, structure, and existing manual edits.

## How to Use

Trigger this skill when you want to ensure your documentation matches your implementation. Common triggers:
- "Regen documentation"
- "Update README for recent changes"
- "Check if any docs are out of date"

### Workflow

1.  **Analyze Staleness**: The skill runs a helper to list all documentation files and how many commits they are "behind" the current codebase.
    ```bash
    python3 doc-regen/scripts/git_helper.py staleness
    ```
2.  **Filter & Contextualize**: For a target document (e.g., `README.md`), it identifies relevant changed files.
3.  **Retrieve Diffs**: It fetches the relevant code changes.
    ```bash
    python3 doc-regen/scripts/git_helper.py diff <doc_file_path>
    ```
4.  **Visual Synchronization (UI Components)**:
    If modified files are UI components (e.g., `.tsx`, `.jsx`, `.html`):
    - Use the **Route Resolver** to find where the component can be viewed:
      ```bash
      python3 doc-regen/scripts/resolver.py <ui_file_path>
      ```
    - Use the **Discovery Helper** to suggest selectors and names:
      ```bash
      python3 doc-regen/scripts/discovery_helper.py <ui_file_path>
      ```
    - Search the documentation for existing images or recipes related to this component.
    - **Update/Create Recipes**: Write or update the recipe in the Markdown file. **Crucially**, you must include both the image link and the `snapshot-recipe` comment immediately after it.
      ```markdown
      ![Component Name](./assets/filename.png)
      <!-- snapshot-recipe: {
        "tasks": [
          {"action": "goto", "url": "RESOLVED_URL"},
          {"action": "snapshot_element", "selector": "SUGGESTED_SELECTOR", "filename": "assets/filename.png"}
        ]
      } -->
      ```
    - **Execute Sync**: After updating the recipes, you MUST ensure they are visually synchronized.
      1.  **Verify Changes**: Run the `detect recipe changes` action to confirm recipes were added/modified.
      2.  **Trigger Sync**: Use the unified orchestrator or trigger `ui-doc-sync`:
          ```bash
          python3 scripts/doc_sync_manager.py --force-sync
          ```
          Alternatively, say: "**regen user documentation**".
      (Ensure the local dev server is running before triggering the sync).
5.  **LLM Synthesis**: The agent combines the current document content with the relevant diffs to generate an updated version.
6.  **Unified Pipeline**: For a full sweep of the codebase and documentation, use the unified manager:
    ```bash
    python3 scripts/doc_sync_manager.py
    ```

### Fallback (No Git)
If the project is not a Git repository:
- The skill will check the current session's modified files.
- It will ask you which files/features were recently implemented to guide the update.

## Best Practices

- **Surgicality**: Only update parts of the documentation that are directly impacted by code changes.
- **Verify References**: Ensure that updated documentation correctly reflects new variable names, function signatures, or configuration options.
- **Review**: Always review the proposed changes to ensure the tone and clarity are maintained.
