"""Deterministic venue, speaker, and scheduling intelligence.

The application can optionally add Gemini-generated prose later, but all
operational decisions are based on the current SQLite data and these rules.
"""

from datetime import datetime, time
import re


def as_dict(row):
    return dict(row) if row else None


def parse_datetime(value):
    if not value:
        return None
    text = str(value).strip().replace("Z", "")
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def parse_clock(value):
    if not value:
        return None
    text = str(value).strip()
    match = re.match(r"^(\d{1,2}):(\d{2})", text)
    if not match:
        parsed = parse_datetime(text)
        return parsed.time() if parsed else None
    hour, minute = int(match.group(1)), int(match.group(2))
    if hour > 23 or minute > 59:
        return None
    return time(hour, minute)


def overlaps(start_a, end_a, start_b, end_b):
    a_start, a_end = parse_datetime(start_a), parse_datetime(end_a)
    b_start, b_end = parse_datetime(start_b), parse_datetime(end_b)
    return bool(a_start and a_end and b_start and b_end and a_start < b_end and b_start < a_end)


def duration_hours(start, end):
    parsed_start, parsed_end = parse_datetime(start), parse_datetime(end)
    if not parsed_start or not parsed_end:
        return 0
    return max(0, (parsed_end - parsed_start).total_seconds() / 3600)


def csv_values(value):
    return {part.strip().lower() for part in re.split(r"[,;\n|]+", str(value or "")) if part.strip()}


def contains_required(actual, required):
    required_values = csv_values(required)
    actual_values = csv_values(actual)
    if not required_values:
        return True, []
    missing = sorted(required_values - actual_values)
    return not missing, missing


def expertise_score(speaker_expertise, topic, required_expertise):
    speaker_terms = csv_values(speaker_expertise)
    requested = csv_values(required_expertise) | csv_values(topic)
    if not requested:
        return 60
    if not speaker_terms:
        return 0
    exact = len(speaker_terms & requested)
    partial = sum(1 for term in requested if any(term in item or item in term for item in speaker_terms))
    return min(100, round((exact * 70 + max(0, partial - exact) * 20) / max(1, len(requested))))


def within_availability(start_time, end_time, available_start, available_end):
    start, end = parse_datetime(start_time), parse_datetime(end_time)
    window_start, window_end = parse_clock(available_start), parse_clock(available_end)
    if not start or not end or not window_start or not window_end:
        return False
    return start.time() >= window_start and end.time() <= window_end


def speaker_workload(conn, speaker_id, exclude_id=None):
    query = "SELECT * FROM sessions WHERE speaker_id = ? AND status != 'Cancelled'"
    params = [speaker_id]
    if exclude_id:
        query += " AND id != ?"
        params.append(exclude_id)
    rows = conn.execute(query, params).fetchall()
    return sum(duration_hours(row["start_time"], row["end_time"]) for row in rows), rows


def venue_sessions(conn, venue_id, exclude_id=None):
    query = "SELECT * FROM sessions WHERE venue_id = ? AND status != 'Cancelled'"
    params = [venue_id]
    if exclude_id:
        query += " AND id != ?"
        params.append(exclude_id)
    return conn.execute(query, params).fetchall()


def session_conflicts(conn, session, ignore_session_id=None):
    conflicts = []
    session_id = session.get("id")
    if ignore_session_id is None:
        ignore_session_id = session_id

    if session.get("speaker_id"):
        speaker = conn.execute("SELECT * FROM speakers WHERE id = ?", (session["speaker_id"],)).fetchone()
        if not speaker:
            conflicts.append({"type": "Speaker", "severity": "high", "message": "Assigned speaker does not exist."})
        else:
            if not within_availability(session["start_time"], session["end_time"],
                                       speaker["availability_start"], speaker["availability_end"]):
                conflicts.append({
                    "type": "Availability", "severity": "high",
                    "message": f"{speaker['name']} is unavailable during this session.",
                })
            workload, assigned = speaker_workload(conn, speaker["id"], ignore_session_id)
            for other in assigned:
                if overlaps(session["start_time"], session["end_time"], other["start_time"], other["end_time"]):
                    conflicts.append({
                        "type": "Speaker", "severity": "high",
                        "message": f"{speaker['name']} is already scheduled from {other['start_time']} to {other['end_time']}.",
                        "session_id": other["id"],
                    })

    if session.get("venue_id"):
        venue = conn.execute("SELECT * FROM venues WHERE id = ?", (session["venue_id"],)).fetchone()
        if not venue:
            conflicts.append({"type": "Venue", "severity": "high", "message": "Assigned venue does not exist."})
        else:
            start, end = parse_datetime(session["start_time"]), parse_datetime(session["end_time"])
            if not start or not end or start >= end:
                conflicts.append({"type": "Time", "severity": "high", "message": "Start time must be before end time."})
            if int(session.get("expected_attendees") or 0) > venue["capacity"]:
                conflicts.append({
                    "type": "Capacity", "severity": "high",
                    "message": f"Expected attendees ({session.get('expected_attendees')}) exceed {venue['name']} capacity ({venue['capacity']}).",
                })
            if not within_availability(session["start_time"], session["end_time"],
                                       venue["availability_start"], venue["availability_end"]):
                conflicts.append({
                    "type": "Venue Availability", "severity": "high",
                    "message": f"{venue['name']} is unavailable during this session.",
                })
            facilities_ok, missing = contains_required(venue["facilities"], session.get("required_equipment"))
            if not facilities_ok:
                conflicts.append({
                    "type": "Equipment", "severity": "medium",
                    "message": f"{venue['name']} is missing: {', '.join(missing)}.",
                })
            for other in venue_sessions(conn, venue["id"], ignore_session_id):
                if overlaps(session["start_time"], session["end_time"], other["start_time"], other["end_time"]):
                    conflicts.append({
                        "type": "Venue", "severity": "high",
                        "message": f"{venue['name']} is already booked from {other['start_time']} to {other['end_time']}.",
                        "session_id": other["id"],
                    })
    return conflicts


