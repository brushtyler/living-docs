from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from living_docs.browser import BrowserRunner, CancellationToken, DriverFactory
from living_docs.errors import BROWSER_UNAVAILABLE, CANCELLED, LivingDocsError
from living_docs.models import LivingDocsConfig, Recipe
from living_docs.security import ProjectBoundary


class FakeDriver:
    def __init__(self) -> None:
        self.quit_called = False

    def quit(self) -> None:
        self.quit_called = True


def test_cancellation_stops_between_actions_and_quits_driver(
    tmp_path: Path,
    monkeypatch,
):
    config = LivingDocsConfig()
    runner = BrowserRunner(tmp_path, config, ProjectBoundary(tmp_path))
    driver = FakeDriver()
    monkeypatch.setattr(runner.factory, "create", lambda: driver)
    recipe = Recipe.model_validate(
        {"tasks": [{"action": "wait", "seconds": 10}]}
    )
    token = CancellationToken()
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(runner.capture, recipe, token=token)
        time.sleep(0.05)
        token.cancel()
        with pytest.raises(LivingDocsError) as error:
            future.result(timeout=2)
    assert error.value.code == CANCELLED
    assert driver.quit_called


def test_offline_mode_fails_without_path_or_cache(monkeypatch):
    config = LivingDocsConfig.model_validate({"browser": {"offline": True}})
    factory = DriverFactory(config)
    monkeypatch.setattr("living_docs.browser.discover_browser", lambda _config: None)
    monkeypatch.setattr("living_docs.browser.discover_driver", lambda _config: None)

    def unavailable(_self, _args):
        raise RuntimeError("no cache")

    monkeypatch.setattr(
        "living_docs.browser.SeleniumManager.binary_paths",
        unavailable,
    )
    with pytest.raises(LivingDocsError) as error:
        factory.create()
    assert error.value.code == BROWSER_UNAVAILABLE
