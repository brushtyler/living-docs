"""Git-backed documentation staleness analysis."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .errors import GIT_UNAVAILABLE, LivingDocsError
from .recipes import find_markdown_files
from .security import project_relative


class GitAnalyzer:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root

    def _git(self, *args: str, check: bool = True) -> str:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=self.project_root,
                check=check,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            message = (
                exc.stderr.strip()
                if isinstance(exc, subprocess.CalledProcessError) and exc.stderr
                else str(exc)
            )
            raise LivingDocsError(GIT_UNAVAILABLE, f"Git command failed: {message}") from exc
        return result.stdout.strip()

    def is_repository(self) -> bool:
        try:
            return self._git("rev-parse", "--is-inside-work-tree") == "true"
        except LivingDocsError:
            return False

    def last_commit(self, relative_path: str) -> str | None:
        commit = self._git("log", "-n", "1", "--pretty=format:%H", "--", relative_path)
        if commit:
            return commit
        roots = self._git("rev-list", "--max-parents=0", "HEAD")
        return roots.splitlines()[0] if roots else None

    def head_revision(self) -> str | None:
        if not self.is_repository():
            return None
        revision = self._git("rev-parse", "HEAD")
        return revision or None

    def changed_files(self, since_commit: str) -> list[str]:
        output = self._git("diff", "--name-only", since_commit)
        return [line.replace("\\", "/") for line in output.splitlines() if line]

    def staleness(self) -> list[dict[str, object]]:
        if not self.is_repository():
            raise LivingDocsError(GIT_UNAVAILABLE, "project root is not a Git repository")
        results: list[dict[str, object]] = []
        for markdown in find_markdown_files(self.project_root):
            relative = project_relative(markdown, self.project_root)
            commit = self.last_commit(relative)
            if not commit:
                continue
            changed = self.changed_files(commit)
            if changed:
                results.append(
                    {
                        "file": relative,
                        "last_commit": commit,
                        "changes_count": len(changed),
                        "changed_files": changed,
                    }
                )
        return results
