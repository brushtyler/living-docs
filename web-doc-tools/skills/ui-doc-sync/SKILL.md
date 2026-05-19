---
name: ui-doc-sync
description: Synchronize documentation screenshots and UI text by syncing with a live website. Use this to ensure visual assets and UI-related text stay accurate.
---

# UI Documentation Sync Skill

This skill synchronizes your Markdown documentation with the current state of a live UI. It handles both image capture (screenshots) and data extraction (text/attributes) to help you keep documentation accurate.

## How it Works

The skill scans your project for Markdown files containing `snapshot-recipe` comments.

### Recipe Format

Place a `snapshot-recipe` comment immediately after a Markdown image link:

```markdown
![Login Form](./assets/login_form.png)
<!-- snapshot-recipe: {
  "tasks": [
    {"action": "goto", "url": "https://example.com/login"},
    {"action": "snapshot_element", "selector": "#login-form", "filename": "assets/login_form.png"},
    {"action": "extract_info", "selector": "#login-form h2"}
  ]
} -->
```

### Automation

When you trigger the sync (e.g., by saying "**regen user documentation**"), the skill will:
1.  Locate all Markdown files.
2.  Extract all `snapshot-recipe` blocks.
3.  Run the `web-snapshot` bot to refresh images and extract UI data.
4.  Provide a report of the extracted data so you can verify if the surrounding documentation text matches the live UI.

## Best Practices

- **Focus on Visuals**: Use this primarily for sections that depend on the UI appearance or specific labels.
- **Relative Paths**: Use paths relative to the Markdown file for image filenames.
- **Selective Sync**: You can ask to sync a specific file or the entire documentation set.
