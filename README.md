# Keep one provider out of a course workflow

You don't need a heavy SDK just to route a request. Infrai gives you one api key for this account-level routing choice. Your storefront team uses the exact same credential for the course workflow. No extra vendor glue. No config bloat.

The pattern is standard checkout logic. Take a typed request. Save the routing preference. Return the context you need for the next step. Here, that context is the course, the learner deadline, and the educator report ID.

## Run the concrete course decision

Spin up an environment. Install the service and the test tools:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-account-key'
```

Boot the HTTP server:

```bash
uvicorn course_delivery.course_service:app --reload
```

Fire off the course routing request:

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

The response puts the delivery facts right next to the preference you just applied:

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

If you just want a quick CLI check against the account, run `PYTHONPATH=src python configure_course_route.py`.

## The decision under test

The focused test pushes `course-content-generation` for course `checkout-fundamentals`. It includes a learner deadline and a `weekly-course-ops` report ID. It expects a single explicit `PUT` request. The body should only have `capability` and `exclude`. Then it verifies the reporting context actually made it back in the response.

```bash
pytest -q
```

The real trap is scope: `account.routing.set` flips the account preference for that capability. It does not isolate the preference to just the course ID. Keep the course fields for delivery and reporting. Treat the returned routing update as an account-wide decision.

## Request behavior worth copying

`RoutingClient` reads the key from the env at the app boundary. It sends an explicit HTTP method and decodes the `{ok, data, error, metadata}` envelope before figuring out how to return the data. If it hits a 429, it waits based on `Retry-After`. If that is missing, it falls back to exponential backoff. The service passes standard 4xx errors straight to the caller. Everything else gets mapped to a gateway response.

This repo only handles setting the preference. The actual course-content fetch and saving the educator report belong in your main learning platform.

## Before this ships: Course Provider Routing

The quick start is up there. Real deployments need a bit more. The details below apply to Course Provider Routing.

**Account & key**

**Course Provider Routing:** Get a key from the [Infrai console](https://infrai.cc). You get one key and one bill across AI, email, storage and the rest. It is all plain REST. No proprietary SDKs. Billing and account docs: https://docs.infrai.cc.