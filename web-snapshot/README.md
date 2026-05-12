# Web Snapshot Skill

This skill allows Gemini CLI to automate browser interactions and capture screenshots of web pages or specific UI elements. It is powered by Selenium and designed to assist in documenting UI components, capturing form states, or visual regression testing.

## Aim

The primary goal of this skill is to provide AI agents with a "visual" capability, enabling them to:
- Capture full-page snapshots for documentation.
- Target specific CSS selectors for component-level screenshots.
- Perform multi-step interactions (click, type, wait) before capturing visuals.

## Features

- **Browser Automation**: Navigate to URLs, click buttons, and fill out forms.
- **Surgical Snapshots**: Take screenshots of specific elements using CSS selectors.
- **JSON-based Tasks**: Define complex interaction sequences in a structured format.
- **Easy Integration**: Native support for Gemini CLI and adaptable for MCP-compatible tools.

## Installation

### Prerequisites
- Python 3.12+
- Google Chrome or Chromium installed on the system.

### Install as a Gemini CLI Skill
```bash
gemini skills install web-snapshot.skill --scope workspace
/skills reload
```

## Usage

### Standalone CLI
You can run the underlying bot directly using the provided script:

```bash
python browser_bot.py --tasks tasks.json
```

### Task Definition
Tasks are defined in a JSON array. Example `tasks.json`:

```json
[
  {"action": "goto", "url": "https://example.com"},
  {"action": "type", "selector": "#search", "text": "Gemini CLI"},
  {"action": "click", "selector": "button.submit"},
  {"action": "wait", "seconds": 1},
  {"action": "snapshot_element", "selector": ".results", "filename": "search_results.png"}
]
```

### Supported Actions
- `goto`: Navigate to a URL.
- `click`: Click an element by CSS selector.
- `type`: Enter text into an input field.
- `wait`: Pause for a specified number of seconds.
- `snapshot_page`: Take a full-page screenshot.
- `snapshot_element`: Take a screenshot of a specific element.

## Development

- `browser_bot.py`: The core Selenium script.
- `skills/web-snapshot/SKILL.md`: Skill definition and documentation.
- `tests/`: Integration tests using a mock server.

For more details on integration, see [INTEGRATION.md](./INTEGRATION.md).
For a detailed usage guide, see [USAGE.md](./USAGE.md).