def venue_recommendations(conn, payload):
    expected = int(payload.get("expected_attendees") or 0)
    start_time, end_time = payload.get("start_time"), payload.get("end_time")
    required = payload.get("required_equipment", "")
    requested_type = str(payload.get("session_type") or "").lower()
    exclude_session_id = payload.get("session_id") or payload.get("id")
    recommendations = []
    for row in conn.execute("SELECT * FROM venues ORDER BY name").fetchall():
        venue = dict(row)
        facilities_ok, missing = contains_required(venue["facilities"], required)
        available = within_availability(start_time, end_time, venue["availability_start"], venue["availability_end"]) if start_time and end_time else True
        booked = any(overlaps(start_time, end_time, session["start_time"], session["end_time"])
                     for session in venue_sessions(conn, venue["id"], exclude_session_id)) if start_time and end_time else False
        capacity_score = 100 if venue["capacity"] >= expected and expected else min(100, round(venue["capacity"] / max(1, expected) * 100))
        fit_score = 100 if not expected else max(0, 100 - min(60, max(0, venue["capacity"] - expected) / max(1, expected) * 60))
        score = 0.35 * capacity_score + 0.25 * (100 if facilities_ok else max(0, 100 - 25 * len(missing)))
        score += 0.15 * (100 if available else 0) + 0.15 * (100 if not booked else 0)
        score += 0.10 * (100 if requested_type and requested_type in venue["venue_type"].lower() else 55)
        reasons = []
        if venue["capacity"] >= expected:
            reasons.append(f"capacity fits {expected} attendees")
        else:
            reasons.append(f"capacity is {venue['capacity']} for {expected} attendees")
        if facilities_ok:
            reasons.append("required facilities are available")
        else:
            reasons.append(f"missing {', '.join(missing)}")
        reasons.append("within operating hours" if available else "outside operating hours")
        if booked:
            reasons.append("has an overlapping booking")
        else:
            reasons.append("no overlapping booking")
        venue.update({
            "match_score": max(0, min(100, round(score))),
            "available_for_request": available and not booked,
            "facilities_match": facilities_ok,
            "missing_facilities": missing,
            "reason": "; ".join(reasons),
        })
        recommendations.append(venue)
    recommendations.sort(key=lambda item: (not item["available_for_request"], -item["match_score"], item["capacity"]))
    return recommendations


def speaker_recommendations(conn, payload):
    topic = payload.get("topic", "")
    expertise = payload.get("required_expertise", "")
    start_time, end_time = payload.get("start_time"), payload.get("end_time")
    exclude_session_id = payload.get("session_id") or payload.get("id")
    recommendations = []
    for row in conn.execute("SELECT * FROM speakers ORDER BY name").fetchall():
        speaker = dict(row)
        expertise_match = expertise_score(speaker["expertise"], topic, expertise)
        available = within_availability(start_time, end_time, speaker["availability_start"], speaker["availability_end"]) if start_time and end_time else True
        workload, assigned = speaker_workload(conn, speaker["id"], exclude_session_id)
        conflict = any(overlaps(start_time, end_time, other["start_time"], other["end_time"]) for other in assigned) if start_time and end_time else False
        availability_match = 100 if available and not conflict else 0
        workload_score = max(0, 100 - min(70, round(workload * 12)))
        score = round(expertise_match * 0.50 + availability_match * 0.30 + workload_score * 0.10 + float(speaker["rating"] or 0) / 5 * 100 * 0.10)
        speaker.update({
            "match_score": max(0, min(100, score)),
            "expertise_match": expertise_match,
            "availability_match": availability_match,
            "current_workload_hours": round(workload, 1),
            "assigned_sessions": len(assigned),
            "available_for_request": available and not conflict,
            "reason": f"{expertise_match}% expertise match; " + ("available with no conflict" if available and not conflict else "has an availability or time conflict"),
        })
        recommendations.append(speaker)
    recommendations.sort(key=lambda item: (not item["available_for_request"], -item["match_score"], -float(item["rating"] or 0)))
    return recommendations