"""Read-only runtime diagnostics."""

from __future__ import annotations

import os
import platform
import shutil
import socket
import sys
from pathlib import Path
from urllib.parse import urlsplit

import selenium

from .models import LivingDocsConfig

_BROWSERS = (
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "chrome",
    "chrome.exe",
)


def discover_browser(config: LivingDocsConfig) -> str | None:
    if config.browser.binary_path:
        path = Path(config.browser.binary_path).expanduser()
        return str(path) if path.is_file() else None
    for name in _BROWSERS:
        located = shutil.which(name)
        if located:
            return located
    return None


def discover_driver(config: LivingDocsConfig) -> str | None:
    if config.browser.driver_path:
        path = Path(config.browser.driver_path).expanduser()
        return str(path) if path.is_file() else None
    return shutil.which("chromedriver") or shutil.which("chromedriver.exe")


def base_url_ready(base_url: str | None) -> tuple[bool, str | None]:
    if not base_url:
        return False, "base_url is not configured"
    parsed = urlsplit(base_url)
    host = parsed.hostname
    if not host:
        return False, "base_url has no hostname"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=1):
            return True, None
    except OSError as exc:
        return False, str(exc)


def diagnostics(
    project_root: Path,
    config_path: Path,
    config: LivingDocsConfig,
    output_root: Path,
) -> dict[str, object]:
    browser = discover_browser(config)
    driver = discover_driver(config)
    base_ok, base_error = base_url_ready(str(config.base_url) if config.base_url else None)
    output_parent = output_root if output_root.exists() else output_root.parent
    return {
        "python": {
            "version": platform.python_version(),
            "supported": sys.version_info >= (3, 12),
            "executable": sys.executable,
        },
        "platform": {
            "system": platform.system(),
            "machine": platform.machine(),
        },
        "selenium": {
            "version": selenium.__version__,
            "manager_enabled": not config.browser.offline,
        },
        "browser": {
            "ready": bool(browser) or not config.browser.offline,
            "path": browser,
            "source": (
                "explicit"
                if config.browser.binary_path
                else "path"
                if browser
                else "selenium-manager"
            ),
        },
        "driver": {
            "ready": bool(driver) or not config.browser.offline,
            "path": driver,
            "source": (
                "explicit"
                if config.browser.driver_path
                else "path"
                if driver
                else "selenium-manager"
            ),
        },
        "configuration": {
            "ready": config_path.is_file(),
            "path": config_path.relative_to(project_root).as_posix(),
            "schema_version": config.schema_version,
        },
        "output_directory": {
            "ready": output_parent.exists() and os.access(output_parent, os.W_OK),
            "path": output_root.relative_to(project_root).as_posix(),
        },
        "base_url": {
            "ready": base_ok,
            "url": str(config.base_url) if config.base_url else None,
            "error": base_error,
        },
    }
