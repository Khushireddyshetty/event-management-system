"""
Import (CSV/JSON) and Export (CSV/JSON) routes for attendee data.
"""

import csv
import io
import json
from flask import Blueprint, request, jsonify, Response
from database import get_db

importexport_bp = Blueprint("importexport", __name__)

ALLOWED_FIELDS = [
    "full_name", "email", "phone", "age", "gender", "role", "department",
    "college", "city", "state", "event_name", "registration_type",
    "food_preference", "special_requirements",
]


@importexport_bp.route("/import", methods=["POST"])
def import_registrations():
    """
    Import attendees from CSV or JSON.
    Expects multipart/form-data with a file field named 'file'.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    filename = file.filename.lower()

    if filename.endswith(".csv"):
        return _import_csv(file)
    elif filename.endswith(".json"):
        return _import_json(file)
    else:
        return jsonify({"error": "Unsupported file type. Use CSV or JSON."}), 400


def _import_csv(file):
    """Parse and import a CSV file."""
    try:
        stream = io.StringIO(file.stream.read().decode("utf-8"))
        reader = csv.DictReader(stream)
        return _bulk_insert(list(reader))
    except Exception as e:
        return jsonify({"error": f"CSV parse error: {str(e)}"}), 400


def _import_json(file):
    """Parse and import a JSON file."""
    try:
        data = json.loads(file.stream.read().decode("utf-8"))
        if not isinstance(data, list):
            return jsonify({"error": "JSON must be a list of objects"}), 400
        return _bulk_insert(data)
    except Exception as e:
        return jsonify({"error": f"JSON parse error: {str(e)}"}), 400


def _bulk_insert(records):
    """Validate and bulk-insert attendee records."""
    if not records:
        return jsonify({"error": "No records found in file"}), 400

    conn = get_db()
    cursor = conn.cursor()

    inserted = 0
    skipped = 0
    errors = []

    for i, rec in enumerate(records, start=1):
        name = str(rec.get("full_name", "")).strip()
        email = str(rec.get("email", "")).strip().lower()

        if not name or not email:
            errors.append(f"Row {i}: missing full_name or email — skipped")
            skipped += 1
            continue

        # Skip duplicates
        cursor.execute("SELECT id FROM attendees WHERE email = ?", (email,))
        if cursor.fetchone():
            skipped += 1
            continue

        try:
            cursor.execute("""
                INSERT INTO attendees
                  (full_name, email, phone, age, gender, role, department, college,
                   city, state, event_name, registration_type, food_preference, special_requirements)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name,
                email,
                str(rec.get("phone", "")),
                int(rec["age"]) if str(rec.get("age", "")).isdigit() else None,
                str(rec.get("gender", "")),
                str(rec.get("role", "")),
                str(rec.get("department", "")),
                str(rec.get("college", "")),
                str(rec.get("city", "")),
                str(rec.get("state", "")),
                str(rec.get("event_name", "")),
                str(rec.get("registration_type", "")),
                str(rec.get("food_preference", "")),
                str(rec.get("special_requirements", "")),
            ))
            inserted += 1
        except Exception as e:
            errors.append(f"Row {i}: {str(e)}")
            skipped += 1

    conn.commit()
    conn.close()

    return jsonify({
        "message": f"Import complete: {inserted} inserted, {skipped} skipped.",
        "inserted": inserted,
        "skipped": skipped,
        "errors": errors[:10],  # Return first 10 errors only
    })


@importexport_bp.route("/export", methods=["GET"])
def export_registrations():
    """
    Export all attendees as CSV (default) or JSON.
    Query param: format=csv|json
    """
    fmt = request.args.get("format", "csv").lower()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM attendees ORDER BY id ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    if fmt == "json":
        return Response(
            json.dumps(rows, indent=2),
            mimetype="application/json",
            headers={"Content-Disposition": "attachment; filename=attendees.json"},
        )

    # Default: CSV
    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    else:
        output.write("No data")

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=attendees.csv"},
    )
