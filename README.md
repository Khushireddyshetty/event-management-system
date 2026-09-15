# Intelligent Event Management Platform — Milestones 1–4

A complete event operations platform built with React, Vite, Tailwind CSS, Flask, and SQLite. It covers registration and check-in, venue and speaker operations, intelligent scheduling, sponsorships, incident response, real-time monitoring, and a data-backed Event Intelligence Engine for management decision support.

## What is included

### Milestone 1 — Registration

- Attendee registration with registration ID and unique PIN
- Attendee search, filtering, editing, and deletion
- Manual and PIN-based check-in
- Registration import/export
- Registration analytics and charts
- Optional Gemini-enhanced insights with a safe local fallback

### Milestone 2 — Operations

- Venue and speaker CRUD
- Capacity, facilities, availability, and expertise matching
- Venue and speaker recommendations
- Session scheduling and timeline
- Conflict detection and automatic schedule optimization
- Venue, speaker, and session analytics

### Milestone 3 — Response

- Sponsor management, payment and deliverable tracking
- Sponsor performance and ROI analytics
- Incident management, escalation, assignment, and resolution
- Operational alerts and real-time monitoring
- Sponsorship and Incident Agents using deterministic local rules

### Milestone 4 — Intelligence and enterprise readiness

- **Executive Dashboard** at `/executive-dashboard`
- **Event Intelligence Center** at `/intelligence`
- Database-backed health score from 0–100
- Risk detection for crowd density, check-in congestion, incidents, conflicts, sponsor payments, workload, and alerts
- Actionable recommendations with priority and source module
- Agent orchestration across Venue, Speaker, Sponsorship, and Incident Agents
- 30-second dashboard polling without a full browser reload
- Run Analysis and Refresh actions with loading, error, and empty states
- Safe database migrations, input validation, configurable CORS, and graceful no-AI behavior
- Deterministic demo data on a fresh database; existing rows are never reset or overwritten
- Architecture, API, testing, and deployment documentation in `docs/`

## Architecture

```text
React + Vite + Tailwind
          │
          ▼
       Flask API
          │
          ▼
Event Intelligence Engine ── Agent Orchestrator
          │                    │
          ├── registrations    ├── Venue Agent
          ├── check-ins        ├── Speaker Agent
          ├── venues           ├── Sponsorship Agent
          ├── speakers         └── Incident Agent
          ├── sessions
          ├── sponsors
          ├── incidents
          └── operational alerts
                    │
                    ▼
             SQLite database
```

The intelligence engine reads current operational tables in one analysis pass and applies explainable rules. Analysis snapshots and agent runs are stored in new tables; existing Milestone 1–3 tables remain intact.

## Technology stack

- Python 3.10+ and Flask 3
- SQLite
- React 18, Vite 5, React Router
- Tailwind CSS
- Chart.js and `react-chartjs-2`
- Axios, React Icons, React Toastify
- Optional Google Gemini integration (never required)

## Project structure

```text
event-management-milestone4/
├── backend/
│   ├── app.py
│   ├── database.py
│   ├── intelligence.py
│   ├── orchestrator.py
│   ├── scheduling.py
│   └── routes/
│       ├── attendees.py
│       ├── analytics.py
│       ├── ai_insights.py
│       ├── importexport.py
│       ├── intelligence.py
│       ├── milestone3.py
│       └── operations.py
├── frontend/
│   ├── src/pages/ExecutiveDashboard.jsx
│   ├── src/pages/Intelligence.jsx
│   ├── src/components/
│   ├── package.json
│   └── vite.config.js
├── docs/
├── requirements.txt
├── seed_milestone2.py
├── .env.example
└── README.md
```

## Run locally in VS Code on Windows

Prerequisites: Python 3.10+, Node.js 18+, npm, and VS Code.

### Backend

Open a terminal in the extracted project folder:

```powershell
cd backend
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r ..\requirements.txt
Copy-Item ..\.env.example .env
python app.py
```

