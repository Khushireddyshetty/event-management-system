# API Reference

All endpoints are relative to `http://localhost:5000`. The Vite frontend calls them through `/api`.

## Intelligence

- `GET /intelligence/overview` — complete current snapshot with `event_health`, `health_status`, `kpis`, `risks`, `recommendations`, `agents`, and `trends`.
- `GET /intelligence/health` — health-only response.
- `GET /intelligence/kpis` — grouped KPI response.
- `GET /intelligence/risks` — current rules-based risk list.
- `GET /intelligence/recommendations` — current rules-based recommendations.
- `GET /intelligence/trends` — registration/check-in trend rows.
- `GET /intelligence/latest` — last persisted analysis.
- `POST /intelligence/analyze` — persist a new analysis.
- `POST /intelligence/refresh` — same as analyze.

## Orchestration

- `POST /orchestrator/analyze` and `POST /orchestrator/run` — run the Venue, Speaker, Sponsorship, and Incident agent checks and return the unified result.
- `GET /orchestrator/status` — readiness, last analysis timestamp, and agent activity.

## Existing API groups

Attendees: `/attendees`, `/attendee/<id>`, `/register`, `/update/<id>`, `/delete/<id>`, `/checkin/<id>`, `/undo-checkin/<id>`, `/checkin/pin`.

Analytics: `/analytics`, `/generate-ai`, `/import`, `/export`.

Operations: `/venues`, `/venues/recommend`, `/venues/optimize`, `/speakers`, `/speakers/recommend`, `/sessions`, `/schedule/validate`, `/schedule/conflicts`, `/schedule/auto`, `/analytics/venue`, `/analytics/speaker`, `/analytics/sessions`, `/analytics/operations`.

Milestone 3: `/sponsors`, `/sponsors/analytics`, `/incidents`, `/incidents/<id>/escalate`, `/alerts`, `/alerts/<id>/<action>`, `/monitoring`, `/ai/<kind>`.
