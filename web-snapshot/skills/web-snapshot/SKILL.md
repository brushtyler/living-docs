---
name: web-snapshot
description: Automate web browsing and take screenshots of pages or elements for documentation. Use when the user needs to capture UI components, form states, or full-page layouts from a live website.
---

# Web Snapshot Skill

This skill allows you to automate a browser using Selenium to navigate web pages, interact with elements, and take snapshots for documentation.

## Core Capabilities

- **Navigate**: Go to any URL.
- **Interact**: Click buttons, fill forms, and wait for elements.
- **Snapshot**: Capture the entire page or a specific element (by CSS selector).

## How to Use

To use this skill, you must define a list of tasks in a JSON format and pass it to the `run_bot.sh` script.

### Task Schema

A task list is a JSON array of objects, where each object has an `action` and associated parameters:

| Action | Parameters | Description |
| :--- | :--- | :--- |
| `goto` | `url` | Navigates to the specified URL. |
| `click` | `selector` | Clicks the element matching the CSS selector. |
| `type` | `selector`, `text` | Types text into the element matching the CSS selector. |
| `wait` | `seconds` | Pauses execution for the specified number of seconds. |
| `snapshot_page` | `filename` | Saves a screenshot of the entire viewport. |
| `snapshot_element` | `selector`, `filename` | Saves a screenshot of a specific element. |

### Example Workflow

If a user asks to "take a screenshot of the login form on example.com", you should:

1.  Identify the URL and CSS selectors.
2.  Create a JSON file (e.g., `tasks.json`):
    ```json
    [
      {"action": "goto", "url": "https://example.com/login"},
      {"action": "snapshot_element", "selector": "#login-form", "filename": "login_form.png"}
    ]
    ```
3.  Execute the script:
    ```bash
    bash skills/web-snapshot/scripts/run_bot.sh --tasks tasks.json
    ```

## Best Practices

- **Headless Mode**: The browser runs in headless mode by default.
- **Selectors**: Use specific CSS selectors to ensure you capture the correct component.
- **Waiting**: Use the `wait` action if a page or element takes time to load after an interaction.
- **Cleanup**: Temporary task files should be deleted after use.
