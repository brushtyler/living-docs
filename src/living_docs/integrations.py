"""Install Living Docs into supported AI coding agents."""

from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from .errors import INIT_FAILED, LivingDocsError
from .models import ErrorDetail, OperationResult, WarningDetail

AgentName = Literal[
    "claude",
    "gemini",
    "codex",
    "copilot",
    "cursor",
    "windsurf",
    "cline",
    "kilocode",
    "antigravity",
    "kimi",
    "pi",
    "hermes",
    "droid",
]

SUPPORTED_AGENTS: tuple[str, ...] = (
    "claude",
    "gemini",
    "codex",
    "copilot",
    "cursor",
    "windsurf",
    "cline",
    "kilocode",
    "antigravity",
    "kimi",
    "pi",
    "hermes",
    "droid",
)

_ALIASES = {
    "claude-code": "claude",
    "github-copilot": "copilot",
    "roo": "cline",
    "roo-code": "cline",
    "kilo": "kilocode",
    "factory": "droid",
}

_STANDARD_MCP = {
    "command": "living-docs-mcp",
    "args": ["--project-root", "."],
}

_BEGIN_CODEX = "# BEGIN living-docs (managed by `living-docs init`)"
_END_CODEX = "# END living-docs (managed by `living-docs init`)"
_CODEX_BLOCK = f"""{_BEGIN_CODEX}
[mcp_servers.living-docs]
command = "living-docs-mcp"
args = ["--project-root", "."]
cwd = "."
{_END_CODEX}
"""


@dataclass(frozen=True, slots=True)
class AgentSpec:
    skill_local: str
    skill_global: str
    mcp_local: str | None
    mcp_global: str | None
    mcp_format: Literal["standard", "copilot", "droid", "kilo", "codex"] | None


_SPECS: dict[str, AgentSpec] = {
    "claude": AgentSpec(
        ".claude/skills/living-docs",
        ".claude/skills/living-docs",
        ".mcp.json",
        ".claude.json",
        "standard",
    ),
    "gemini": AgentSpec(
        ".gemini/skills/living-docs",
        ".gemini/skills/living-docs",
        ".gemini/settings.json",
        ".gemini/settings.json",
        "standard",
    ),
    "codex": AgentSpec(
        ".agents/skills/living-docs",
        ".codex/skills/living-docs",
        ".codex/config.toml",
        ".codex/config.toml",
        "codex",
    ),
    "copilot": AgentSpec(
        ".github/skills/living-docs",
        ".copilot/skills/living-docs",
        ".github/mcp.json",
        ".copilot/mcp-config.json",
        "copilot",
    ),
    "cursor": AgentSpec(
        ".cursor/skills/living-docs",
        ".cursor/skills/living-docs",
        ".cursor/mcp.json",
        ".cursor/mcp.json",
        "standard",
    ),
    "windsurf": AgentSpec(
        ".windsurf/skills/living-docs",
        ".codeium/windsurf/skills/living-docs",
        None,
        ".codeium/windsurf/mcp_config.json",
        "standard",
    ),
    "cline": AgentSpec(
        ".cline/skills/living-docs",
        ".cline/skills/living-docs",
        ".cline/mcp.json",
        ".cline/data/settings/cline_mcp_settings.json",
        "standard",
    ),
    "kilocode": AgentSpec(
        ".kilo/skills/living-docs",
        ".kilo/skills/living-docs",
        ".kilo/kilo.json",
        ".config/kilo/kilo.json",
        "kilo",
    ),
    "kimi": AgentSpec(
        ".kimi-code/skills/living-docs",
        ".kimi-code/skills/living-docs",
        ".kimi-code/mcp.json",
        ".kimi-code/mcp.json",
        "standard",
    ),
    "pi": AgentSpec(
        ".pi/skills/living-docs",
        ".pi/agent/skills/living-docs",
        None,
        None,
        None,
    ),
    "droid": AgentSpec(
        ".factory/skills/living-docs",
        ".factory/skills/living-docs",
        ".factory/mcp.json",
        ".factory/mcp.json",
        "droid",
    ),
}


