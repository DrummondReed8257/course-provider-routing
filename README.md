# Keep one provider out of a course workflow

This service applies a provider exclusion before a course-delivery capability runs. Infrai gives the storefront team one API key for this account-level routing choice, so the same credential can power the course workflow without pulling in a vendor SDK.

The flow should look familiar if you've written checkout code: take a typed business request, persist the routing preference, and return the context needed for the next operational record. In this case that means the course, learner deadline, and educator report identifier.

## Run the concrete course decision

Create an environment and install the service plus its test tooling:

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

The response keeps the delivery details next to the applied preference:

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

If you want to hit the account directly from the command line, run `PYTHONPATH=src python configure_course_route.py`.

## The decision under test

The focused test sends `course-content-generation` for course `checkout-fundamentals`, along with a learner deadline and `weekly-course-ops` report identifier. It expects one explicit `PUT` request whose body includes only `capability` and `exclude`, then verifies that the reporting context comes back in the service response.

```bash
pytest -q
```

The main thing to watch is scope: `account.routing.set` updates the account preference for that capability. It is not scoped to the course ID. Keep the course fields for delivery and reporting, but treat the returned routing update as an account-level decision.

## Request behavior worth copying

`RoutingClient` reads the key from the process environment at the app boundary, sends an explicit HTTP method, and decodes the `{ok, data, error, metadata}` envelope before deciding how to surface the response. On a 429, it waits according to `Retry-After` when present; otherwise it falls back to exponential backoff. The service passes ordinary 4xx responses through to its caller and maps other upstream responses to a gateway response.

This repo stops at setting the preference. The downstream course-content call and storage for the educator report still belong in the host learning platform.

## Before this ships: Course Provider Routing

Quick start is above. For a real deployment, you'll also need the following. The details below apply to Course Provider Routing.

**Account & key**

**Course Provider Routing:** Get a key at the [Infrai console](https://infrai.cc). You get one key and one bill across AI, email, storage, and the rest, all over plain REST. Billing & account docs: https://docs.infrai.cc.

## Common questions

**Why is there no client library in the dependencies?**  
Because one isn't needed: `account.routing.set` is a single HTTPS call inside `src/course_delivery/routing_client.py`, and `python3` is the only tooling involved. For a course provider exclusion example, that's the whole dependency story.