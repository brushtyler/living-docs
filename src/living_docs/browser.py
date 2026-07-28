"""Selenium execution service with filesystem and network boundaries."""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable, Iterable
from urllib.parse import urlsplit, urlunsplit

from PIL import Image
from pydantic import ValidationError
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.selenium_manager import SeleniumManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .doctor import discover_browser, discover_driver
from .errors import (
    BROWSER_UNAVAILABLE,
    CANCELLED,
    CAPTURE_FAILED,
    ELEMENT_TIMEOUT,
    INVALID_RECIPE,
    LivingDocsError,
)
from .models import (
    Action,
    Artifact,
    CaptureProvenance,
    ElementMetadata,
    LivingDocsConfig,
    Recipe,
    RecipeRecord,
    SyncOutcome,
)
from .review import ReviewWorkspace
from .security import (
    ProjectBoundary,
    project_relative,
    resolve_navigation_url,
    substitute_env,
)

LOGGER = logging.getLogger(__name__)
ProgressCallback = Callable[[int, int, str], None]
OutputMapper = Callable[[Path], Path]


class CancellationToken:
    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    def raise_if_cancelled(self) -> None:
        if self._event.is_set():
            raise LivingDocsError(CANCELLED, "operation was cancelled")

    def wait(self, seconds: float) -> None:
        if self._event.wait(seconds):
            self.raise_if_cancelled()


@dataclass(slots=True)
class CaptureData:
    artifacts: list[Artifact]
    metadata: list[ElementMetadata]
    provenance: CaptureProvenance


class DriverFactory:
    def __init__(self, config: LivingDocsConfig) -> None:
        self.config = config

    @staticmethod
    def _existing_explicit(value: str | None, label: str) -> str | None:
        if value is None:
            return None
        path = Path(value).expanduser().resolve()
        if not path.is_file():
            raise LivingDocsError(
                BROWSER_UNAVAILABLE,
                f"configured {label} does not exist: {value}",
            )
        return str(path)

    def create(self) -> webdriver.Chrome:
        browser = self._existing_explicit(
            self.config.browser.binary_path,
            "browser.binary_path",
        ) or discover_browser(self.config)
        driver_path = self._existing_explicit(
            self.config.browser.driver_path,
            "browser.driver_path",
        ) or discover_driver(self.config)

        if self.config.browser.offline and (not browser or not driver_path):
            try:
                paths = SeleniumManager().binary_paths(
                    ["--browser", "chrome", "--offline"]
                )
                browser = browser or paths.get("browser_path")
                driver_path = driver_path or paths.get("driver_path")
            except Exception as exc:
                raise LivingDocsError(
                    BROWSER_UNAVAILABLE,
                    "offline mode requires explicit, PATH, or Selenium-cached Chrome and ChromeDriver",
                ) from exc
            if not browser or not driver_path:
                raise LivingDocsError(
                    BROWSER_UNAVAILABLE,
                    "offline mode requires explicit, PATH, or Selenium-cached Chrome and ChromeDriver",
                )

        options = ChromeOptions()
        if self.config.browser.headless:
            options.add_argument("--headless=new")
        width, height = self.config.browser.window_size
        options.add_argument(f"--window-size={width},{height}")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        if browser:
            options.binary_location = browser

        service = ChromeService(executable_path=driver_path) if driver_path else ChromeService()
        try:
            return webdriver.Chrome(service=service, options=options)
        except WebDriverException as exc:
            raise LivingDocsError(
                BROWSER_UNAVAILABLE,
                "Chrome could not be started; run `living-docs doctor` for diagnostics",
                {"selenium_error": str(exc).splitlines()[0]},
            ) from exc


