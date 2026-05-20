---
name: doc-pipeline
description: Master orchestrator that coordinates the technical documentation (doc-regen) and visual synchronization (ui-doc-sync) skills.
---

# Documentation Pipeline Orchestrator

This skill provides a unified interface for the entire Living Docs ecosystem. It bridges the gap between codebase changes and visual documentation.

## Core Capabilities

- **Unified Synchronization**: Runs both `doc-regen` and `ui-doc-sync` in a coordinated sequence.
- **Recipe Change Detection**: Automatically triggers visual updates if it detects that documentation "recipes" have been modified.
- **Readiness Auditing**: Verifies that the local environment (Git, Python, Dev Server) is prepared for a successful sync.

## When to Use

Trigger this skill when you want to ensure the *entire* documentation set is accurate, both in text and visuals.
- "Update documentation with recent changes"
- "Sync all documentation"
- "Run full doc sync"
- "Check if the doc pipeline is ready"

## How it Works

The orchestrator follows a three-stage logic:
1.  **Analysis**: It calls `doc-regen` helpers to identify stale files and code diffs.
2.  **Detection**: It scans for new or modified `snapshot-recipe` comments in your Markdown files.
3.  **Synchronization**: If a dev server is running and changes are detected, it triggers the visual capture engine to refresh screenshots.

## Best Practices

- **Local Server**: Always ensure your local development server is running before starting a full sync.
- **Review Mode**: Use the individual skills (`doc-regen`) if you only want to update text without refreshing images.
- **Batch Updates**: Use the pipeline after a series of commits to bring everything up to date in one go.
