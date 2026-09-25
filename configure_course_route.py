from __future__ import annotations

import os
from datetime import datetime, timezone

from course_delivery.course_service import CourseRoutingRequest, configure_course_provider
from course_delivery.routing_client import RoutingClient


def main() -> None:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise SystemExit("Set INFRAI_API_KEY before running this script")

    request = CourseRoutingRequest(
        course_id="checkout-fundamentals",
        capability="course-content-generation",
        excluded_provider="vendor-under-review",
        learner_deadline=datetime(2026, 10, 1, 16, 0, tzinfo=timezone.utc),
        educator_report_id="weekly-course-ops",
    )
    client = RoutingClient(api_key)
    try:
        result = configure_course_provider(request, client)
        print(result.model_dump_json(indent=2))
    finally:
        client.close()


if __name__ == "__main__":
    main()
