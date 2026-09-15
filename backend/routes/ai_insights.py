"""
AI Insights route — fetches analytics data and passes it to the AI module.
"""

from flask import Blueprint, jsonify
from database import get_db
from ai import generate_insights
from routes.analytics import get_analytics
from flask import current_app

ai_bp = Blueprint("ai", __name__)


@ai_bp.route("/generate-ai", methods=["POST"])
def generate_ai_insights():
    """Generate AI insights based on current attendee analytics."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM attendees")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM attendees WHERE status = 'checked_in'")
    checked_in = cursor.fetchone()[0]

    cursor.execute("SELECT gender, COUNT(*) as count FROM attendees WHERE gender != '' GROUP BY gender")
    gender_dist = {row["gender"]: row["count"] for row in cursor.fetchall()}

    cursor.execute("SELECT department, COUNT(*) as count FROM attendees WHERE department != '' GROUP BY department ORDER BY count DESC LIMIT 10")
    dept_dist = {row["department"]: row["count"] for row in cursor.fetchall()}

    cursor.execute("""
        SELECT DATE(registration_date) as reg_date, COUNT(*) as count
        FROM attendees
        WHERE registration_date >= DATE('now', '-6 days', 'localtime')
        GROUP BY reg_date ORDER BY reg_date ASC
    """)
    trend = [{"date": r["reg_date"], "count": r["count"]} for r in cursor.fetchall()]

    cursor.execute("""
        SELECT college, COUNT(*) as count FROM attendees WHERE college != ''
        GROUP BY college ORDER BY count DESC LIMIT 5
    """)
    top_colleges = [{"college": r["college"], "count": r["count"]} for r in cursor.fetchall()]

    conn.close()

    analytics_data = {
        "total": total,
        "checked_in": checked_in,
        "gender_dist": gender_dist,
        "dept_dist": dept_dist,
        "trend": trend,
        "top_colleges": top_colleges,
    }

    insights = generate_insights(analytics_data)
    return jsonify({"insights": insights})
