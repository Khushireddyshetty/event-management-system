"""Data-backed Event Intelligence Engine.

The engine deliberately has no dependency on an external AI provider. It
converts the current SQLite operational records into explainable KPIs, risks,
recommendations, trends, and agent findings. Gemini can be added later for
wording, but it is never required for a correct result.
"""

from datetime import datetime
import json

from scheduling import duration_hours, session_conflicts


SEVERITY_RANK = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _safe_float(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _round(value, digits=1):
    return round(_safe_float(value), digits)


def _percent(numerator, denominator):
    return _round((numerator / denominator) * 100, 1) if denominator else 0


def _elapsed_hours(start, end):
    if not start or not end:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return max(0, (datetime.strptime(str(end), fmt) - datetime.strptime(str(start), fmt)).total_seconds() / 3600)
        except ValueError:
            continue
    return None


def _is_open(status):
    return str(status or "").lower() not in {"resolved", "closed", "complete"}


def _trend(conn):
    registrations = [
        dict(row)
        for row in conn.execute(
            """SELECT DATE(registration_date) AS date, COUNT(*) AS count
               FROM attendees
               WHERE registration_date IS NOT NULL
               GROUP BY DATE(registration_date)
               ORDER BY date DESC LIMIT 7"""
        ).fetchall()
    ]
    checkins = [
        dict(row)
        for row in conn.execute(
            """SELECT DATE(checkin_time) AS date, COUNT(*) AS count
               FROM attendees
               WHERE checkin_time IS NOT NULL
               GROUP BY DATE(checkin_time)
               ORDER BY date DESC LIMIT 7"""
        ).fetchall()
    ]
    by_date = {}
    for item in registrations:
        by_date.setdefault(item["date"], {})["registrations"] = item["count"]
    for item in checkins:
        by_date.setdefault(item["date"], {})["checkins"] = item["count"]
    return [
        {"date": date, "registrations": values.get("registrations", 0), "checkins": values.get("checkins", 0)}
        for date, values in sorted(by_date.items())
    ]


def collect_data(conn):
    """Read all operational sources once for one analysis run."""
    attendees = [dict(row) for row in conn.execute("SELECT * FROM attendees").fetchall()]
    venues = [dict(row) for row in conn.execute("SELECT * FROM venues").fetchall()]
    speakers = [dict(row) for row in conn.execute("SELECT * FROM speakers").fetchall()]
    sessions = [dict(row) for row in conn.execute("SELECT * FROM sessions").fetchall()]
    sponsors = [dict(row) for row in conn.execute("SELECT * FROM sponsors").fetchall()]
    incidents = [dict(row) for row in conn.execute("SELECT * FROM incidents").fetchall()]
    alerts = [dict(row) for row in conn.execute("SELECT * FROM operational_alerts").fetchall()]
    return {
        "attendees": attendees,
        "venues": venues,
        "speakers": speakers,
        "sessions": sessions,
        "sponsors": sponsors,
        "incidents": incidents,
        "alerts": alerts,
        "trend": _trend(conn),
    }


def _kpis(conn, data):
    attendees = data["attendees"]
    venues = data["venues"]
    speakers = data["speakers"]
    sessions = data["sessions"]
    sponsors = data["sponsors"]
    incidents = data["incidents"]
    alerts = data["alerts"]

    confirmed = [a for a in attendees if str(a.get("status", "")).lower() != "cancelled"]
    checked_in = [a for a in attendees if str(a.get("status", "")).lower() == "checked_in" or a.get("checked_in")]
    completed_statuses = {"completed", "conducted"}
    conducted = [
        s for s in sessions
        if str(s.get("status", "")).lower() in completed_statuses
        or (s.get("end_time") and str(s["end_time"]) < datetime.now().strftime("%Y-%m-%dT%H:%M"))
    ]
    active_sessions = [s for s in sessions if str(s.get("status", "")).lower() != "cancelled"]
    open_incidents = [i for i in incidents if _is_open(i.get("status"))]
    critical_incidents = [
        i for i in open_incidents
        if str(i.get("priority", "")).lower() == "critical"
        or str(i.get("severity", "")).lower() == "critical"
    ]
    resolved_incidents = [i for i in incidents if not _is_open(i.get("status"))]
    resolution_times = [
        elapsed for incident in resolved_incidents
        for elapsed in [_elapsed_hours(incident.get("created_at"), incident.get("resolution_date"))]
        if elapsed is not None
    ]
    active_sponsors = [s for s in sponsors if s.get("contract_status") in ("Active", "Confirmed")]
    pending_payments = [s for s in sponsors if s.get("payment_status") != "Paid"]
    pending_deliverables = [s for s in sponsors if s.get("deliverable_status") != "Complete"]
    occupied_venue_ids = {s.get("venue_id") for s in active_sessions if s.get("venue_id")}
    expected_by_venue = {}
    for session in active_sessions:
        if session.get("venue_id"):
            expected_by_venue[session["venue_id"]] = expected_by_venue.get(session["venue_id"], 0) + int(session.get("expected_attendees") or 0)
    total_capacity = sum(int(v.get("capacity") or 0) for v in venues)
    expected_capacity = sum(expected_by_venue.values())

    speaker_stats = []
    for speaker in speakers:
        assigned = [s for s in active_sessions if s.get("speaker_id") == speaker.get("id")]
        hours = sum(duration_hours(s.get("start_time"), s.get("end_time")) for s in assigned)
        speaker_stats.append({
            "id": speaker["id"], "name": speaker["name"], "sessions": len(assigned),
            "hours": _round(hours), "rating": _safe_float(speaker.get("rating")),
        })
    conflicts = []
    for session in active_sessions:
        conflicts.extend([
            {"session_id": session["id"], "session": session["title"], **item}
            for item in session_conflicts(conn, session)
        ])

    return {
        "overview": {
            "total_registrations": len(attendees),
            "confirmed_attendees": len(confirmed),
            "checked_in": len(checked_in),
            "attendance_rate": _percent(len(checked_in), len(confirmed)),
            "pending_registrations": max(0, len(confirmed) - len(checked_in)),
            "sessions_conducted": len(conducted),
            "sessions_remaining": max(0, len(active_sessions) - len(conducted)),
            "event_completion": _percent(len(conducted), len(active_sessions)),
        },
        "venue": {
            "total": len(venues), "occupied": len(occupied_venue_ids),
            "available": max(0, len(venues) - len(occupied_venue_ids)),
            "utilization": _percent(len(occupied_venue_ids), len(venues)),
            "capacity_utilization": _percent(expected_capacity, total_capacity),
            "overcrowding_risk": sum(1 for venue in venues if expected_by_venue.get(venue["id"], 0) >= int(venue.get("capacity") or 0) * 0.8),
            "venue_conflicts": sum(1 for item in conflicts if item.get("type") in ("Venue", "Capacity")),
        },
        "speaker": {
            "total": len(speakers),
            "sessions_conducted": sum(item["sessions"] for item in speaker_stats),
            "participation": _percent(sum(1 for item in speaker_stats if item["sessions"]), len(speakers)),
            "average_rating": _round(sum(item["rating"] for item in speaker_stats) / len(speaker_stats), 2) if speaker_stats else 0,
            "max_workload_hours": max((item["hours"] for item in speaker_stats), default=0),
            "schedule_conflicts": sum(1 for item in conflicts if item.get("type") in ("Speaker", "Availability")),
            "workload": speaker_stats,
        },
        "incidents": {
            "total": len(incidents), "open": len(open_incidents),
            "critical": len(critical_incidents),
            "high": sum(1 for i in open_incidents if str(i.get("priority", "")).lower() == "high"),
            "escalated": sum(1 for i in open_incidents if int(i.get("escalation_level") or 0) > 0 or i.get("status") == "Escalated"),
            "resolved": len(resolved_incidents),
            "average_resolution_hours": _round(sum(resolution_times) / len(resolution_times), 1) if resolution_times else 0,
        },
        "sponsors": {
            "total": len(sponsors), "active": len(active_sponsors),
            "revenue": _round(sum(_safe_float(s.get("amount")) for s in sponsors), 2),
            "pending_payments": len(pending_payments),
            "pending_deliverables": len(pending_deliverables),
            "average_performance": _round(sum(_safe_float(s.get("performance_score")) for s in sponsors) / len(sponsors), 1) if sponsors else 0,
            "average_roi": _round(sum(_safe_float(s.get("roi")) for s in sponsors) / len(sponsors), 2) if sponsors else 0,
        },
        "operations": {
            "active_alerts": sum(1 for alert in alerts if _is_open(alert.get("status"))),
            "conflicts": conflicts,
        },
    }


def _health(kpis, risk_count=0):
    overview, venue, speaker, incidents, sponsors, operations = (
        kpis["overview"], kpis["venue"], kpis["speaker"],
        kpis["incidents"], kpis["sponsors"], kpis["operations"],
    )
    components = [
        overview["attendance_rate"] if overview["confirmed_attendees"] else 75,
        max(0, 100 - venue["capacity_utilization"] * 0.35),
        max(0, 100 - incidents["critical"] * 25 - incidents["open"] * 7),
        max(0, 100 - venue["venue_conflicts"] * 12 - speaker["schedule_conflicts"] * 12),
        min(100, sponsors["average_performance"] if sponsors["total"] else 75),
        max(0, 100 - operations["active_alerts"] * 8),
    ]
    # Risk count is a small tie-breaker, while the component scores keep the
    # result explainable and responsive to operational data changes.
    score = max(0, min(100, round(sum(components) / len(components) - min(10, risk_count * 1.5))))
    status = "Healthy" if score >= 80 else "Moderate" if score >= 60 else "At Risk" if score >= 40 else "Critical"
    return score, status


def _risk(title, description, severity, source, action):
    return {
        "title": title, "description": description, "severity": severity,
        "source": source, "detected_at": _now(), "recommended_action": action,
    }


def detect_risks(conn, data, kpis):
    risks = []
    venue_lookup = {v["id"]: v for v in data["venues"]}
    for venue_id, expected in {
        sid: sum(int(s.get("expected_attendees") or 0) for s in data["sessions"] if s.get("venue_id") == sid)
        for sid in venue_lookup
    }.items():
        venue = venue_lookup[venue_id]
        capacity = int(venue.get("capacity") or 0)
        if capacity and expected >= capacity * 0.8:
            risks.append(_risk(
                f"High crowd density expected at {venue['name']}",
                f"{expected} expected attendees are assigned against a capacity of {capacity}.",
                "High" if expected < capacity else "Critical", "Venue Intelligence",
                "Deploy additional check-in staff and review an alternative entry point.",
            ))
    if kpis["incidents"]["critical"]:
        risks.append(_risk(
            "Critical incidents require immediate attention",
            f"{kpis['incidents']['critical']} open critical incident(s) are currently escalated or unresolved.",
            "Critical", "Incident Management", "Escalate the incident owner and keep the operations lead on site.",
        ))
    if kpis["overview"]["pending_registrations"] >= 3:
        risks.append(_risk(
            "Check-in congestion may occur",
            f"{kpis['overview']['pending_registrations']} confirmed attendees have not checked in.",
            "Medium", "Registration & Check-In", "Deploy additional registration staff and send attendee reminders.",
        ))
    if kpis["speaker"]["schedule_conflicts"]:
        risks.append(_risk(
            "Speaker or session conflicts detected",
            f"{kpis['speaker']['schedule_conflicts']} speaker availability or overlap conflict(s) need review.",
            "High", "Schedule Operations", "Review speaker assignments and move one affected session.",
        ))
    if kpis["venue"]["venue_conflicts"]:
        risks.append(_risk(
            "Venue allocation conflicts detected",
            f"{kpis['venue']['venue_conflicts']} venue or capacity conflict(s) were found in the schedule.",
            "High", "Schedule Operations", "Reassign conflicting sessions to an available suitable venue.",
        ))
    overdue = [s["company"] for s in data["sponsors"] if s.get("payment_status") == "Overdue"]
    if overdue:
        risks.append(_risk(
            "Overdue sponsorship payments require follow-up",
            f"Payment follow-up is needed for: {', '.join(overdue)}.",
            "High", "Sponsorship", "Contact the sponsor and update the payment plan.",
        ))
    if kpis["speaker"]["max_workload_hours"] >= 6:
        busiest = max(kpis["speaker"]["workload"], key=lambda item: item["hours"])
        risks.append(_risk(
            "Speaker workload is high",
            f"{busiest['name']} is scheduled for {busiest['hours']} hours across {busiest['sessions']} sessions.",
            "Medium", "Speaker Operations", "Redistribute one session to an available qualified speaker.",
        ))
    if kpis["operations"]["active_alerts"] >= 3:
        risks.append(_risk(
            "Operational alert backlog is growing",
            f"{kpis['operations']['active_alerts']} operational alerts remain active.",
            "Medium", "Real-Time Monitoring", "Acknowledge owners and resolve stale alerts.",
        ))
    risks.sort(key=lambda item: SEVERITY_RANK.get(item["severity"], 9))
    return risks


def build_recommendations(kpis, risks):
    recommendations = []
    for risk in risks:
        recommendations.append({
            "recommendation": risk["recommended_action"],
            "reason": risk["description"],
            "priority": risk["severity"],
            "related_module": risk["source"],
            "suggested_action": risk["recommended_action"],
        })
    # Always provide a useful next step when the event is currently healthy.
    if not recommendations:
        recommendations.append({
            "recommendation": "Continue live monitoring and review the next event checkpoint.",
            "reason": "No material operational risks were detected in the current data snapshot.",
            "priority": "Low", "related_module": "Event Intelligence",
            "suggested_action": "Refresh the intelligence snapshot after the next registration or check-in update.",
        })
    # De-duplicate repeated actions from multiple rule triggers.
    unique = []
    seen = set()
    for item in recommendations:
        key = (item["recommendation"], item["related_module"])
        if key not in seen:
            unique.append(item)
            seen.add(key)
    return unique


def agent_activity(kpis, risks):
    risk_sources = {risk["source"] for risk in risks}
    specs = [
        ("Venue Agent", "Venue Intelligence", "analyzed capacity, utilization, and booking conflicts"),
        ("Speaker Agent", "Speaker Operations", "checked speaker workload and schedule availability"),
        ("Sponsorship Agent", "Sponsorship", "checked sponsor payment and performance data"),
        ("Incident Agent", "Incident Management", "analyzed priority, escalation, and resolution status"),
    ]
    result = []
    for name, source, base in specs:
        relevant = [r for r in risks if r["source"] == source]
        result.append({
            "agent_name": name, "status": "attention_required" if relevant else "completed",
            "last_execution": _now(), "findings": (relevant[0]["description"] if relevant else f"No immediate issue; {base}."),
            "recommendations": [r["recommended_action"] for r in relevant],
            "used": bool(relevant) or source in {"Venue Intelligence", "Speaker Operations", "Sponsorship", "Incident Management"},
        })
    return result


def analyze(conn, persist=True):
    data = collect_data(conn)
    kpis = _kpis(conn, data)
    # First pass identifies risks; health includes a small risk penalty.
    risks = detect_risks(conn, data, kpis)
    score, status = _health(kpis, len(risks))
    recommendations = build_recommendations(kpis, risks)
    agents = agent_activity(kpis, risks)
    summary = (
        f"Event health is {status.lower()} at {score}/100. "
        f"{kpis['overview']['checked_in']} of {kpis['overview']['confirmed_attendees']} confirmed attendees are checked in, "
        f"with {len(risks)} risk(s) detected across the operational modules."
    )
    result = {
        "event_health": score, "health_status": status, "summary": summary,
        "source_mode": "rule-based", "timestamp": _now(), "kpis": kpis,
        "risks": risks, "recommendations": recommendations, "agents": agents,
        "trends": data["trend"],
    }
    if persist:
        save_analysis(conn, result)
    return result


def save_analysis(conn, result):
    cursor = conn.execute(
        """INSERT INTO intelligence_analyses (health_score, health_status, summary, source_mode)
           VALUES (?, ?, ?, ?)""",
        (result["event_health"], result["health_status"], result["summary"], result["source_mode"]),
    )
    analysis_id = cursor.lastrowid
    for risk in result["risks"]:
        conn.execute(
            """INSERT INTO intelligence_risks
               (analysis_id,title,description,severity,source,recommended_action)
               VALUES (?,?,?,?,?,?)""",
            (analysis_id, risk["title"], risk["description"], risk["severity"], risk["source"], risk["recommended_action"]),
        )
    for recommendation in result["recommendations"]:
        conn.execute(
            """INSERT INTO intelligence_recommendations
               (analysis_id,recommendation,reason,priority,related_module,suggested_action)
               VALUES (?,?,?,?,?,?)""",
            (analysis_id, recommendation["recommendation"], recommendation["reason"],
             recommendation["priority"], recommendation["related_module"], recommendation["suggested_action"]),
        )
    for agent in result["agents"]:
        conn.execute(
            """INSERT INTO agent_runs
               (analysis_id,agent_name,status,findings,recommendations)
               VALUES (?,?,?,?,?)""",
            (analysis_id, agent["agent_name"], agent["status"], agent["findings"], json.dumps(agent["recommendations"])),
        )
    conn.commit()
    result["analysis_id"] = analysis_id
