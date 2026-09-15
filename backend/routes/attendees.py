"""
Attendee CRUD routes: register, list, get, update, delete, check-in.
New features: unique PIN generation, registration ID, PIN-based check-in, email confirmation.
"""

import random
import string
from datetime import datetime
from flask import Blueprint, request, jsonify
from database import get_db
from email_service import send_confirmation_email

attendees_bp = Blueprint("attendees", __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_unique_pin(cursor) -> str:
    """Generate a 6-digit numeric PIN that does not already exist in the DB."""
    for _ in range(50):          # max 50 attempts (effectively impossible to exhaust)
        pin = str(random.randint(100000, 999999))
        cursor.execute("SELECT id FROM attendees WHERE unique_pin = ?", (pin,))
        if not cursor.fetchone():
            return pin
    raise RuntimeError("Unable to generate a unique PIN — try again.")


def _make_registration_id(row_id: int) -> str:
    """Return a human-friendly registration ID like REG00042."""
    return f"REG{str(row_id).zfill(5)}"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@attendees_bp.route("/attendees", methods=["GET"])
def get_attendees():
    """Return all attendees with optional search/filter/pagination."""
    search = request.args.get("search", "").strip()
    gender = request.args.get("gender", "")
    department = request.args.get("department", "")
    status = request.args.get("status", "")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))

    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM attendees WHERE 1=1"
    params = []

    if search:
        query += " AND (full_name LIKE ? OR email LIKE ? OR college LIKE ? OR phone LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like, like, like])
    if gender:
        query += " AND gender = ?"
        params.append(gender)
    if department:
        query += " AND department = ?"
        params.append(department)
    if status:
        query += " AND status = ?"
        params.append(status)

    # Count total matching records
    count_cursor = conn.cursor()
    count_cursor.execute(query.replace("SELECT *", "SELECT COUNT(*)", 1), params)
    total = count_cursor.fetchone()[0]

    # Apply pagination
    query += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return jsonify({
        "attendees": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    })


