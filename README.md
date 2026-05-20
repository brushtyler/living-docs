# Living Docs

**The Automated Documentation Pipeline for Gemini CLI**

*Documentation that stays in sync with code logic and UI visuals.*

## Overview

Living Docs is a coordinated pipeline that bridges the gap between codebase changes and documentation accuracy. All capabilities are consolidated into a single, high-level skill: **Living Docs**.

The pipeline automates three critical tasks:
1.  **Code-to-Text**: Synchronizing technical logic and API changes with Markdown text.
2.  **Code-to-Recipe**: Automatically discovering where UI components appear (URLs) and how to target them (CSS selectors).
3.  **UI-to-Snapshot**: Regenerating visual assets (screenshots) using a headless browser.

---

## 1. Prerequisites & Setup

### System Requirements
- **Git**: Your project must be a Git repository (used for change detection).
- **Python 3.12+**: Required for analysis and synchronization scripts.
- **Google Chrome / Chromium**: Required for the visual snapshot engine (Selenium).

### Configuration
A `living-docs-config.json` in your project root is **required** for visual synchronization. It must define your local development server's `base_url`.

```json
{
  "base_url": "http://localhost:3000"
}
```

*If the configuration is missing, the AI agent is instructed to help you discover the correct URL and create the file.*

### Installation
To install the Living Docs skill into your Gemini CLI workspace:

```bash
gemini skills install living-docs/ --scope workspace
/skills reload
```

---

## 2. How to Use the Pipeline

### Standard Sync
Simply ask the Gemini CLI:
> "Update my documentation to reflect the latest changes in the codebase."

This single command triggers a coordinated workflow:
- **Detection**: Identifies stale documents and relevant code changes.
- **Text Sync**: Updates Markdown content with technical details.
- **Visual Discovery**: Automatically suggests `snapshot-recipes` for new/updated UI components.
- **Image Sync**: Triggers the visual capture of screenshots.

*Note: Visual synchronization requires your local development server to be running (e.g., `npm run dev`).*

---

## 3. Project Configuration

To enable advanced features or support custom frameworks, create a `living-docs-config.json` in your project root.

```json
{
  "base_url": "http://localhost:3000",
  "flows": {
    "login": [
      {"action": "goto", "url": "/login"},
      {"action": "type", "selector": "#user", "text": "admin"},
      {"action": "type", "selector": "#pass", "text": "password"},
      {"action": "click", "selector": "#submit"},
      {"action": "wait", "seconds": 2}
    ]
  },
  "mappings": [
    {
      "description": "User Components",
      "pattern": "src/components/user/(.*)\\.tsx",
      "urls": ["/profile", "/settings"]
    }
  ]
}
```

---

## 4. Preparing Your Documentation (Recipes)

To enable **Visual Sync**, add a `snapshot-recipe` HTML comment immediately after an image link in your Markdown files.

### Example Recipe
```markdown
![Login Page](./assets/login.png)
<!-- snapshot-recipe: {
  "prerequisites": ["login"],
  "tasks": [
    {"action": "goto", "url": "/dashboard"},
    {"action": "snapshot_element", "selector": "#dashboard-header", "filename": "assets/dashboard.png"}
  ]
} -->
```

---

## 5. Testing & Sandbox

We provide a **Sandbox Environment** to verify the pipeline.

1.  **Start the Mock Server**:
    ```bash
    python3 sandbox/mock_server.py
    ```
2.  **Trigger Sync**: Ask the CLI to "Update sandbox documentation". 
    *(The agent will use `living-docs/scripts/orchestrator.py`, which looks for `living-docs-config.json` in the root by default.)*
3.  **Verify**: Check `sandbox/docs/assets/sandbox.png` for the updated visual.

For detailed test instructions, see [TESTING.md](./TESTING.md).

---

## License

This repository is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
