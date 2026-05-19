# Adopting Living Docs in Your Project

Living Docs is designed to automate the documentation lifecycle for web projects under active development. This guide explains how to prepare your project for automatic synchronization.

## 1. Prerequisites

To use the full pipeline (text + visual sync), your environment must meet these requirements:
- **Git**: Your project must be a Git repository (used for change detection).
- **Python 3.12+**: Required for the background analysis and synchronization scripts.
- **Google Chrome / Chromium**: Required for the visual snapshot engine.
- **Active Dev Server**: The visual sync requires your application to be running locally (e.g., via `npm run dev`) so the bot can capture screenshots.

## 2. Supported Frontends

### Built-in Support
- **Next.js (App Router)**: Automatically resolves `app/**/page.tsx` to the correct URL paths.
- **Next.js (Pages Router)**: Automatically resolves `pages/**/index.tsx` or `pages/name.tsx`.

### Extensible Support
You can support **any** web framework (React, Vue, Angular, Svelte, or even static HTML) by adding a `doc-sync-config.json` to your project root. This tells the system how to map your source files to your local URLs.

```json
{
  "base_url": "http://localhost:3000",
  "mappings": [
    {
      "description": "User Components",
      "pattern": "src/components/user/(.*)\\.tsx",
      "urls": ["/profile", "/settings"]
    }
  ]
}
```

## 3. Preparing Your Documentation

To enable **Visual Sync**, you must provide the agent with "recipes" inside your Markdown files.

### The Recipe Format
Place a `snapshot-recipe` HTML comment immediately after an image link:

```markdown
![Login Page](./assets/login.png)
<!-- snapshot-recipe: {
  "tasks": [
    {"action": "goto", "url": "http://localhost:3000/login"},
    {"action": "snapshot_element", "selector": "#login-form", "filename": "assets/login.png"}
  ]
} -->
```

### Automation via Discovery
If you don't want to write recipes manually, the `Codebase Documentation Synchronizer` can help. When you ask it to "Update docs", it will:
1. Detect a UI change.
2. Use the `resolver` to find the URL.
3. Use the `discovery_helper` to find a CSS selector.
4. **Propose a new recipe** for you to approve and insert.

## 4. Best Practices for Adoption

- **Stable Selectors**: Use `id` or `data-testid` in your code. This makes the automated recipes more resilient to CSS changes.
- **Component-Level Docs**: Try to document components individually rather than just full pages. This keeps your visual assets small and focused.
- **Consistent Base URL**: Ensure the `base_url` in your `doc-sync-config.json` matches your actual local dev server port.
