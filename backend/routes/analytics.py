"""
Analytics route: aggregates attendee data for charts and dashboard.
"""

from flask import Blueprint, jsonify
from database import get_db
from collections import Counter

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics", methods=["GET"])
def get_analytics():
    """Return aggregated analytics data."""
    conn = get_db()
    cursor = conn.cursor()

    # Basic counts
    cursor.execute("SELECT COUNT(*) FROM attendees")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM attendees WHERE status = 'checked_in'")
    checked_in = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM attendees WHERE DATE(registration_date) = DATE('now','localtime')")
    today_registrations = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM attendees WHERE role = 'Student'")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM attendees WHERE role = 'Professional'")
    total_professionals = cursor.fetchone()[0]

    # Gender distribution
    cursor.execute("SELECT gender, COUNT(*) as count FROM attendees WHERE gender != '' GROUP BY gender")
    gender_dist = {row["gender"]: row["count"] for row in cursor.fetchall()}

    # Age distribution (buckets)
    cursor.execute("SELECT age FROM attendees WHERE age IS NOT NULL AND age > 0")
    ages = [row["age"] for row in cursor.fetchall()]
    age_dist = _bucket_ages(ages)

    # Department distribution
    cursor.execute("""
        SELECT department, COUNT(*) as count
        FROM attendees WHERE department != ''
        GROUP BY department ORDER BY count DESC LIMIT 10
    """)
    dept_dist = {row["department"]: row["count"] for row in cursor.fetchall()}

    # Registration trend (last 7 days)
    cursor.execute("""
        SELECT DATE(registration_date) as reg_date, COUNT(*) as count
        FROM attendees
        WHERE registration_date >= DATE('now', '-6 days', 'localtime')
        GROUP BY reg_date ORDER BY reg_date ASC
    """)
    trend_rows = cursor.fetchall()
    trend = [{"date": r["reg_date"], "count": r["count"]} for r in trend_rows]

    # Top colleges
    cursor.execute("""
        SELECT college, COUNT(*) as count
        FROM attendees WHERE college != ''
        GROUP BY college ORDER BY count DESC LIMIT 8
    """)
    top_colleges = [{"college": r["college"], "count": r["count"]} for r in cursor.fetchall()]

    # Food preference distribution
    cursor.execute("""
        SELECT food_preference, COUNT(*) as count
        FROM attendees WHERE food_preference != ''
        GROUP BY food_preference ORDER BY count DESC
    """)
    food_dist = {r["food_preference"]: r["count"] for r in cursor.fetchall()}

    # Check-in percentage over event days
    cursor.execute("""
        SELECT DATE(checkin_time) as day, COUNT(*) as count
        FROM attendees WHERE checkin_time IS NOT NULL
        GROUP BY day ORDER BY day ASC
    """)
    checkin_trend = [{"date": r["day"], "count": r["count"]} for r in cursor.fetchall()]

    # Recent registrations (last 5)
    cursor.execute("""
        SELECT id, full_name, email, department, registration_date, status
        FROM attendees ORDER BY id DESC LIMIT 5
    """)
    recent = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return jsonify({
        "total": total,
        "checked_in": checked_in,
        "pending": total - checked_in,
        "today_registrations": today_registrations,
        "total_students": total_students,
        "total_professionals": total_professionals,
        "gender_dist": gender_dist,
        "age_dist": age_dist,
        "dept_dist": dept_dist,
        "trend": trend,
        "top_colleges": top_colleges,
        "food_dist": food_dist,
        "checkin_trend": checkin_trend,
        "recent": recent,
    })


def _bucket_ages(ages):
    """Group ages into readable buckets."""
    buckets = {
        "Under 18": 0,
        "18–22": 0,
        "23–27": 0,
        "28–35": 0,
        "36–45": 0,
        "46+": 0,
    }
    for age in ages:
        if age < 18:
            buckets["Under 18"] += 1
        elif age <= 22:
            buckets["18–22"] += 1
        elif age <= 27:
            buckets["23–27"] += 1
        elif age <= 35:
            buckets["28–35"] += 1
        elif age <= 45:
            buckets["36–45"] += 1
        else:
            buckets["46+"] += 1
    return {k: v for k, v in buckets.items() if v > 0}
