---
name: doc-sync
description: Surgically synchronize the text of technical Markdown documents based on recent code diffs. Focuses on content accuracy without visual capture.
---

# Documentation Sync Skill

This skill helps maintain technical documentation by identifying which parts of your codebase have changed since a document was last updated and applying surgical text updates.

## Core Capabilities

- **Content Staleness Detection**: Identifies `.md` files that are out of sync with recent code changes.
- **Change Extraction**: Retrieves relevant code diffs to guide documentation updates.
- **Surgical Text Updates**: Updates technical details (variable names, logic, config) while preserving manual prose.

## How to Use

Trigger this skill when you want to update the text of your documentation to match code changes.
- "Sync code changes to markdown"
- "Update technical document text"
- "Check for technical doc staleness"

### Workflow

1.  **Analyze Staleness**: Identify which documents need updating using the `doc-discovery` skill.
2.  **Retrieve Diffs**: Fetch relevant code changes using `git_helper.py` in `doc-discovery`.
3.  **LLM Synthesis**: The agent combines the current document content with the relevant diffs to generate an updated version.
4.  **Review**: Verify that the technical accuracy is maintained.

## Best Practices

- **Minimal Edits**: Only update parts of the documentation that are directly impacted by code changes.
- **Accuracy**: Ensure updated documentation reflects new variable names or logic correctly.