The API runs at `http://localhost:5000`.

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### Frontend

Open a second terminal in the project folder:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. Keep the backend terminal running. Vite proxies `/api/*` to `http://localhost:5000/*`.

To create a production frontend bundle:

```powershell
npm run build
```

## Environment variables

Copy `.env.example` to `backend/.env`.

| Variable | Required | Purpose |
|---|---:|---|
| `PORT` | No | Flask port, defaults to `5000` |
| `FLASK_DEBUG` | No | Development reload, defaults to `true` |
| `SECRET_KEY` | No | Flask secret; change it for deployment |
| `CORS_ORIGINS` | No | Comma-separated allowed frontend origins |
| `GEMINI_API_KEY` | No | Optional AI prose enhancement |
| `MAIL_*` | No | Optional registration confirmation email |

The app never crashes when Gemini or SMTP settings are absent. The local, deterministic engine remains active.

## Demo data

On first start, independent sections are seeded only when their table is empty. The demo includes attendees, venues, speakers, sessions, sponsors, incidents, and operational alerts so the new dashboards are useful immediately. Check-in, incident, and payment data intentionally creates meaningful risk signals. Existing records are preserved.

You can also run the original safe operations seed script:

```powershell
python seed_milestone2.py
```

It uses `INSERT OR IGNORE` and does not delete or overwrite records.

## Milestone 4 API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/intelligence/overview` | Fresh complete intelligence snapshot |
| GET | `/intelligence/health` | Health score, status, and summary |
| GET | `/intelligence/kpis` | Overview, venue, speaker, incident, sponsor, and operations KPIs |
| GET | `/intelligence/risks` | Current prioritized risks |
| GET | `/intelligence/recommendations` | Current recommended actions |
| GET | `/intelligence/trends` | Registration and check-in trend |
| GET | `/intelligence/latest` | Latest persisted analysis, or a fresh snapshot |
| POST | `/intelligence/analyze` | Run, persist, and return a complete analysis |
| POST | `/intelligence/refresh` | Alias for a persisted fresh analysis |
| POST | `/orchestrator/analyze` | Run the agent orchestration layer |
| POST | `/orchestrator/run` | Alias for orchestration |
| GET | `/orchestrator/status` | Last analysis and agent activity |

Existing Milestone 1–3 endpoints remain available. See `docs/API.md` for the complete list.

## Testing

The final source ZIP intentionally excludes `node_modules`, virtual environments, generated databases, build output, and caches. After installing dependencies:

```powershell
# Backend smoke test (from project root)
cd backend
python -m py_compile app.py database.py intelligence.py orchestrator.py routes\intelligence.py
python -c "from app import app; print(app.test_client().get('/').status_code); print(app.test_client().get('/intelligence/overview').status_code); print(app.test_client().post('/orchestrator/analyze').status_code)"

# Frontend build
cd ..\frontend
npm run build
```

For the full verification checklist and manual CRUD flow, see `docs/TESTING.md`.

## Production notes

- Use a strong `SECRET_KEY` and explicit `CORS_ORIGINS`.
- Run Flask behind a production WSGI server such as Waitress or Gunicorn.
- Put SQLite on persistent storage and back it up.
- Store Gemini, SMTP, and deployment secrets in environment variables.
- Use a reverse proxy to serve the built frontend and forward API requests.
- Authentication and role-based access are intentionally not forced in this local teaching/demo project; add them before exposing operational data publicly.

## Troubleshooting

- **Frontend cannot reach API:** confirm Flask is running on port 5000 and that the frontend is opened through Vite on port 3000.
- **PowerShell activation denied:** run the `Set-ExecutionPolicy` command above.
- **npm registry error:** the included `frontend/.npmrc` uses the public npm registry. Remove a partially created `node_modules` folder and run `npm install` again.
- **No records shown:** remove only your local `backend/database/events.db` if you want a fresh demo database, then restart Flask. Do not do this if the database contains real data.
- **AI key missing:** expected behavior; the rule-based engine is the default.
