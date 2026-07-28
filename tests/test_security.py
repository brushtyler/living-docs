from __future__ import annotations

from pathlib import Path

import pytest

from living_docs.errors import (
    INPUT_PATH_DENIED,
    NAVIGATION_DENIED,
    OUTPUT_PATH_DENIED,
    LivingDocsError,
)
from living_docs.security import (
    ProjectBoundary,
    literal_secret_paths,
    redact,
    resolve_navigation_url,
    substitute_env,
)


def test_project_paths_cannot_escape(tmp_path: Path):
    boundary = ProjectBoundary(tmp_path, "generated")
    with pytest.raises(LivingDocsError) as output_error:
        boundary.output_path("../outside.png")
    assert output_error.value.code == OUTPUT_PATH_DENIED
    with pytest.raises(LivingDocsError) as input_error:
        boundary.input_path("../outside.md", must_exist=False)
    assert input_error.value.code == INPUT_PATH_DENIED
    with pytest.raises(LivingDocsError):
        boundary.output_path(str(tmp_path / "absolute.png"))


def test_output_root_is_enforced(tmp_path: Path):
    boundary = ProjectBoundary(tmp_path, "docs/assets")
    assert boundary.output_path("image.png", relative_to=tmp_path / "docs/assets") == (
        tmp_path / "docs/assets/image.png"
    )
    with pytest.raises(LivingDocsError):
        boundary.output_path("other/image.png")


def test_origins_default_ports_and_cross_origin_denial():
    allowed = ["http://localhost:80"]
    assert (
        resolve_navigation_url("/", base_url="http://localhost", allowed_origins=allowed)
        == "http://localhost/"
    )
    with pytest.raises(LivingDocsError) as error:
        resolve_navigation_url(
            "https://example.com/",
            base_url="http://localhost",
            allowed_origins=allowed,
        )
    assert error.value.code == NAVIGATION_DENIED
    with pytest.raises(LivingDocsError) as invalid:
        resolve_navigation_url(
            "http://localhost:not-a-port/",
            base_url=None,
            allowed_origins=allowed,
        )
    assert invalid.value.code == NAVIGATION_DENIED


def test_secret_substitution_and_redaction(monkeypatch):
    monkeypatch.setenv("TEST_PASSWORD", "resolved-value")
    raw = {
        "password": "${ENV:TEST_PASSWORD}",
        "nested": {"api_key": "literal", "safe": "shown"},
    }
    assert substitute_env(raw)["password"] == "resolved-value"
    assert literal_secret_paths(raw) == ["nested.api_key"]
    assert redact(raw) == {
        "password": "<redacted>",
        "nested": {"api_key": "<redacted>", "safe": "shown"},
    }
