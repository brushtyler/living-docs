# Testing Guide for Living Docs

This document outlines how to run the test suite for the Living Docs pipeline.

## 1. Test Architecture

The project uses **Pytest** for integration and unit testing.
- **Integration Tests**: Located in `living-docs/tests/`. These tests use a mock server to simulate web pages and verify browser automation.
- **Mock Server**: Found at `living-docs/tests/mock_server.py`. It provides a stable target for the Selenium bot.

## 2. Environment Setup

All tests should be run using the primary virtual environment in the project root.

```bash
# From the project root
source venv/bin/activate
```

## 3. Running the Tests

### Visual Sync Integration Tests
The tests in `living-docs` are **location-sensitive** because they resolve paths for the mock server and the `browser_bot.py` script relative to the execution directory.

**Correct way to run:**
```bash
cd living-docs
../venv/bin/pytest -v tests/test_browser_bot.py
```

### Pipeline & Discovery Checks
The master orchestrator and its supporting discovery scripts can be verified by running them with the `--check-only` flag or specific subcommands.

```bash
# Verify pipeline readiness
python3 living-docs/scripts/orchestrator.py --check-only

# Verify staleness detection (requires a git repo)
python3 living-docs/scripts/git_helper.py staleness
```

## 4. Common Pitfalls

- **Working Directory**: Running `pytest` from the root will cause the `living-docs` tests to fail as they won't find the `browser_bot.py` or the `tests/mock_server.py` file. Always `cd` into the relevant skill directory if the test uses relative file paths.
- **Port Conflicts**: The mock server used in tests usually runs on port **5000**. Ensure this port is not occupied before running tests.
- **Python Path**: The tests are configured to use `sys.executable`. This ensures that sub-processes (like the mock server) use the same virtual environment as the test runner.

## 5. Adding New Tests

When adding new tests, follow these best practices:
1.  **Use Fixtures**: Use the `mock_server` fixture to handle server lifecycle.
2.  **Avoid Hardcoded Paths**: Use `sys.executable` and `os.path.abspath` to make tests resilient to different execution environments.
3.  **Cleanup**: Ensure temporary task files and generated screenshots are removed after the test run.
