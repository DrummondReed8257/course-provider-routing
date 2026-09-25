from __future__ import annotations

import os
from datetime import datetime
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from .routing_client import InfraiError, RoutingClient


class CourseRoutingRequest(BaseModel):
    course_id: str = Field(min_length=1)
    capability: str = Field(min_length=1)
    excluded_provider: str = Field(min_length=1)
    learner_deadline: datetime
    educator_report_id: str = Field(min_length=1)


class CourseRoutingResult(BaseModel):
    course_id: str
    capability: str
    excluded_provider: str
    learner_deadline: datetime
    educator_report_id: str
    routing_updated: bool
    provider_preference: dict[str, Any]


def get_routing_client() -> RoutingClient:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set INFRAI_API_KEY before starting the service")
    return RoutingClient(api_key)


app = FastAPI(title="Course delivery provider routing")


@app.post("/course-delivery/provider-preference", response_model=CourseRoutingResult)
def configure_course_provider(
    request: CourseRoutingRequest,
    client: Annotated[RoutingClient, Depends(get_routing_client)],
) -> CourseRoutingResult:
    try:
        preference = client.set_excluded_provider(
            request.capability,
            request.excluded_provider,
        )
    except InfraiError as exc:
        client_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=client_status,
            detail={"code": exc.code, "error": exc.details},
        ) from exc

    return CourseRoutingResult(
        **request.model_dump(),
        routing_updated=True,
        provider_preference=preference,
    )
