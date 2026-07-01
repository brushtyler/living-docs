# Usage Guide: Living Docs

Living Docs includes a Selenium-powered browser automation script designed for AI agents to capture website components for documentation.

## Installation

### Prerequisites
- Python 3.12+
- `virtualenv`
- Google Chrome (or Chromium) installed on the system.

### Setup
If you are using it as a standalone script:
1. Create a virtual environment: `virtualenv venv`
2. Activate it: `source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`

## CLI Commands

The browser bot tool is executed via `browser_bot.py`:

```bash
python browser_bot.py --tasks <path_to_json> [--output-metadata <path_to_metadata_json>]
```

### CLI Arguments

- `--tasks`: **(Required)** Path to the JSON file containing the list of tasks or batches.
- `--output-metadata`: Path to a JSON file where extracted metadata (from `extract_info` actions) will be saved.

### Task JSON Format

The JSON file must contain a list of actions or a list of batches (lists of tasks).

#### Batch Execution and Session Isolation

To isolate tests or distinct scenarios, you can define your tasks as a list of batches (an array of arrays of tasks). Between each batch, the browser bot automatically clears all cookies and local storage to prevent session leakage.

Example batch file:
```json
[
  [
    {"action": "goto", "url": "http://localhost:3000/login"},
    {"action": "type", "selector": "#username", "text": "user1"},
    {"action": "type", "selector": "#password", "text": "pass123"},
    {"action": "click", "selector": "#login-btn"}
  ],
  [
    {"action": "goto", "url": "http://localhost:3000/login"},
    {"action": "type", "selector": "#username", "text": "user2"},
    {"action": "type", "selector": "#password", "text": "pass456"},
    {"action": "click", "selector": "#login-btn"}
  ]
]
```

#### Supported Actions

| Action | Parameters | Example | Description |
| :--- | :--- | :--- | :--- |
| `goto` | `url` | `{"action": "goto", "url": "https://google.com"}` | Navigates the browser to the specified URL. |
| `click` | `selector` | `{"action": "click", "selector": "button.submit"}` | Clicks the element matching the selector. |
| `type` | `selector`, `text` | `{"action": "type", "selector": "#name", "text": "John"}` | Enters text into the element matching the selector. |
| `wait` | `seconds` | `{"action": "wait", "seconds": 2}` | Pauses execution for the specified number of seconds. |
| `wait_for_selector` | `selector`, `timeout` | `{"action": "wait_for_selector", "selector": ".card"}` | Waits for the selector to be present in the DOM. |
| `wait_for_hidden` | `selector`, `timeout` | `{"action": "wait_for_hidden", "selector": ".loading"}` | Waits for the selector to become hidden or absent. |
| `wait_for_text` | `selector`, `text`, `timeout` | `{"action": "wait_for_text", "selector": "h1", "text": "Home"}` | Waits for the text to appear inside the element. |
| `snapshot_page` | `filename` | `{"action": "snapshot_page", "filename": "home.png"}` | Captures a full page screenshot. |
| `snapshot_element` | `selector`, `filename` | `{"action": "snapshot_element", "selector": "nav", "filename": "menu.png"}` | Captures a screenshot of the specific element. |
| `highlight` | `selector`, `style`, `color` | `{"action": "highlight", "selector": "#btn", "style": "spotlight", "color": "#ff3366"}` | Highlights an element (style: `outline`, `spotlight`, or `badge`). |
| `clear_highlights` | None | `{"action": "clear_highlights"}` | Clears all highlighted overlays and badges from the page. |
| `extract_info` | `selector` | `{"action": "extract_info", "selector": "#user-profile"}` | Extracts text, tag, and key attributes (aria-label, alt, title, placeholder, value) from the element and appends them to the metadata list. |

---

## Pipeline Orchestration & Selective Syncing

The Living Docs pipeline scripts manage overall documentation sync.

### 1. Master Orchestrator (`scripts/orchestrator.py`)
Checks for stale documents and triggers visual regeneration.
```bash
python scripts/orchestrator.py [--force-sync] [--only-images <images>] [--only-files <files>]
```

### 2. Document Visual Updater (`scripts/updater.py`)
Scans markdown documents and runs the browser bot to update screenshots.
```bash
python scripts/updater.py [--config <config_path>] [--only-images <images>] [--only-files <files>]
```

### Selective Sync Options
Both scripts support the following filters:
- `--only-images`: Comma-separated list of image filenames or paths to update (e.g. `login.png,dashboard.png`).
- `--only-files`: Comma-separated list of Markdown files to scan for recipes (e.g. `README.md,docs/guide.md`).

---

## Error Handling
- **Exit Code 0**: Success.
- **Exit Code 1**: Failure (Element not found, timeout, or navigation error). Error details are printed to `stderr`.

## Tips for AI Agents
- Always start with a `goto` action.
- Use `snapshot_element` for documenting specific UI components (modals, buttons, cards).
- **Stabilization**: Instead of generic `wait` actions, prefer `wait_for_hidden` (to wait for spinners to disappear) or `wait_for_text` (to wait for specific content to load).
- **Network Idle**: The bot automatically waits for the network to be idle after `goto`, `click`, and `type` actions, but explicit waits are more reliable for client-side transitions.
