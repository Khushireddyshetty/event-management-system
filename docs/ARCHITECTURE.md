# Architecture

## Layers

1. React pages call the shared Axios client with `/api` paths.
2. Vite proxies those requests to Flask on port 5000.
3. Flask blueprints keep attendee, operations, Milestone 3, and Milestone 4 APIs separate.
4. `intelligence.py` reads the operational tables once, computes KPIs, detects risks, and builds recommendations.
5. `orchestrator.py` exposes a single coordination facade and records agent activity alongside each analysis.
6. SQLite stores the operational data and append-only intelligence snapshots.

## Intelligence flow

```text
GET overview ───────► collect current tables ─► KPIs ─► risks ─► recommendations
POST analyze ───────► same flow + save snapshot + save agent runs
POST orchestrator ──► same flow through orchestrator facade
```

The engine is deterministic, explainable, and safe without an AI key. It can be enhanced with Gemini wording later without moving operational decisions out of the local rules.

## Database safety

All tables use `CREATE TABLE IF NOT EXISTS`. Milestone 4 adds only `intelligence_analyses`, `intelligence_risks`, `intelligence_recommendations`, and `agent_runs`. Demo inserts are independently guarded by table counts and never delete existing rows.
