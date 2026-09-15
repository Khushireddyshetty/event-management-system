# Testing and Verification

## Automated smoke checks

From the project root after installing dependencies:

```powershell
cd backend
python -m py_compile app.py database.py intelligence.py orchestrator.py routes\intelligence.py
python -c "from app import app; c=app.test_client(); print(c.get('/').status_code); print(c.get('/intelligence/overview').status_code); print(c.get('/intelligence/kpis').status_code); print(c.post('/orchestrator/analyze').status_code)"
cd ..\frontend
npm run build
```

Expected API codes are `200` for GETs and `200` for the analysis POST.

## Manual end-to-end checklist

- Open Dashboard and confirm registration charts load.
- Register an attendee, then check the attendee in by ID or PIN.
- Search and update an attendee; verify export and import.
- Create or edit a venue and speaker.
- Create a session, inspect conflicts, and run automatic scheduling.
- Open Sponsorships, Incidents, and Real-Time Monitoring.
- Escalate an incident and acknowledge an alert.
- Open Executive Dashboard; confirm health, KPIs, risks, and recommendations come from the API.
- Click Refresh; verify only data refreshes and a timestamp changes.
- Click Run analysis; verify agent activity and a persisted latest analysis.
- Open Event Intelligence; inspect KPI, risk, recommendation, and agent panels.
- Stop the backend and confirm the frontend shows a user-friendly error rather than crashing.
- Start with an empty database and confirm the seeded demo appears.

## Data-change verification

Check in another attendee and refresh `/executive-dashboard`; the check-in count and attendance rate should change. Resolve a critical incident and run analysis; the incident risk and health score should change accordingly.
