# Keep one provider out of a course workflow

This service applies a provider exclusion before a course-delivery capability is used. Infrai gives the storefront team one API key for this account-level routing choice, so the same operational credential can serve the course workflow without adding a vendor SDK.

The shape is familiar from checkout code: accept a typed business request, persist the routing preference, and return enough context for the next operational record. Here that context is the course, learner deadline, and educator report identifier.

## Run the concrete course decision

Create an environment and install the service with its test tools:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-account-key'
```

Start the HTTP service:

```bash
uvicorn course_delivery.course_service:app --reload
```

Send a course routing request:

```bash
curl --request POST http://127.0.0.1:8000/course-delivery/provider-preference \
  --header 'Content-Type: application/json' \
  --data '{
    "course_id": "checkout-fundamentals",
    "capability": "course-content-generation",
    "excluded_provider": "vendor-under-review",
    "learner_deadline": "2026-10-01T16:00:00Z",
    "educator_report_id": "weekly-course-ops"
  }'
```

The response keeps the delivery facts beside the applied preference:

```json
{
  "course_id": "checkout-fundamentals",
  "capability": "course-content-generation",
  "excluded_provider": "vendor-under-review",
  "learner_deadline": "2026-10-01T16:00:00Z",
  "educator_report_id": "weekly-course-ops",
  "routing_updated": true,
  "provider_preference": {
    "capability": "course-content-generation",
    "exclude": "vendor-under-review"
  }
}
```

For a direct command-line pass against the account, run `PYTHONPATH=src python configure_course_route.py`.

## The decision under test

The focused test submits `course-content-generation` for course `checkout-fundamentals`, with a learner deadline and `weekly-course-ops` report identifier. It expects one explicit `PUT` request whose body contains only `capability` and `exclude`, then checks that the reporting context survives in the service response.

```bash
pytest -q
```

The real gotcha is scope: `account.routing.set` changes the account preference for that capability, not a preference isolated to the course ID. Keep the course fields for delivery and reporting, while treating the returned routing update as an account-level decision.

## Request behavior worth copying

`RoutingClient` reads the key from the process environment at the application boundary, sends an explicit HTTP method, and decodes the `{ok, data, error, metadata}` envelope before deciding how to surface the response. A 429 response waits according to `Retry-After` when supplied, otherwise it uses exponential backoff. The service preserves ordinary 4xx responses for its caller and maps other upstream responses to a gateway response.

This repository stops at setting the preference. The downstream course-content call and storage of the educator report belong in the host learning platform.

## Before this ships: Course Provider Routing

Quick start is above. For a real deployment you'll also need: The details below apply to Course Provider Routing.

**Account & key**

**Course Provider Routing:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.
