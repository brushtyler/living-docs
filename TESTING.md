# Testing Guide for Living Docs

This document outlines how to run the test suite for the Living Docs pipeline and its component skills.

## 1. Test Architecture

The project uses **Pytest** for integration and unit testing.
- **Integration Tests**: Located in `web-doc-tools/tests/`. These tests use a mock server to simulate web pages and verify browser automation.
- **Mock Server**: Found at `web-doc-tools/tests/mock_server.py`. It provides a stable target for the Selenium bot.

## 2. Environment Setup

All tests should be run using the primary virtual environment in the project root.

```bash
# From the project root
source venv/bin/activate
```

## 3. Running the Tests

### Visual Sync Integration Tests
The tests in `web-doc-tools` are **location-sensitive** because they resolve paths for the mock server and the `browser_bot.py` script relative to the execution directory.

**Correct way to run:**
```bash
cd web-doc-tools
../venv/bin/pytest -v tests/test_browser_bot.py
```

### Technical Synchronization Checks
The `doc-regen` (pipeline) and `doc-discovery` scripts can be verified by running their respective commands with test data or the `--check-only` flag.

```bash
# Verify pipeline readiness
python3 doc-regen/scripts/orchestrator.py --check-only

# Verify recipe detection (requires a git repo)
python3 doc-discovery/scripts/git_helper.py check-recipes
```

## 4. Common Pitfalls

- **Working Directory**: Running `pytest` from the root will cause the `web-doc-tools` tests to fail as they won't find the `browser_bot.py` or the `tests/mock_server.py` file. Always `cd` into the relevant skill directory if the test uses relative file paths.
- **Port Conflicts**: The mock server uses port **5000**. Ensure this port is not occupied before running tests.
- **Python Path**: The tests are configured to use `sys.executable`. This ensures that sub-processes (like the mock server) use the same virtual environment as the test runner.

## 5. Adding New Tests

When adding new tests, follow these best practices:
1.  **Use Fixtures**: Use the `mock_server` fixture in `conftest.py` or within the test file to handle server lifecycle.
2.  **Avoid Hardcoded Paths**: Use `sys.executable` and `os.path.abspath` to make tests resilient to different execution environments.
3.  **Cleanup**: Ensure temporary task files (e.g., `test_tasks.json`) and generated screenshots are removed after the test run.
