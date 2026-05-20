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

## How it Works

The pipeline follows a multi-stage process:
1.  **Discovery**: Uses `doc-discovery` to find stale documentation and map code changes to relevant UI routes.
2.  **Text Sync**: Triggers `doc-sync` to update Markdown text with new code logic and variable names.
3.  **Visual Sync**: Triggers `ui-doc-sync` to capture new screenshots for modified UI components or explicitly defined recipes.

## Best Practices

- **Dev Server**: Ensure your local development server is running if UI snapshots are expected.
- **Holistic Review**: Use the pipeline for a complete sweep of the project, especially before a release or after major refactoring.
