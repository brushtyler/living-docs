# Living Docs

**The Automated Documentation Pipeline for Gemini CLI**

*Documentation that stays in sync with code logic and UI visuals.*

## Overview

Living Docs is a coordinated pipeline for Gemini CLI that bridges the gap between codebase changes and documentation accuracy.

> **Note**: This tool is currently optimized for **Web-based UIs** only. It uses Selenium and Chrome to interact with the DOM. See [Future Roadmap](#future-roadmap) for other platforms.

The pipeline automates three critical tasks:
1.  **Code-to-Text**: Synchronizing technical logic and API changes with Markdown text.
2.  **Visual Discovery**: Automatically identifying where UI components appear (URLs) and suggesting recipes for the AI to insert into your docs.
3.  **UI-to-Snapshot**: Regenerating visual assets (screenshots) using a headless browser.

---

## 1. Prerequisites & Setup

### System Requirements
- **Git**: Your project must be a Git repository (used for change detection).
- **Python 3.12+**: Required for analysis and synchronization scripts.
- **Google Chrome / Chromium**: Required for the visual snapshot engine (Selenium).

### Configuration
A `living-docs-config.json` in your project root is **required** for visual synchronization. It defines your local development server's `base_url`.

```json
{ "base_url": "http://localhost:3000" }
```
See the [Configuration Guide](./living-docs/CONFIGURATION.md) for advanced flows and route mappings.

---

## 2. Managing Snapshot Recipes

Snapshot recipes tell the system how to capture a specific UI element. There are two ways to manage them:

### A. Automatic Discovery (AI-Driven)
When you modify a UI component, ask the Gemini CLI:
> "Update the documentation for the changes in Login.tsx"

The AI will automatically:
1.  **Resolve** the component to a URL (using your `mappings` or folder structure).
2.  **Discover** the correct CSS selector for the component.
3.  **Propose** a `snapshot-recipe` block for you to insert into your Markdown file.

### B. Manual Definition
You can manually add recipes by placing an HTML comment immediately after any image link:

```markdown
![Dashboard Page](./assets/dashboard.png)
<!-- snapshot-recipe: {
  "prerequisites": ["login"],
  "tasks": [
    {"action": "goto", "url": "/dashboard"},
    {"action": "snapshot_element", "selector": "#dashboard-header", "filename": "assets/dashboard.png"}
  ]
} -->
```
*See [Usage Guide](./living-docs/USAGE.md) for a full list of supported actions like `wait_for_hidden` and `type`.*

---

## 3. Testing & Sandbox

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

## 4. Future Roadmap

We are working to expand Living Docs beyond the web:
- **Desktop (Electron)**: Direct support for Electron app binaries.
- **Mobile (Appium)**: Integration with mobile simulators for iOS/Android screenshots.
- **Native Desktop**: Support for Windows/macOS native UI hierarchies via platform drivers.

---

## License

This repository is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
