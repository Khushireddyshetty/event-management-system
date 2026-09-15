"""Milestone 2 operations APIs: venues, speakers, sessions, scheduling, analytics."""

from datetime import datetime
from flask import Blueprint, jsonify, request
from database import get_db
from scheduling import (
    as_dict, duration_hours, expertise_score, parse_datetime, session_conflicts,
    speaker_recommendations, venue_recommendations, overlaps, within_availability,
)

operations_bp = Blueprint("operations", __name__)


def error(message, status=400):
    return jsonify({"error": message}), status


def json_rows(cursor):
    return [dict(row) for row in cursor.fetchall()]


def validate_base_time(data):
    start, end = parse_datetime(data.get("start_time")), parse_datetime(data.get("end_time"))
    if not start or not end or start >= end:
        return "Start time must be a valid date/time before end time."
    return None


@operations_bp.route("/venues", methods=["GET"])
def list_venues():
    conn = get_db()
    rows = json_rows(conn.execute("SELECT * FROM venues ORDER BY name"))
    for venue in rows:
        sessions = conn.execute("SELECT start_time, end_time FROM sessions WHERE venue_id = ? AND status != 'Cancelled'", (venue["id"],)).fetchall()
        venue["session_count"] = len(sessions)
        venue["calculated_utilization"] = round(min(100, sum(duration_hours(s["start_time"], s["end_time"]) for s in sessions) / 14 * 100), 1)
        venue["booking_status"] = "Booked" if sessions else "Open"
    conn.close()
    return jsonify({"venues": rows})


