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

The tool is executed via `browser_bot.py`:

```bash
python browser_bot.py --tasks <path_to_json>
```

### Task JSON Format
The JSON file must contain a list of actions.

#### Supported Actions:

| Action | Parameters | Example |
| :--- | :--- | :--- |
| `goto` | `url` | `{"action": "goto", "url": "https://google.com"}` |
| `click` | `selector` | `{"action": "click", "selector": "button.submit"}` |
| `type` | `selector`, `text` | `{"action": "type", "selector": "#name", "text": "John"}` |
| `wait` | `seconds` | `{"action": "wait", "seconds": 2}` |
| `snapshot_page` | `filename` | `{"action": "snapshot_page", "filename": "home.png"}` |
| `snapshot_element` | `selector`, `filename` | `{"action": "snapshot_element", "selector": "nav", "filename": "menu.png"}` |

## Error Handling
- **Exit Code 0**: Success.
- **Exit Code 1**: Failure (Element not found, timeout, or navigation error). Error details are printed to `stderr`.

## Tips for AI Agents
- Always start with a `goto` action.
- Use `snapshot_element` for documenting specific UI components (modals, buttons, cards).
- If a click triggers an animation or AJAX load, add a `wait` action (e.g., 1-2 seconds) before taking a snapshot.
