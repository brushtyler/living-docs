# Testing Living Docs

Install development dependencies:

```bash
python -m pip install -e ".[test]"
```

Run the cross-platform unit, CLI, and MCP protocol suite:

```bash
python -m pytest -m "not browser"
```

Run a real isolated Chrome capture:

```bash
LIVING_DOCS_REAL_BROWSER=1 python -m pytest -m browser
```

On Windows PowerShell:

```powershell
$env:LIVING_DOCS_REAL_BROWSER = "1"
python -m pytest -m browser
```

The browser test serves a temporary local page, exercises navigation, typing,
clicking, waits, highlighting, an element screenshot, metadata extraction, and
driver cleanup. Selenium Manager may download a matching driver unless an
explicit or PATH driver is available.

The unit suite also verifies non-destructive review captures, visual diff
generation, provenance redaction, inferred ownership, duplicate-output
rejection, source-route-to-screenshot impact mapping, `--version`, and
project/global agent installation. Installer tests use temporary home and
project directories and never touch active host configuration.

Build release artifacts:

```bash
python -m build
```

Host smoke checks are listed in [INTEGRATIONS.md](INTEGRATIONS.md). The CI
matrix covers Ubuntu, Windows, macOS Intel, and macOS Apple Silicon.
