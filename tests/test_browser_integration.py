from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

from living_docs.models import Recipe
from living_docs.runtime import LivingDocsRuntime

pytestmark = pytest.mark.browser


def _free_port() -> int:
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        return int(server.getsockname()[1])


@pytest.mark.skipif(
    os.environ.get("LIVING_DOCS_REAL_BROWSER") != "1",
    reason="set LIVING_DOCS_REAL_BROWSER=1 for a real Chrome capture",
)
def test_real_chrome_capture_and_cleanup(tmp_path: Path):
    (tmp_path / "index.html").write_text(
        """
<!doctype html>
<html><body>
  <input id="name">
  <button id="show" onclick="document.querySelector('#result').textContent='Ready'">Show</button>
  <div id="result">Waiting</div>
</body></html>
""",
        encoding="utf-8",
    )
    port = _free_port()
    config = {
        "base_url": f"http://127.0.0.1:{port}",
        "browser": {"headless": True, "offline": False},
        "security": {
            "allowed_origins": [f"http://127.0.0.1:{port}"],
            "output_root": ".",
        },
    }
    (tmp_path / "living-docs-config.json").write_text(
        json.dumps(config),
        encoding="utf-8",
    )
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "http.server",
            str(port),
            "--bind",
            "127.0.0.1",
        ],
        cwd=tmp_path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(50):
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                    break
            except OSError:
                time.sleep(0.1)
        recipe = Recipe.model_validate(
            {
                "tasks": [
                    {"action": "goto", "url": "/"},
                    {"action": "type", "selector": "#name", "text": "Living Docs"},
                    {"action": "click", "selector": "#show"},
                    {
                        "action": "wait_for_text",
                        "selector": "#result",
                        "text": "Ready",
                    },
                    {
                        "action": "highlight",
                        "selector": "#result",
                        "style": "outline",
                    },
                    {
                        "action": "snapshot_element",
                        "selector": "#result",
                        "filename": "capture.png",
                    },
                    {"action": "clear_highlights"},
                    {"action": "extract_info", "selector": "#result", "key": "result"},
                ]
            }
        )
        result = LivingDocsRuntime(tmp_path).capture(recipe)
        assert result.ok
        assert result.artifacts[0].path == "capture.png"
        assert result.data["metadata"][0]["text"] == "Ready"
        assert result.data["provenance"]["browser_name"] == "chrome"
        assert result.data["provenance"]["final_url"] == (
            f"http://127.0.0.1:{port}/"
        )
        assert (tmp_path / "capture.png").is_file()
    finally:
        server.terminate()
        server.wait(timeout=5)
