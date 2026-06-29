import pytest
import subprocess
import time
import os
import json
import requests
from PIL import Image

import sys

# Helper to start mock server
@pytest.fixture(scope="session", autouse=True)
def mock_server():
    process = subprocess.Popen([sys.executable, "tests/mock_server.py"])
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
        [sys.executable, "browser_bot.py", "--tasks", "test_tasks.json"],
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

def test_highlight_action():
    tasks = [
        {"action": "goto", "url": "http://localhost:5000"},
        {"action": "highlight", "selector": "#element-to-snapshot", "style": "spotlight", "color": "rgb(255, 0, 0)"},
        {"action": "snapshot_page", "filename": "highlighted_page.png"},
        {"action": "clear_highlights"},
        {"action": "snapshot_page", "filename": "cleared_page.png"}
    ]
    result = run_browser_bot(tasks)
    assert result.returncode == 0
    assert os.path.exists("highlighted_page.png")
    assert os.path.exists("cleared_page.png")
    os.remove("highlighted_page.png")
    os.remove("cleared_page.png")

def test_updater_filtering():
    # Write a temporary config
    config_data = {
        "base_url": "http://localhost:5000",
        "flows": {}
    }
    with open("test-config.json", "w") as f:
        json.dump(config_data, f)
        
    # Write a temporary Markdown document with two snapshot recipes
    md_content = """# Test Doc
    
![Image One](./test_img1.png)
<!-- snapshot-recipe: {
  "prerequisites": [],
  "tasks": [
    {"action": "goto", "url": "/"},
    {"action": "snapshot_element", "selector": "#header", "filename": "test_img1.png"}
  ]
} -->

![Image Two](./test_img2.png)
<!-- snapshot-recipe: {
  "prerequisites": [],
  "tasks": [
    {"action": "goto", "url": "/"},
    {"action": "snapshot_element", "selector": "#element-to-snapshot", "filename": "test_img2.png"}
  ]
} -->
"""
    with open("test_doc.md", "w") as f:
        f.write(md_content)
        
    try:
        # Run updater filtering for only test_img1.png
        result = subprocess.run(
            [sys.executable, "scripts/updater.py", "--config", "test-config.json", "--dir", ".", "--only-images", "test_img1.png"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        
        # test_img1.png should be generated, but test_img2.png should NOT be
        assert os.path.exists("test_img1.png")
        assert not os.path.exists("test_img2.png")
        
    finally:
        # Cleanup
        if os.path.exists("test-config.json"):
            os.remove("test-config.json")
        if os.path.exists("test_doc.md"):
            os.remove("test_doc.md")
        if os.path.exists("test_img1.png"):
            os.remove("test_img1.png")
        if os.path.exists("test_img2.png"):
            os.remove("test_img2.png")
