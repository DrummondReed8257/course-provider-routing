from datetime import datetime, timezone

import httpx
from fastapi.testclient import TestClient

from course_delivery.course_service import app, get_routing_client
from course_delivery.routing_client import RoutingClient


def test_course_delivery_excludes_provider_and_keeps_reporting_context() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["payload"] = __import__("json").loads(request.content)
        return httpx.Response(
            200,
            json={
                "ok": True,
                "data": {
                    "capability": "course-content-generation",
                    "exclude": "vendor-under-review",
                },
                "error": None,
                "metadata": {},
            },
        )

    routing = RoutingClient("test-key", transport=httpx.MockTransport(handler))
    app.dependency_overrides[get_routing_client] = lambda: routing
    try:
        response = TestClient(app).post(
            "/course-delivery/provider-preference",
            json={
                "course_id": "checkout-fundamentals",
                "capability": "course-content-generation",
                "excluded_provider": "vendor-under-review",
                "learner_deadline": datetime(2026, 10, 1, 16, 0, tzinfo=timezone.utc).isoformat(),
                "educator_report_id": "weekly-course-ops",
            },
        )
    finally:
        app.dependency_overrides.clear()
        routing.close()

    assert response.status_code == 200
    assert captured == {
        "method": "PUT",
        "path": "/v1/account/routing/set",
        "payload": {
            "capability": "course-content-generation",
            "exclude": "vendor-under-review",
        },
    }
    result = response.json()
    assert result["routing_updated"] is True
    assert result["educator_report_id"] == "weekly-course-ops"
    assert result["learner_deadline"] == "2026-10-01T16:00:00Z"