@operations_bp.route("/venues/<int:venue_id>", methods=["GET"])
def get_venue(venue_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM venues WHERE id = ?", (venue_id,)).fetchone()
    conn.close()
    return jsonify(as_dict(row)) if row else error("Venue not found.", 404)


@operations_bp.route("/venues", methods=["POST"])
def create_venue():
    data = request.get_json(silent=True) or {}
    required = ["name", "capacity", "venue_type", "location"]
    missing = next((field for field in required if not str(data.get(field, "")).strip()), None)
    if missing:
        return error(f"'{missing}' is required.")
    try:
        capacity = int(data["capacity"])
        if capacity <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return error("Capacity must be a positive number.")
    conn = get_db()
    try:
        cursor = conn.execute(
            """INSERT INTO venues
            (name, capacity, venue_type, location, facilities, accessibility,
             availability_start, availability_end, status, utilization)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (data["name"].strip(), capacity, data["venue_type"].strip(), data["location"].strip(),
             data.get("facilities", ""), data.get("accessibility", ""),
             data.get("availability_start", "08:00"), data.get("availability_end", "22:00"),
             data.get("status", "Available"), float(data.get("utilization", 0) or 0)),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM venues WHERE id = ?", (cursor.lastrowid,)).fetchone()
    except Exception as exc:
        conn.rollback()
        conn.close()
        if "UNIQUE" in str(exc).upper():
            return error("A venue with this name already exists.")
        return error("Unable to create venue.")
    conn.close()
    return jsonify(as_dict(row)), 201


@operations_bp.route("/venues/<int:venue_id>", methods=["PUT"])
def update_venue(venue_id):
    data = request.get_json(silent=True) or {}
    required = ["name", "capacity", "venue_type", "location"]
    missing = next((field for field in required if not str(data.get(field, "")).strip()), None)
    if missing:
        return error(f"'{missing}' is required.")
    try:
        capacity = int(data["capacity"])
        if capacity <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return error("Capacity must be a positive number.")
    conn = get_db()
    try:
        conn.execute(
            """UPDATE venues SET name=?, capacity=?, venue_type=?, location=?, facilities=?,
            accessibility=?, availability_start=?, availability_end=?, status=?, utilization=? WHERE id=?""",
            (data["name"].strip(), capacity, data["venue_type"].strip(), data["location"].strip(),
             data.get("facilities", ""), data.get("accessibility", ""),
             data.get("availability_start", "08:00"), data.get("availability_end", "22:00"),
             data.get("status", "Available"), float(data.get("utilization", 0) or 0), venue_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM venues WHERE id = ?", (venue_id,)).fetchone()
    except Exception as exc:
        conn.rollback()
        conn.close()
        if "UNIQUE" in str(exc).upper():
            return error("A venue with this name already exists.")
        return error("Unable to update venue.")
    conn.close()
    return jsonify(as_dict(row)) if row else error("Venue not found.", 404)


@operations_bp.route("/venues/<int:venue_id>", methods=["DELETE"])
def delete_venue(venue_id):
    conn = get_db()
    if conn.execute("SELECT 1 FROM venues WHERE id = ?", (venue_id,)).fetchone() is None:
        conn.close()
        return error("Venue not found.", 404)
    conn.execute("UPDATE sessions SET venue_id = NULL, status = 'Conflict' WHERE venue_id = ?", (venue_id,))
    conn.execute("DELETE FROM venues WHERE id = ?", (venue_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Venue deleted."})


@operations_bp.route("/venues/recommend", methods=["POST"])
def recommend_venues():
    conn = get_db()
    rows = venue_recommendations(conn, request.get_json(silent=True) or {})
    conn.close()
    return jsonify({"recommendations": rows})


@operations_bp.route("/venues/optimize", methods=["POST"])
def optimize_venues():
    conn = get_db()
    sessions = [dict(row) for row in conn.execute("SELECT * FROM sessions ORDER BY start_time").fetchall()]
    venues = {row["id"]: dict(row) for row in conn.execute("SELECT * FROM venues").fetchall()}
    conflicts_found, recommendations = 0, []
    current_hours = 0
    optimized_hours = 0
    for session in sessions:
        if session["venue_id"] in venues:
            current_hours += duration_hours(session["start_time"], session["end_time"])
        conflicts = session_conflicts(conn, session)
        conflicts_found += len(conflicts)
        ranked = venue_recommendations(conn, session)
        best = next((item for item in ranked if item["available_for_request"] and item["match_score"] >= 55), None)
        if best and best["id"] != session["venue_id"]:
            recommendations.append({
                "session_id": session["id"], "session": session["title"],
                "from_venue": venues.get(session["venue_id"], {}).get("name", "Unassigned"),
                "to_venue": best["name"], "reason": best["reason"], "match_score": best["match_score"],
            })
            optimized_hours += duration_hours(session["start_time"], session["end_time"])
        elif session["venue_id"] in venues and not conflicts:
            optimized_hours += duration_hours(session["start_time"], session["end_time"])
    total_venue_hours = max(1, len(venues) * 14)
    current_utilization = round(min(100, current_hours / total_venue_hours * 100), 1)
    optimized_utilization = round(min(100, max(current_utilization, optimized_hours / total_venue_hours * 100)), 1)
    conn.close()
    return jsonify({
        "current_utilization": current_utilization,
        "optimized_utilization": optimized_utilization,
        "conflicts_found": conflicts_found,
        "conflicts_resolved": max(0, conflicts_found - len(recommendations)),
        "venue_changes_recommended": len(recommendations),
        "recommendations": recommendations,
    })


@operations_bp.route("/speakers", methods=["GET"])
def list_speakers():
    conn = get_db()
    speakers = json_rows(conn.execute("SELECT * FROM speakers ORDER BY name"))
    for speaker in speakers:
        sessions = conn.execute("SELECT * FROM sessions WHERE speaker_id = ? AND status != 'Cancelled'", (speaker["id"],)).fetchall()
        speaker["assigned_sessions"] = len(sessions)
        speaker["scheduled_hours"] = round(sum(duration_hours(s["start_time"], s["end_time"]) for s in sessions), 1)
    conn.close()
    return jsonify({"speakers": speakers})


@operations_bp.route("/speakers/<int:speaker_id>", methods=["GET"])
def get_speaker(speaker_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM speakers WHERE id = ?", (speaker_id,)).fetchone()
    conn.close()
    return jsonify(as_dict(row)) if row else error("Speaker not found.", 404)


@operations_bp.route("/speakers", methods=["POST"])
def create_speaker():
    data = request.get_json(silent=True) or {}
    required = ["name", "email"]
    missing = next((field for field in required if not str(data.get(field, "")).strip()), None)
    if missing:
        return error(f"'{missing}' is required.")
    try:
        rating = float(data.get("rating", 4.5))
        if not 0 <= rating <= 5:
            raise ValueError
    except (ValueError, TypeError):
        return error("Rating must be between 0 and 5.")
    conn = get_db()
    try:
        cursor = conn.execute(
            """INSERT INTO speakers
            (name, designation, organization, email, phone, expertise,
             availability_start, availability_end, rating, biography)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (data["name"].strip(), data.get("designation", ""), data.get("organization", ""),
             data["email"].strip(), data.get("phone", ""), data.get("expertise", ""),
             data.get("availability_start", "09:00"), data.get("availability_end", "17:00"),
             rating, data.get("biography", "")),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM speakers WHERE id = ?", (cursor.lastrowid,)).fetchone()
    except Exception as exc:
        conn.rollback()
        conn.close()
        if "UNIQUE" in str(exc).upper():
            return error("A speaker with this email already exists.")
        return error("Unable to create speaker.")
    conn.close()
    return jsonify(as_dict(row)), 201


@operations_bp.route("/speakers/<int:speaker_id>", methods=["PUT"])
def update_speaker(speaker_id):
    data = request.get_json(silent=True) or {}
    if not str(data.get("name", "")).strip() or not str(data.get("email", "")).strip():
        return error("Name and email are required.")
    try:
        rating = float(data.get("rating", 4.5))
        if not 0 <= rating <= 5:
            raise ValueError
    except (ValueError, TypeError):
        return error("Rating must be between 0 and 5.")
    conn = get_db()
    try:
        conn.execute(
            """UPDATE speakers SET name=?, designation=?, organization=?, email=?, phone=?,
            expertise=?, availability_start=?, availability_end=?, rating=?, biography=? WHERE id=?""",
            (data["name"].strip(), data.get("designation", ""), data.get("organization", ""),
             data["email"].strip(), data.get("phone", ""), data.get("expertise", ""),
             data.get("availability_start", "09:00"), data.get("availability_end", "17:00"),
             rating, data.get("biography", ""), speaker_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM speakers WHERE id = ?", (speaker_id,)).fetchone()
    except Exception as exc:
        conn.rollback()
        conn.close()
        if "UNIQUE" in str(exc).upper():
            return error("A speaker with this email already exists.")
        return error("Unable to update speaker.")
    conn.close()
    return jsonify(as_dict(row)) if row else error("Speaker not found.", 404)


@operations_bp.route("/speakers/<int:speaker_id>", methods=["DELETE"])
def delete_speaker(speaker_id):
    conn = get_db()
    if conn.execute("SELECT 1 FROM speakers WHERE id = ?", (speaker_id,)).fetchone() is None:
        conn.close()
        return error("Speaker not found.", 404)
    conn.execute("UPDATE sessions SET speaker_id = NULL, status = 'Conflict' WHERE speaker_id = ?", (speaker_id,))
    conn.execute("DELETE FROM speakers WHERE id = ?", (speaker_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Speaker deleted."})


@operations_bp.route("/speakers/recommend", methods=["POST"])
def recommend_speakers():
    conn = get_db()
    rows = speaker_recommendations(conn, request.get_json(silent=True) or {})
    conn.close()
    return jsonify({"recommendations": rows})


def session_payload(data):
    required = ["title", "start_time", "end_time"]
    missing = next((field for field in required if not str(data.get(field, "")).strip()), None)
    if missing:
        return None, f"'{missing}' is required."
    time_error = validate_base_time(data)
    if time_error:
        return None, time_error
    try:
        attendees = int(data.get("expected_attendees", 0))
        if attendees < 0:
            raise ValueError
    except (ValueError, TypeError):
        return None, "Expected attendees must be zero or greater."
    return {
        "title": data["title"].strip(), "speaker_id": data.get("speaker_id") or None,
        "venue_id": data.get("venue_id") or None, "start_time": data["start_time"],
        "end_time": data["end_time"], "expected_attendees": attendees,
        "session_type": data.get("session_type", "General"), "required_equipment": data.get("required_equipment", ""),
        "required_expertise": data.get("required_expertise", ""), "status": data.get("status", "Draft"),
    }, None


def hydrate_session(conn, row):
    session = dict(row)
    session["speaker"] = as_dict(conn.execute("SELECT id, name, designation, organization FROM speakers WHERE id = ?", (row["speaker_id"],)).fetchone())
    session["venue"] = as_dict(conn.execute("SELECT id, name, capacity, venue_type, location FROM venues WHERE id = ?", (row["venue_id"],)).fetchone())
    session["duration_hours"] = round(duration_hours(row["start_time"], row["end_time"]), 1)
    session["conflicts"] = session_conflicts(conn, session)
    if session["conflicts"] and session["status"] not in ("Conflict", "Cancelled"):
        session["computed_status"] = "Conflict"
    else:
        session["computed_status"] = session["status"]
    return session


@operations_bp.route("/sessions", methods=["GET"])
def list_sessions():
    conn = get_db()
    sessions = [hydrate_session(conn, row) for row in conn.execute("SELECT * FROM sessions ORDER BY start_time").fetchall()]
    conn.close()
    return jsonify({"sessions": sessions})


@operations_bp.route("/sessions/<int:session_id>", methods=["GET"])
def get_session(session_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    result = hydrate_session(conn, row) if row else None
    conn.close()
    return jsonify(result) if result else error("Session not found.", 404)


@operations_bp.route("/sessions", methods=["POST"])
def create_session():
    data, validation_error = session_payload(request.get_json(silent=True) or {})
    if validation_error:
        return error(validation_error)
    conn = get_db()
    if data["speaker_id"] and not conn.execute("SELECT 1 FROM speakers WHERE id = ?", (data["speaker_id"],)).fetchone():
        conn.close()
        return error("Selected speaker was not found.")
    if data["venue_id"] and not conn.execute("SELECT 1 FROM venues WHERE id = ?", (data["venue_id"],)).fetchone():
        conn.close()
        return error("Selected venue was not found.")
    cursor = conn.execute(
        """INSERT INTO sessions
        (title, speaker_id, venue_id, start_time, end_time, expected_attendees,
         session_type, required_equipment, required_expertise, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        tuple(data.values()),
    )
    conn.commit()
    result = hydrate_session(conn, conn.execute("SELECT * FROM sessions WHERE id = ?", (cursor.lastrowid,)).fetchone())
    conn.close()
    return jsonify(result), 201


@operations_bp.route("/sessions/<int:session_id>", methods=["PUT"])
def update_session(session_id):
    data, validation_error = session_payload(request.get_json(silent=True) or {})
    if validation_error:
        return error(validation_error)
    conn = get_db()
    if not conn.execute("SELECT 1 FROM sessions WHERE id = ?", (session_id,)).fetchone():
        conn.close()
        return error("Session not found.", 404)
    values = tuple(data.values()) + (session_id,)
    conn.execute(
        """UPDATE sessions SET title=?, speaker_id=?, venue_id=?, start_time=?, end_time=?,
        expected_attendees=?, session_type=?, required_equipment=?, required_expertise=?, status=? WHERE id=?""",
        values,
    )
    conn.commit()
    result = hydrate_session(conn, conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone())
    conn.close()
    return jsonify(result)


@operations_bp.route("/sessions/<int:session_id>", methods=["DELETE"])
def delete_session(session_id):
    conn = get_db()
    if not conn.execute("SELECT 1 FROM sessions WHERE id = ?", (session_id,)).fetchone():
        conn.close()
        return error("Session not found.", 404)
    conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Session deleted."})


@operations_bp.route("/schedule/validate", methods=["POST"])
def validate_schedule():
    data = request.get_json(silent=True) or {}
    conn = get_db()
    conflicts = session_conflicts(conn, data, data.get("id"))
    conn.close()
    return jsonify({"valid": not conflicts, "conflicts": conflicts})


@operations_bp.route("/schedule/conflicts", methods=["GET"])
def schedule_conflicts():
    conn = get_db()
    conflicts = []
    sessions = [dict(row) for row in conn.execute("SELECT * FROM sessions ORDER BY start_time").fetchall()]
    for session in sessions:
        for conflict in session_conflicts(conn, session):
            conflicts.append({"session_id": session["id"], "session": session["title"], **conflict})
    conn.close()
    return jsonify({"conflicts": conflicts})


@operations_bp.route("/schedule/auto", methods=["POST"])
def auto_schedule():
    conn = get_db()
    sessions = [dict(row) for row in conn.execute("SELECT * FROM sessions ORDER BY start_time, id").fetchall()]
    results = []
    changed = 0
    conflicts_before = 0
    for session in sessions:
        conflicts_before += len(session_conflicts(conn, session))
        best_speaker = next((s for s in speaker_recommendations(conn, {
            "topic": session["title"], "required_expertise": session["required_expertise"],
            "start_time": session["start_time"], "end_time": session["end_time"],
            "session_id": session["id"],
        }) if s["available_for_request"]), None)
        if best_speaker and best_speaker["id"] != session["speaker_id"]:
            conn.execute("UPDATE sessions SET speaker_id=? WHERE id=?", (best_speaker["id"], session["id"]))
            session["speaker_id"] = best_speaker["id"]
            changed += 1
        best_venue = next((v for v in venue_recommendations(conn, session) if v["available_for_request"]), None)
        if best_venue and best_venue["id"] != session["venue_id"]:
            conn.execute("UPDATE sessions SET venue_id=? WHERE id=?", (best_venue["id"], session["id"]))
            session["venue_id"] = best_venue["id"]
            changed += 1
        remaining = session_conflicts(conn, session)
        status = "Conflict" if remaining else "Optimized"
        conn.execute("UPDATE sessions SET status=? WHERE id=?", (status, session["id"]))
        results.append({"id": session["id"], "title": session["title"], "status": status, "conflicts": remaining})
    conn.commit()
    conflicts_after = sum(len(session_conflicts(conn, session)) for session in sessions)
    venue_hours = sum(duration_hours(row["start_time"], row["end_time"]) for row in sessions if row["venue_id"])
    speaker_hours = {}
    for row in sessions:
        if row["speaker_id"]:
            speaker_hours[row["speaker_id"]] = speaker_hours.get(row["speaker_id"], 0) + duration_hours(row["start_time"], row["end_time"])
    venues = conn.execute("SELECT COUNT(*) AS count FROM venues").fetchone()["count"]
    conn.close()
    return jsonify({
        "message": "AI Schedule Generated Successfully",
        "sessions_scheduled": len(results), "conflicts_detected": conflicts_before,
        "conflicts_resolved": max(0, conflicts_before - conflicts_after),
        "venue_utilization": round(min(100, venue_hours / max(1, venues * 14) * 100), 1),
        "speaker_workload": [{"speaker_id": key, "hours": round(value, 1)} for key, value in speaker_hours.items()],
        "changed_assignments": changed, "sessions": results,
    })


def operations_summary(conn):
    venue_rows = [dict(row) for row in conn.execute("SELECT * FROM venues ORDER BY name").fetchall()]
    speaker_rows = [dict(row) for row in conn.execute("SELECT * FROM speakers ORDER BY name").fetchall()]
    session_rows = [dict(row) for row in conn.execute("SELECT * FROM sessions ORDER BY start_time").fetchall()]
    conflicts = []
    for row in session_rows:
        conflicts.extend([{"session_id": row["id"], "session": row["title"], **item} for item in session_conflicts(conn, row)])
    venue_analytics = []
    for venue in venue_rows:
        assigned = [row for row in session_rows if row["venue_id"] == venue["id"]]
        hours = sum(duration_hours(row["start_time"], row["end_time"]) for row in assigned)
        venue_analytics.append({
            **venue, "sessions": len(assigned),
            "attendees": sum(row["expected_attendees"] for row in assigned),
            "utilization": round(min(100, hours / 14 * 100), 1),
            "status": "Overbooked" if any(item["type"] == "Venue" and item["session_id"] in [r["id"] for r in assigned] for item in conflicts) else ("Active" if assigned else "Underutilized"),
        })
    speaker_analytics = []
    for speaker in speaker_rows:
        assigned = [row for row in session_rows if row["speaker_id"] == speaker["id"]]
        hours = sum(duration_hours(row["start_time"], row["end_time"]) for row in assigned)
        availability = max(1, (parse_datetime("2026-01-01 " + str(speaker["availability_end"])) - parse_datetime("2026-01-01 " + str(speaker["availability_start"]))).total_seconds() / 3600) if parse_datetime(speaker["availability_start"]) is None else 8
        speaker_analytics.append({**speaker, "sessions": len(assigned), "scheduled_hours": round(hours, 1), "availability_utilization": round(min(100, hours / availability * 100), 1)})
    session_analytics = []
    for row in session_rows:
        item = hydrate_session(conn, row)
        session_analytics.append(item)
    avg_utilization = round(sum(item["utilization"] for item in venue_analytics) / max(1, len(venue_analytics)), 1)
    return {
        "summary": {
            "average_venue_utilization": avg_utilization,
            "planned_attendees": sum(row["expected_attendees"] for row in session_rows),
            "total_speakers": len(speaker_rows),
            "confirmed_sessions": sum(1 for row in session_rows if row["status"] in ("Confirmed", "Optimized")),
            "total_venues": len(venue_rows),
            "scheduling_conflicts": len(conflicts),
        },
        "venues": venue_analytics, "speakers": speaker_analytics,
        "sessions": session_analytics, "conflicts": conflicts,
    }


@operations_bp.route("/analytics/operations", methods=["GET"])
def operations_analytics():
    conn = get_db()
    result = operations_summary(conn)
    conn.close()
    return jsonify(result)


@operations_bp.route("/analytics/venue", methods=["GET"])
def venue_analytics():
    conn = get_db()
    result = operations_summary(conn)["venues"]
    conn.close()
    return jsonify({"venues": result})


@operations_bp.route("/analytics/speaker", methods=["GET"])
def speaker_analytics():
    conn = get_db()
    result = operations_summary(conn)["speakers"]
    conn.close()
    return jsonify({"speakers": result})


@operations_bp.route("/analytics/sessions", methods=["GET"])
def session_analytics():
    conn = get_db()
    result = operations_summary(conn)["sessions"]
    conn.close()
    return jsonify({"sessions": result})