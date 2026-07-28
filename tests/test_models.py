from __future__ import annotations

import pytest
from pydantic import ValidationError

from living_docs.models import LivingDocsConfig, Recipe


@pytest.mark.parametrize(
    "task",
    [
        {"action": "unknown"},
        {"action": "click"},
        {"action": "goto"},
        {"action": "wait_for_text", "selector": "#x"},
    ],
)
def test_actions_require_known_type_and_fields(task):
    with pytest.raises(ValidationError):
        Recipe.model_validate({"tasks": [task]})


@pytest.mark.parametrize("selector", ["", "[broken", "div)", "\"unterminated"])
def test_malformed_selectors_are_rejected(selector):
    with pytest.raises(ValidationError):
        Recipe.model_validate(
            {"tasks": [{"action": "click", "selector": selector}]}
        )


def test_existing_v1_config_defaults_new_sections():
    config = LivingDocsConfig.model_validate(
        {
            "base_url": "http://localhost:3000",
            "flows": {},
            "mappings": [],
        }
    )
    assert config.schema_version == 1
    assert config.security.allowed_origins == ["http://localhost:3000"]
    assert config.browser.window_size == (1920, 1080)


def test_extract_info_legacy_key_remains_compatible():
    recipe = Recipe.model_validate(
        {
            "tasks": [
                {"action": "extract_info", "selector": "h1", "key": "title"}
            ]
        }
    )
    assert recipe.tasks[0].key == "title"
