import pytest
import subprocess
import time
import os
import json
import requests
from PIL import Image

# Helper to start mock server
@pytest.fixture(scope="session", autouse=True)
def mock_server():
    process = subprocess.Popen(["venv/bin/python3", "tests/mock_server.py"])
    # Wait for server to be ready
    for _ in range(10):
        try:
            requests.get("http://localhost:5000")
            break
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    yield
    process.terminate()

def run_browser_bot(tasks):
    with open("test_tasks.json", "w") as f:
        json.dump(tasks, f)
    
    result = subprocess.run(
        ["venv/bin/python3", "browser_bot.py", "--tasks", "test_tasks.json"],
        capture_output=True,
        text=True
    )
    return result

def test_goto_and_snapshot():
    tasks = [
        {"action": "goto", "url": "http://localhost:5000"},
        {"action": "snapshot_page", "filename": "full_page.png"}
    ]
    result = run_browser_bot(tasks)
    assert result.returncode == 0
    assert os.path.exists("full_page.png")
    # Verify it's a valid image
    with Image.open("full_page.png") as img:
        assert img.size[0] > 0
    os.remove("full_page.png")

def test_click_and_snapshot_element():
    tasks = [
        {"action": "goto", "url": "http://localhost:5000"},
        {"action": "click", "selector": "#click-me"},
        {"action": "snapshot_element", "selector": "#header", "filename": "header.png"}
    ]
    result = run_browser_bot(tasks)
    assert result.returncode == 0
    assert os.path.exists("header.png")
    # In a real scenario, we might want to OCR or compare images, 
    # but for now, we'll check existence and basic properties.
    os.remove("header.png")

def test_type_and_wait():
    tasks = [
        {"action": "goto", "url": "http://localhost:5000"},
        {"action": "type", "selector": "#input-field", "text": "Hello Gemini"},
        {"action": "wait", "seconds": 1},
        {"action": "snapshot_page", "filename": "typed.png"}
    ]
    result = run_browser_bot(tasks)
    assert result.returncode == 0
    assert os.path.exists("typed.png")
    os.remove("typed.png")

def test_invalid_selector():
    tasks = [
        {"action": "goto", "url": "http://localhost:5000"},
        {"action": "click", "selector": "#non-existent"}
    ]
    result = run_browser_bot(tasks)
    assert result.returncode != 0
    assert "Element not found" in result.stderr or "error" in result.stderr.lower()