class BrowserRunner:
    def __init__(
        self,
        project_root: Path,
        config: LivingDocsConfig,
        boundary: ProjectBoundary,
    ) -> None:
        self.project_root = project_root
        self.config = config
        self.boundary = boundary
        self.factory = DriverFactory(config)
        self.base_url = str(config.base_url) if config.base_url else None

    @staticmethod
    def _recipe_fingerprint(recipe: Recipe) -> str:
        payload = json.dumps(
            recipe.model_dump(mode="json"),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
        return hashlib.sha256(payload).hexdigest()

    def _provenance(
        self,
        driver: webdriver.Chrome,
        recipe_sha256: str,
        *,
        source_revision: str | None,
        target_path: str | None,
    ) -> CaptureProvenance:
        capabilities = getattr(driver, "capabilities", {}) or {}
        chrome = capabilities.get("chrome", {})
        driver_version = chrome.get("chromedriverVersion")
        if isinstance(driver_version, str):
            driver_version = driver_version.split()[0]
        current_url = getattr(driver, "current_url", None)
        final_url = None
        if isinstance(current_url, str) and current_url.startswith(("http://", "https://")):
            parsed = urlsplit(current_url)
            # Deliberately omit query strings, fragments, and user information.
            host = parsed.hostname or ""
            if parsed.port:
                host = f"{host}:{parsed.port}"
            final_url = urlunsplit((parsed.scheme, host, parsed.path or "/", "", ""))
        return CaptureProvenance(
            captured_at=datetime.now(UTC).isoformat(),
            recipe_sha256=recipe_sha256,
            target_path=target_path,
            source_revision=source_revision,
            browser_name=capabilities.get("browserName"),
            browser_version=capabilities.get("browserVersion"),
            driver_version=driver_version,
            viewport=self.config.browser.window_size,
            final_url=final_url,
        )

    def _materialize(self, recipe: Recipe) -> Recipe:
        try:
            return Recipe.model_validate(substitute_env(recipe.model_dump(mode="python")))
        except (ValueError, ValidationError) as exc:
            raise LivingDocsError(INVALID_RECIPE, f"invalid recipe secret reference: {exc}") from exc

    def prepare_recipe(self, recipe: Recipe, relative_to: Path | None = None) -> list[Action]:
        recipe = self._materialize(recipe)
        tasks: list[Action] = []
        for name in recipe.prerequisites:
            if name not in self.config.flows:
                raise LivingDocsError(
                    INVALID_RECIPE,
                    f"prerequisite flow is unavailable: {name}",
                )
            tasks.extend(self.config.flows[name])
        tasks.extend(recipe.tasks)

        produced_sessions: set[Path] = set()
        for task in tasks:
            action = task.action
            if action == "goto":
                resolve_navigation_url(
                    task.url,
                    base_url=self.base_url,
                    allowed_origins=self.config.security.allowed_origins,
                )
            elif action in {"snapshot", "snapshot_page", "snapshot_element", "save_session"}:
                resolved = self.boundary.output_path(task.filename, relative_to=relative_to)
                if action == "save_session":
                    produced_sessions.add(resolved)
            elif action == "restore_session":
                session = self.boundary.output_path(task.filename, relative_to=relative_to)
                if session not in produced_sessions and not session.exists():
                    raise LivingDocsError(
                        INVALID_RECIPE,
                        f"session file is unavailable: {task.filename}",
                    )
        return tasks

    def _allowed_url(self, value: str) -> str:
        return resolve_navigation_url(
            value,
            base_url=self.base_url,
            allowed_origins=self.config.security.allowed_origins,
        )

    @staticmethod
    def _wait_until(
        driver: webdriver.Chrome,
        timeout: float,
        condition: Callable[[webdriver.Chrome], object],
        token: CancellationToken,
    ) -> object:
        def cancellable(current: webdriver.Chrome) -> object:
            token.raise_if_cancelled()
            return condition(current)

        return WebDriverWait(driver, timeout, poll_frequency=0.2).until(cancellable)

    @staticmethod
    def _network_idle(
        driver: webdriver.Chrome,
        token: CancellationToken,
        timeout: float = 10,
        idle_time: float = 0.5,
    ) -> None:
        token.wait(0.1)
        started = time.monotonic()
        last_count = driver.execute_script(
            "return window.performance.getEntriesByType('resource').length"
        )
        last_activity = time.monotonic()
        while time.monotonic() - started < timeout:
            token.raise_if_cancelled()
            count = driver.execute_script(
                "return window.performance.getEntriesByType('resource').length"
            )
            if count != last_count:
                last_count = count
                last_activity = time.monotonic()
            if time.monotonic() - last_activity >= idle_time:
                return
            token.wait(0.1)

    def _assert_current_origin(self, driver: webdriver.Chrome) -> None:
        if driver.current_url and not driver.current_url.startswith(("about:", "data:")):
            self._allowed_url(driver.current_url)

    def _artifact(self, path: Path) -> Artifact:
        try:
            with Image.open(path) as image:
                width, height = image.size
                image.verify()
        except Exception as exc:
            raise LivingDocsError(
                CAPTURE_FAILED,
                f"invalid image artifact: {project_relative(path, self.project_root)}",
            ) from exc
        return Artifact(
            path=project_relative(path, self.project_root),
            kind="image",
            media_type="image/png",
            width=width,
            height=height,
        )

    def _save_session(self, driver: webdriver.Chrome, path: Path) -> None:
        current_url = driver.current_url
        local_storage: dict[str, str] = {}
        session_storage: dict[str, str] = {}
        if current_url and not current_url.startswith(("about:", "data:")):
            local_storage = driver.execute_script(
                "return Object.assign({}, window.localStorage);"
            ) or {}
            session_storage = driver.execute_script(
                "return Object.assign({}, window.sessionStorage);"
            ) or {}
        payload = {
            "origin": current_url,
            "cookies": driver.get_cookies(),
            "local_storage": local_storage,
            "session_storage": session_storage,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
        try:
            path.chmod(0o600)
        except OSError:
            pass

    def _restore_session(self, driver: webdriver.Chrome, path: Path) -> None:
        payload = json.loads(path.read_text(encoding="utf-8"))
        origin = payload.get("origin")
        if origin:
            driver.get(self._allowed_url(origin))
        for cookie in payload.get("cookies", []):
            safe_cookie = {
                key: value
                for key, value in cookie.items()
                if key
                in {
                    "name",
                    "value",
                    "path",
                    "domain",
                    "secure",
                    "httpOnly",
                    "sameSite",
                    "expiry",
                }
            }
            try:
                driver.add_cookie(safe_cookie)
            except WebDriverException:
                continue
        for key, value in payload.get("local_storage", {}).items():
            driver.execute_script(
                "window.localStorage.setItem(arguments[0], arguments[1]);",
                key,
                str(value),
            )
        for key, value in payload.get("session_storage", {}).items():
            driver.execute_script(
                "window.sessionStorage.setItem(arguments[0], arguments[1]);",
                key,
                str(value),
            )

    def _execute_tasks(
        self,
        driver: webdriver.Chrome,
        tasks: Iterable[Action],
        *,
        relative_to: Path | None,
        token: CancellationToken,
        recipe_sha256: str,
        source_revision: str | None = None,
        target_path: str | None = None,
        output_mapper: OutputMapper | None = None,
    ) -> CaptureData:
        artifacts: list[Artifact] = []
        metadata: list[ElementMetadata] = []
        for task in tasks:
            token.raise_if_cancelled()
            action = task.action
            LOGGER.debug("executing browser action %s", action)
            try:
                if action == "goto":
                    driver.get(self._allowed_url(task.url))
                    self._assert_current_origin(driver)
                    self._network_idle(driver, token, idle_time=0.8)
                elif action == "click":
                    element = self._wait_until(
                        driver,
                        task.timeout,
                        EC.element_to_be_clickable((By.CSS_SELECTOR, task.selector)),
                        token,
                    )
                    element.click()
                    self._network_idle(driver, token, idle_time=0.4)
                    self._assert_current_origin(driver)
                elif action == "type":
                    element = self._wait_until(
                        driver,
                        task.timeout,
                        EC.presence_of_element_located((By.CSS_SELECTOR, task.selector)),
                        token,
                    )
                    element.clear()
                    element.send_keys(task.text)
                    self._network_idle(driver, token, idle_time=0.2)
                elif action == "wait":
                    token.wait(task.seconds)
                elif action == "wait_for_selector":
                    self._wait_until(
                        driver,
                        task.timeout,
                        EC.presence_of_element_located((By.CSS_SELECTOR, task.selector)),
                        token,
                    )
                elif action == "wait_for_hidden":
                    self._wait_until(
                        driver,
                        task.timeout,
                        EC.invisibility_of_element_located((By.CSS_SELECTOR, task.selector)),
                        token,
                    )
                elif action == "wait_for_text":
                    self._wait_until(
                        driver,
                        task.timeout,
                        EC.text_to_be_present_in_element(
                            (By.CSS_SELECTOR, task.selector),
                            task.text,
                        ),
                        token,
                    )
                elif action == "highlight":
                    self._wait_until(
                        driver,
                        task.timeout,
                        EC.presence_of_element_located((By.CSS_SELECTOR, task.selector)),
                        token,
                    )
                    driver.execute_script(_HIGHLIGHT_SCRIPT, task.selector, task.style, task.color)
                elif action == "clear_highlights":
                    driver.execute_script(_CLEAR_HIGHLIGHTS_SCRIPT)
                elif action in {"snapshot", "snapshot_page"}:
                    self._network_idle(driver, token)
                    output = self.boundary.output_path(task.filename, relative_to=relative_to)
                    if output_mapper is not None:
                        output = output_mapper(output)
                    output.parent.mkdir(parents=True, exist_ok=True)
                    if not driver.save_screenshot(str(output)):
                        raise LivingDocsError(CAPTURE_FAILED, "page screenshot failed")
                    artifacts.append(self._artifact(output))
                elif action == "snapshot_element":
                    self._network_idle(driver, token)
                    output = self.boundary.output_path(task.filename, relative_to=relative_to)
                    if output_mapper is not None:
                        output = output_mapper(output)
                    output.parent.mkdir(parents=True, exist_ok=True)
                    element = self._wait_until(
                        driver,
                        task.timeout,
                        EC.presence_of_element_located((By.CSS_SELECTOR, task.selector)),
                        token,
                    )
                    if not element.screenshot(str(output)):
                        raise LivingDocsError(CAPTURE_FAILED, "element screenshot failed")
                    artifacts.append(self._artifact(output))
                elif action == "extract_info":
                    element = self._wait_until(
                        driver,
                        task.timeout,
                        EC.presence_of_element_located((By.CSS_SELECTOR, task.selector)),
                        token,
                    )
                    attributes = {}
                    for name in ("aria-label", "alt", "title", "placeholder"):
                        value = element.get_attribute(name)
                        if value:
                            attributes[name] = value
                    metadata.append(
                        ElementMetadata(
                            key=task.key,
                            selector=task.selector,
                            text=element.text,
                            tag=element.tag_name,
                            attributes=attributes,
                        )
                    )
                elif action == "save_session":
                    output = self.boundary.output_path(task.filename, relative_to=relative_to)
                    self._save_session(driver, output)
                elif action == "restore_session":
                    source = self.boundary.output_path(task.filename, relative_to=relative_to)
                    self._restore_session(driver, source)
            except LivingDocsError:
                raise
            except (TimeoutException, NoSuchElementException) as exc:
                raise LivingDocsError(
                    ELEMENT_TIMEOUT,
                    f"element operation timed out during {action}",
                    {"action": action},
                ) from exc
            except WebDriverException as exc:
                raise LivingDocsError(
                    CAPTURE_FAILED,
                    f"browser action failed during {action}",
                    {"selenium_error": str(exc).splitlines()[0]},
                ) from exc
        return CaptureData(
            artifacts=artifacts,
            metadata=metadata,
            provenance=self._provenance(
                driver,
                recipe_sha256,
                source_revision=source_revision,
                target_path=target_path,
            ),
        )

    def capture(
        self,
        recipe: Recipe,
        *,
        relative_to: Path | None = None,
        token: CancellationToken | None = None,
    ) -> CaptureData:
        token = token or CancellationToken()
        tasks = self.prepare_recipe(recipe, relative_to)
        recipe_sha256 = self._recipe_fingerprint(recipe)
        driver = self.factory.create()
        try:
            return self._execute_tasks(
                driver,
                tasks,
                relative_to=relative_to,
                token=token,
                recipe_sha256=recipe_sha256,
            )
        finally:
            try:
                driver.quit()
            except Exception:
                LOGGER.debug("driver cleanup failed", exc_info=True)

    def capture_records(
        self,
        records: list[RecipeRecord],
        *,
        token: CancellationToken,
        progress: ProgressCallback | None = None,
        progress_offset: int = 0,
        progress_total: int | None = None,
        review: bool = False,
        source_revision: str | None = None,
    ) -> list[SyncOutcome]:
        prepared: list[tuple[RecipeRecord, list[Action], Path]] = []
        for record in records:
            source = self.project_root / record.source_file
            relative_to = source.parent
            prepared.append(
                (record, self.prepare_recipe(record.recipe, relative_to), relative_to)
            )

        total = progress_total or len(prepared)
        outcomes: list[SyncOutcome] = []
        driver: webdriver.Chrome | None = None
        executed_flows: set[str] = set()
        review_workspace = (
            ReviewWorkspace(self.project_root, self.boundary) if review else None
        )
        try:
            driver = self.factory.create()
            for index, (record, tasks, relative_to) in enumerate(prepared, start=1):
                token.raise_if_cancelled()
                selected_tasks = tasks
                if self.config.reuse_session and executed_flows:
                    selected_tasks = []
                    cursor = 0
                    for flow_name in record.recipe.prerequisites:
                        flow_length = len(self.config.flows[flow_name])
                        segment = tasks[cursor : cursor + flow_length]
                        if flow_name not in executed_flows:
                            selected_tasks.extend(segment)
                        cursor += flow_length
                    selected_tasks.extend(tasks[cursor:])
                if not self.config.reuse_session:
                    try:
                        driver.delete_all_cookies()
                        if driver.current_url.startswith(("http://", "https://")):
                            driver.execute_script(
                                "window.localStorage.clear(); window.sessionStorage.clear();"
                            )
                    except WebDriverException:
                        pass
                try:
                    target = self.boundary.output_path(
                        record.image_path,
                        relative_to=relative_to,
                    )
                    target_path = project_relative(target, self.project_root)
                    mapped_outputs: dict[Path, Path] = {}

                    def map_review_output(original: Path) -> Path:
                        assert review_workspace is not None
                        candidate = review_workspace.candidate_for(original)
                        mapped_outputs[candidate] = original
                        return candidate

                    captured = self._execute_tasks(
                        driver,
                        selected_tasks,
                        relative_to=relative_to,
                        token=token,
                        recipe_sha256=self._recipe_fingerprint(record.recipe),
                        source_revision=source_revision,
                        target_path=target_path,
                        output_mapper=map_review_output if review else None,
                    )
                    executed_flows.update(record.recipe.prerequisites)
                    artifacts = list(captured.artifacts)
                    reviews = []
                    if review_workspace is not None:
                        artifacts = []
                        for candidate, original in mapped_outputs.items():
                            detail, review_artifacts = review_workspace.compare(
                                original,
                                candidate,
                            )
                            reviews.append(detail)
                            artifacts.extend(review_artifacts)
                    outcomes.append(
                        SyncOutcome(
                            recipe_id=record.recipe_id,
                            source_file=record.source_file,
                            image_path=record.image_path,
                            target_path=target_path,
                            ok=True,
                            artifacts=artifacts,
                            provenance=captured.provenance,
                            reviews=reviews,
                        )
                    )
                except LivingDocsError as exc:
                    target_path = project_relative(
                        self.boundary.output_path(
                            record.image_path,
                            relative_to=relative_to,
                        ),
                        self.project_root,
                    )
                    outcomes.append(
                        SyncOutcome(
                            recipe_id=record.recipe_id,
                            source_file=record.source_file,
                            image_path=record.image_path,
                            target_path=target_path,
                            ok=False,
                            error={
                                "code": exc.code,
                                "message": exc.message,
                                "details": exc.details,
                            },
                        )
                    )
                if progress:
                    progress(
                        progress_offset + index,
                        total,
                        f"processed {record.image_path}",
                    )
        finally:
            if driver is not None:
                try:
                    driver.quit()
                except Exception:
                    LOGGER.debug("driver cleanup failed", exc_info=True)
        return outcomes


_HIGHLIGHT_SCRIPT = r"""
const selector = arguments[0], styleType = arguments[1], color = arguments[2];
const el = document.querySelector(selector);
if (!el) return;
el.dataset.livingDocsOutline = el.style.outline || "";
el.dataset.livingDocsOutlineOffset = el.style.outlineOffset || "";
el.dataset.livingDocsBoxShadow = el.style.boxShadow || "";
el.dataset.livingDocsPosition = el.style.position || "";
el.dataset.livingDocsZIndex = el.style.zIndex || "";
if (styleType === "outline") {
  el.style.outline = "4px solid " + color;
  el.style.outlineOffset = "4px";
  el.style.boxShadow = "0 0 10px " + color;
} else if (styleType === "spotlight") {
  el.style.position = "relative";
  el.style.zIndex = "999999";
  el.style.outline = "4px solid " + color;
  el.style.outlineOffset = "4px";
  el.style.boxShadow = "0 0 0 99999px rgba(0,0,0,.5), 0 0 15px " + color;
} else {
  const badge = document.createElement("span");
  badge.className = "living-docs-highlight-badge";
  badge.style.cssText = "position:absolute;top:-8px;left:-8px;width:20px;height:20px;"
    + "border-radius:50%;border:2px solid white;z-index:1000000;background:" + color;
  if (!el.style.position || el.style.position === "static") el.style.position = "relative";
  el.appendChild(badge);
}
"""

_CLEAR_HIGHLIGHTS_SCRIPT = r"""
document.querySelectorAll("[data-living-docs-outline]").forEach(el => {
  el.style.outline = el.dataset.livingDocsOutline;
  el.style.outlineOffset = el.dataset.livingDocsOutlineOffset;
  el.style.boxShadow = el.dataset.livingDocsBoxShadow;
  el.style.position = el.dataset.livingDocsPosition;
  el.style.zIndex = el.dataset.livingDocsZIndex;
  delete el.dataset.livingDocsOutline;
  delete el.dataset.livingDocsOutlineOffset;
  delete el.dataset.livingDocsBoxShadow;
  delete el.dataset.livingDocsPosition;
  delete el.dataset.livingDocsZIndex;
});
document.querySelectorAll(".living-docs-highlight-badge").forEach(el => el.remove());
"""
