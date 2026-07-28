from __future__ import annotations

from living_docs.models import LivingDocsConfig
from living_docs.routes import resolve_route


def test_custom_mapping_and_next_routes():
    config = LivingDocsConfig.model_validate(
        {
            "base_url": "http://localhost:3000",
            "mappings": [
                {
                    "pattern": r"src/components/(.*)\.tsx",
                    "urls": ["/preview/{1}"],
                }
            ],
        }
    )
    assert resolve_route("src/components/Card.tsx", config) == [
        {
            "route": "/preview/Card",
            "url": "http://localhost:3000/preview/Card",
        }
    ]
    assert resolve_route("src/app/(admin)/users/[id]/page.tsx", config)[0]["route"] == (
        "/users/[id]"
    )
    assert resolve_route("src/pages/help/index.tsx", config)[0]["route"] == "/help"