def normalize_agent(value: str) -> str:
    normalized = _ALIASES.get(value.lower(), value.lower())
    if normalized not in SUPPORTED_AGENTS:
        choices = ", ".join(SUPPORTED_AGENTS)
        raise LivingDocsError(
            INIT_FAILED,
            f"unsupported agent {value!r}; choose one of: {choices}",
        )
    return normalized


def _asset_root() -> Path:
    packaged = Path(__file__).resolve().parent / "integrations"
    if packaged.is_dir():
        return packaged
    source = Path(__file__).resolve().parents[2] / "integrations"
    if source.is_dir():
        return source
    raise LivingDocsError(INIT_FAILED, "packaged integration assets are missing")


def _contained(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


class AgentInstaller:
    """Idempotently install the shared skill and one MCP registration."""

    def __init__(
        self,
        project_root: str | Path,
        *,
        home: str | Path | None = None,
        asset_root: str | Path | None = None,
    ) -> None:
        self.project_root = Path(project_root).expanduser().resolve()
        self.home = (
            Path(home).expanduser().resolve()
            if home is not None
            else Path.home().resolve()
        )
        self.asset_root = (
            Path(asset_root).resolve() if asset_root is not None else _asset_root()
        )
        self._changes: list[dict[str, str]] = []
        self._warnings: list[WarningDetail] = []
        self._dry_run = False

    def install(
        self,
        agent: str,
        *,
        global_scope: bool = False,
        dry_run: bool = False,
    ) -> OperationResult:
        selected = normalize_agent(agent)
        self._changes = []
        self._warnings = []
        self._dry_run = dry_run

        if selected == "antigravity":
            self._install_antigravity(global_scope)
        elif selected == "hermes":
            self._install_hermes(global_scope)
        else:
            self._install_standard(selected, global_scope)

        scope = "global" if global_scope or selected == "hermes" else "project"
        changed = sum(
            item["action"] not in {"unchanged", "would_leave_unchanged"}
            for item in self._changes
        )
        verb = "Would configure" if dry_run else "Configured"
        return OperationResult(
            ok=True,
            summary=f"{verb} Living Docs for {selected} ({scope} scope)",
            data={
                "agent": selected,
                "scope": scope,
                "dry_run": dry_run,
                "changed": changed,
                "files": self._changes,
                "check": "living-docs --version",
                "reload": self._reload_hint(selected),
            },
            warnings=self._warnings,
        )

    def _install_standard(self, agent: str, global_scope: bool) -> None:
        spec = _SPECS[agent]
        root = self.home if global_scope else self.project_root
        skill_relative = spec.skill_global if global_scope else spec.skill_local
        self._write_skill(root / skill_relative, root)

        mcp_relative = spec.mcp_global if global_scope else spec.mcp_local
        if mcp_relative is None:
            message = (
                "Pi has no built-in MCP client; the installed skill uses the "
                "`living-docs` CLI fallback."
                if agent == "pi"
                else "Windsurf exposes MCP configuration only at user scope; "
                "rerun with `-g --agent windsurf` to register the MCP server."
            )
            self._warnings.append(
                WarningDetail(code="MCP_NOT_CONFIGURED", message=message)
            )
            return

        config_path = root / mcp_relative
        if spec.mcp_format == "codex":
            self._merge_codex(config_path, root)
        elif spec.mcp_format == "kilo":
            self._merge_json(
                config_path,
                root,
                key="mcp",
                entry={
                    "type": "local",
                    "command": [
                        "living-docs-mcp",
                        "--project-root",
                        ".",
                    ],
                    "enabled": True,
                },
            )
        else:
            entry = dict(_STANDARD_MCP)
            if spec.mcp_format in {"copilot", "droid"}:
                entry["type"] = "stdio"
            if spec.mcp_format == "droid":
                entry["disabled"] = False
            self._merge_json(
                config_path,
                root,
                key="mcpServers",
                entry=entry,
            )

    def _install_antigravity(self, global_scope: bool) -> None:
        root = self.home if global_scope else self.project_root
        relative = (
            ".gemini/config/plugins/living-docs"
            if global_scope
            else ".agents/plugins/living-docs"
        )
        destination = root / relative
        source = self.asset_root / "antigravity" / "plugin"
        files = (
            "plugin.json",
            "mcp_config.json",
            "skills/living-docs/SKILL.md",
        )
        for relative_file in files:
            source_file = source / relative_file
            if not source_file.is_file():
                raise LivingDocsError(
                    INIT_FAILED,
                    f"Antigravity plugin asset is missing: {relative_file}",
                )
            self._write_text(
                destination / relative_file,
                source_file.read_text(encoding="utf-8"),
                root,
            )

    def _install_hermes(self, global_scope: bool) -> None:
        if not global_scope:
            self._warnings.append(
                WarningDetail(
                    code="GLOBAL_SCOPE_REQUIRED",
                    message=(
                        "Hermes stores skills and MCP servers only in user scope; "
                        "`--agent hermes` therefore installs under ~/.hermes."
                    ),
                )
            )
        self._write_skill(self.home / ".hermes/skills/living-docs", self.home)
        self._merge_hermes_yaml(self.home / ".hermes/config.yaml", self.home)

    def _write_skill(self, destination: Path, root: Path) -> None:
        source = (
            self.asset_root
            / "antigravity"
            / "plugin"
            / "skills"
            / "living-docs"
            / "SKILL.md"
        )
        if not source.is_file():
            raise LivingDocsError(INIT_FAILED, "shared Agent Skill asset is missing")
        self._write_text(
            destination / "SKILL.md",
            source.read_text(encoding="utf-8"),
            root,
        )

    def _merge_json(
        self,
        path: Path,
        root: Path,
        *,
        key: str,
        entry: dict[str, Any],
    ) -> None:
        if path.exists():
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise LivingDocsError(
                    INIT_FAILED,
                    f"cannot safely merge invalid JSON in {self._display(path)}: {exc}",
                ) from exc
            if not isinstance(value, dict):
                raise LivingDocsError(
                    INIT_FAILED,
                    f"{self._display(path)} must contain a JSON object",
                )
        else:
            value = {}

        servers = value.setdefault(key, {})
        if not isinstance(servers, dict):
            raise LivingDocsError(
                INIT_FAILED,
                f"{key} in {self._display(path)} must be a JSON object",
            )
        servers["living-docs"] = entry
        self._write_text(
            path,
            json.dumps(value, indent=2, ensure_ascii=False) + "\n",
            root,
        )

    def _merge_codex(self, path: Path, root: Path) -> None:
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        if _BEGIN_CODEX in existing or _END_CODEX in existing:
            pattern = re.compile(
                rf"{re.escape(_BEGIN_CODEX)}.*?{re.escape(_END_CODEX)}\n?",
                re.DOTALL,
            )
            if not pattern.search(existing):
                raise LivingDocsError(
                    INIT_FAILED,
                    f"managed Living Docs block is malformed in {self._display(path)}",
                )
            updated = pattern.sub(_CODEX_BLOCK, existing, count=1)
        elif re.search(r"(?m)^\s*\[mcp_servers\.living-docs\]\s*$", existing):
            raise LivingDocsError(
                INIT_FAILED,
                (
                    f"{self._display(path)} already contains an unmanaged "
                    "[mcp_servers.living-docs] table; remove or rename it before init"
                ),
            )
        else:
            separator = "" if not existing or existing.endswith("\n\n") else "\n"
            updated = f"{existing}{separator}{_CODEX_BLOCK}"
        self._write_text(path, updated, root)

    def _merge_hermes_yaml(self, path: Path, root: Path) -> None:
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        block = (
            "  living-docs:\n"
            '    command: "living-docs-mcp"\n'
            "    args:\n"
            '      - "--project-root"\n'
            '      - "."\n'
        )
        lines = existing.splitlines(keepends=True)
        section_index = next(
            (
                index
                for index, line in enumerate(lines)
                if line.rstrip("\r\n") == "mcp_servers:"
            ),
            None,
        )
        if section_index is None:
            if re.search(r"(?m)^mcp_servers\s*:", existing):
                raise LivingDocsError(
                    INIT_FAILED,
                    (
                        f"cannot safely merge the inline mcp_servers value in "
                        f"{self._display(path)}"
                    ),
                )
            separator = "" if not existing or existing.endswith("\n\n") else "\n"
            updated = f"{existing}{separator}mcp_servers:\n{block}"
            self._write_text(path, updated, root)
            return

        section_end = len(lines)
        for index in range(section_index + 1, len(lines)):
            stripped = lines[index].strip()
            if stripped and not stripped.startswith("#") and not lines[index][0].isspace():
                section_end = index
                break

        child_start = next(
            (
                index
                for index in range(section_index + 1, section_end)
                if lines[index].rstrip("\r\n") == "  living-docs:"
            ),
            None,
        )
        if child_start is None:
            lines.insert(section_end, block)
        else:
            child_end = section_end
            for index in range(child_start + 1, section_end):
                stripped = lines[index].strip()
                indentation = len(lines[index]) - len(lines[index].lstrip())
                if stripped and not stripped.startswith("#") and indentation <= 2:
                    child_end = index
                    break
            lines[child_start:child_end] = [block]
        self._write_text(path, "".join(lines), root)

    def _write_text(self, path: Path, content: str, root: Path) -> None:
        if not _contained(path, root):
            raise LivingDocsError(
                INIT_FAILED,
                f"installer target escapes its scope root: {path}",
            )
        previous = path.read_text(encoding="utf-8") if path.exists() else None
        if previous == content:
            action = "would_leave_unchanged" if self._dry_run else "unchanged"
        elif previous is None:
            action = "would_create" if self._dry_run else "created"
        else:
            action = "would_update" if self._dry_run else "updated"
        self._changes.append({"path": self._display(path), "action": action})
        if self._dry_run or previous == content:
            return

        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=path.parent,
                prefix=f".{path.name}.",
                delete=False,
            ) as handle:
                temporary = Path(handle.name)
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            temporary.replace(path)
        except OSError as exc:
            if "temporary" in locals():
                temporary.unlink(missing_ok=True)
            raise LivingDocsError(
                INIT_FAILED,
                f"cannot write {self._display(path)}: {exc}",
            ) from exc

    def _display(self, path: Path) -> str:
        resolved = path.resolve()
        if _contained(resolved, self.project_root):
            relative = resolved.relative_to(self.project_root)
            return "." if not relative.parts else relative.as_posix()
        if _contained(resolved, self.home):
            relative = resolved.relative_to(self.home)
            return "~" if not relative.parts else f"~/{relative.as_posix()}"
        return str(resolved)

    @staticmethod
    def _reload_hint(agent: str) -> str:
        hints = {
            "antigravity": "Open /mcp and reload the living-docs plugin.",
            "claude": "Restart Claude Code or run /mcp.",
            "gemini": "Run /skills reload and restart MCP servers.",
            "codex": "Restart Codex so it reloads skills and MCP servers.",
            "copilot": "Restart Copilot CLI or reload the editor workspace.",
            "cursor": "Reload Cursor MCP servers.",
            "windsurf": "Reload Cascade skills and MCP servers.",
            "cline": "Restart Cline or reload MCP servers.",
            "kilocode": "Run /reload or start a new Kilo session.",
            "kimi": "Start a new Kimi session and run /mcp.",
            "pi": "Start a new Pi session; the skill uses the CLI fallback.",
            "hermes": "Run /reload-skills and restart Hermes MCP connections.",
            "droid": "Restart Droid; MCP configuration reloads automatically.",
        }
        return hints[agent]


def init_agent(
    project_root: str | Path,
    *,
    agent: str,
    global_scope: bool = False,
    dry_run: bool = False,
) -> OperationResult:
    """Public service used by the CLI and tests."""

    try:
        return AgentInstaller(project_root).install(
            agent,
            global_scope=global_scope,
            dry_run=dry_run,
        )
    except (LivingDocsError, OSError) as exc:
        if isinstance(exc, LivingDocsError):
            code = exc.code
            message = exc.message
            details = exc.details
        else:
            code = INIT_FAILED
            message = str(exc)
            details = None
        return OperationResult(
            ok=False,
            summary=message,
            errors=[
                ErrorDetail(
                    code=code,
                    message=message,
                    details=details,
                )
            ],
        )