@attendees_bp.route("/attendee/<int:attendee_id>", methods=["GET"])
def get_attendee(attendee_id):
    """Return a single attendee by ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM attendees WHERE id = ?", (attendee_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Attendee not found"}), 404
    return jsonify(dict(row))


@attendees_bp.route("/register", methods=["POST"])
def register_attendee():
    """Register a new attendee. Generates a unique PIN and registration ID,
    then sends a confirmation email."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    required = ["full_name", "email"]
    for field in required:
        if not data.get(field, "").strip():
            return jsonify({"error": f"'{field}' is required"}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Check for duplicate email
    cursor.execute("SELECT id FROM attendees WHERE email = ?", (data["email"].strip().lower(),))
    if cursor.fetchone():
        conn.close()
        return jsonify({"error": "Email already registered"}), 409

    # Generate unique PIN before insert
    unique_pin = _generate_unique_pin(cursor)

    cursor.execute("""
        INSERT INTO attendees
          (full_name, email, phone, age, gender, role, department, college, city, state,
           event_name, registration_type, food_preference, special_requirements, unique_pin)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("full_name", "").strip(),
        data.get("email", "").strip().lower(),
        data.get("phone", ""),
        data.get("age"),
        data.get("gender", ""),
        data.get("role", ""),
        data.get("department", ""),
        data.get("college", ""),
        data.get("city", ""),
        data.get("state", ""),
        data.get("event_name", ""),
        data.get("registration_type", ""),
        data.get("food_preference", ""),
        data.get("special_requirements", ""),
        unique_pin,
    ))
    conn.commit()
    new_id = cursor.lastrowid

    # Build and store the registration ID
    registration_id = _make_registration_id(new_id)
    cursor.execute(
        "UPDATE attendees SET registration_id = ? WHERE id = ?",
        (registration_id, new_id),
    )
    conn.commit()

    # Fetch the full row (includes registration_date set by DB default)
    cursor.execute("SELECT * FROM attendees WHERE id = ?", (new_id,))
    attendee = dict(cursor.fetchone())
    conn.close()

    # Send confirmation email (non-blocking — failure does not abort the response)
    send_confirmation_email(attendee)

    return jsonify({
        "message": "Registration successful",
        "id": new_id,
        "registration_id": registration_id,
        "unique_pin": unique_pin,
        "registration_date": attendee.get("registration_date", ""),
    }), 201


@attendees_bp.route("/update/<int:attendee_id>", methods=["PUT"])
def update_attendee(attendee_id):
    """Update an existing attendee's details."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM attendees WHERE id = ?", (attendee_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "Attendee not found"}), 404

    fields = [
        "full_name", "email", "phone", "age", "gender", "role", "department",
        "college", "city", "state", "event_name", "registration_type",
        "food_preference", "special_requirements",
    ]
    updates = {f: data[f] for f in fields if f in data}
    if not updates:
        conn.close()
        return jsonify({"error": "No valid fields to update"}), 400

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [attendee_id]
    cursor.execute(f"UPDATE attendees SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return jsonify({"message": "Attendee updated successfully"})


@attendees_bp.route("/delete/<int:attendee_id>", methods=["DELETE"])
def delete_attendee(attendee_id):
    """Delete an attendee by ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM attendees WHERE id = ?", (attendee_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "Attendee not found"}), 404

    cursor.execute("DELETE FROM attendees WHERE id = ?", (attendee_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Attendee deleted successfully"})


@attendees_bp.route("/checkin/<int:attendee_id>", methods=["POST"])
def checkin_attendee(attendee_id):
    """Mark an attendee as checked in (by ID) with a timestamp."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, status FROM attendees WHERE id = ?", (attendee_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Attendee not found"}), 404
    if dict(row)["status"] == "checked_in":
        conn.close()
        return jsonify({"error": "Attendee already checked in"}), 400

    cursor.execute(
        "UPDATE attendees SET status = 'checked_in', checked_in = 1, checkin_time = datetime('now','localtime') WHERE id = ?",
        (attendee_id,),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Check-in successful"})


@attendees_bp.route("/checkin/pin", methods=["POST"])
def checkin_by_pin():
    """Check in an attendee using their unique 6-digit PIN.

    Request body: { "pin": "482951" }

    Returns attendee info on success, or an error message if PIN is invalid /
    attendee already checked in.
    """
    data = request.get_json()
    if not data or not str(data.get("pin", "")).strip():
        return jsonify({"error": "PIN is required"}), 400

    pin = str(data["pin"]).strip()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM attendees WHERE unique_pin = ?", (pin,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Invalid PIN. No attendee found with this PIN."}), 404

    attendee = dict(row)

    if attendee["status"] == "checked_in":
        conn.close()
        return jsonify({
            "error": "Attendee already checked in.",
            "attendee": attendee,
        }), 400

    cursor.execute(
        "UPDATE attendees SET status = 'checked_in', checked_in = 1, checkin_time = datetime('now','localtime') WHERE unique_pin = ?",
        (pin,),
    )
    conn.commit()

    # Return updated record
    cursor.execute("SELECT * FROM attendees WHERE unique_pin = ?", (pin,))
    updated = dict(cursor.fetchone())
    conn.close()

    return jsonify({
        "message": "Check-in successful!",
        "attendee": updated,
    })


@attendees_bp.route("/undo-checkin/<int:attendee_id>", methods=["POST"])
def undo_checkin(attendee_id):
    """Reverse a check-in for an attendee."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, status FROM attendees WHERE id = ?", (attendee_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Attendee not found"}), 404

    cursor.execute(
        "UPDATE attendees SET status = 'registered', checked_in = 0, checkin_time = NULL WHERE id = ?",
        (attendee_id,),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Check-in reversed successfully"})
