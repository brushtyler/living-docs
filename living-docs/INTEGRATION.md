# Integration Guide: Web Snapshot Skill

This document explains how to integrate the Web Snapshot tool into various AI-coding platforms.

## 1. Gemini CLI Integration

The tool is packaged as a Gemini CLI skill, which is the native way to extend Gemini CLI.

### Installation
```bash
gemini skills install living-docs/ --scope workspace
```

### Usage
Once installed, reload the skills:
```bash
/skills reload
```
The AI will now automatically detect the `living-docs` skill when you ask it to "take a screenshot of a component" or "document this web page".

## 2. MCP-compatible Tools (Claude Desktop, Windsurf, Cursor)

The Model Context Protocol (MCP) is the emerging standard for connecting AI models to local tools. You can wrap the `browser_bot.py` in an MCP server.

### Example MCP Server Configuration (Stdio)
If using an MCP Python SDK wrapper:
```python
@mcp.tool()
def take_web_snapshot(tasks_json: str):
    # Call browser_bot.py with the provided JSON
    ...
```

## 3. Cursor / Windsurf (Manual Integration)

For tools that don't natively support `.skill` files but allow executing local scripts:

1.  **Add to context**: Add the `USAGE.md` or `browser_bot.py` to the AI's context (e.g., using `@file` in Cursor).
2.  **Instruction**: Add a rule to your `.cursorrules` or project instructions:
    > "When I ask for a web component screenshot, use the `browser_bot.py` script. Define the interaction steps in a JSON file and run it using the virtual environment in `venv/`."

## 4. GitHub Actions / CI Integration

You can use this tool to automatically generate documentation screenshots on every commit.

```yaml
jobs:
  snapshot:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run Snapshot Bot
        run: python browser_bot.py --tasks docs/screenshots_plan.json
```
