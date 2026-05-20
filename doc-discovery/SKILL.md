---
name: doc-discovery
description: Discover documentation staleness, map codebase changes to UI routes, and suggest CSS selectors for visual synchronization.
---

# Documentation Discovery Skill

This skill provides analytical tools to bridge the gap between your codebase and your documentation. It helps you identify what needs to be updated and where to find the relevant UI components.

## Core Capabilities

- **Staleness Analysis**: Checks Git history to find Markdown files that are "behind" the latest code changes.
- **Route Resolution**: Maps technical file paths (like React components) to live application URLs based on project conventions and configuration.
- **Selector Discovery**: Scans UI source code to suggest the best CSS selectors (IDs, data-testids, or unique classes) for automated snapshots.

## How to Use

Trigger this skill when you want to audit your documentation status or prepare for a sync.
- "Which documentation files are stale?"
- "What is the UI route for this component?"
- "Find the best selector for this element"

### Scripts

This skill exposes several helper scripts:
- `git_helper.py`: Analyzes staleness and retrieves code diffs.
- `resolver.py`: Resolves file paths to URLs.
- `discovery_helper.py`: Suggests component names and CSS selectors.

## Examples

### Check Staleness
```bash
python3 doc-discovery/scripts/git_helper.py staleness
```

### Resolve Route
```bash
python3 doc-discovery/scripts/resolver.py src/app/login/page.tsx
```

### Suggest Selectors
```bash
python3 doc-discovery/scripts/discovery_helper.py src/components/Button.tsx
```
