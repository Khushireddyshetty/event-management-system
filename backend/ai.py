"""
AI Insights module using Google Gemini API.
Falls back to mock responses if no API key is configured.
"""

import os
import json
from datetime import datetime


def generate_insights(analytics_data: dict) -> dict:
    """
    Generate AI-powered insights from attendee analytics data.
    Uses Gemini API if GEMINI_API_KEY is set, otherwise returns mock insights.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "")

    if api_key and api_key.strip():
        return _gemini_insights(api_key, analytics_data)
    else:
        return _mock_insights(analytics_data)


def _gemini_insights(api_key: str, data: dict) -> dict:
    """Call Google Gemini API to generate insights."""
    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-pro")

        prompt = f"""
You are an expert event analyst. Analyze this event registration data and provide insights.

Data:
- Total Registrations: {data.get('total', 0)}
- Checked In: {data.get('checked_in', 0)}
- Gender Distribution: {json.dumps(data.get('gender_dist', {}))}
- Age Distribution: {json.dumps(data.get('age_dist', {}))}
- Department Distribution: {json.dumps(data.get('dept_dist', {}))}
- Registration Trend (last 7 days): {json.dumps(data.get('trend', []))}
- Top Colleges: {json.dumps(data.get('top_colleges', []))}

Return a JSON object with these exact keys:
{{
  "registration_summary": "2-3 sentence summary",
  "attendance_prediction": "prediction with percentage",
  "peak_registration_hours": "insight about timing",
  "volunteer_suggestions": "staffing recommendations",
  "crowd_insights": "behavioral insights",
  "department_trends": "department-specific trends",
  "event_recommendations": "actionable recommendations"
}}
"""
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Extract JSON from response
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        return json.loads(text)

    except Exception as e:
        print(f"[AI] Gemini API error: {e}. Falling back to mock insights.")
        return _mock_insights(data)


def _mock_insights(data: dict) -> dict:
    """Generate realistic mock insights from actual data."""
    total = data.get("total", 0)
    checked_in = data.get("checked_in", 0)
    check_pct = round((checked_in / total * 100), 1) if total > 0 else 0

    gender_dist = data.get("gender_dist", {})
    dept_dist = data.get("dept_dist", {})
    top_dept = max(dept_dist, key=dept_dist.get) if dept_dist else "N/A"
    top_colleges = data.get("top_colleges", [])
    top_college = top_colleges[0]["college"] if top_colleges else "N/A"

    male_pct = round((gender_dist.get("Male", 0) / total * 100), 1) if total > 0 else 0
    female_pct = round((gender_dist.get("Female", 0) / total * 100), 1) if total > 0 else 0

    return {
        "registration_summary": (
            f"The event has attracted {total} registrations so far, with a strong check-in rate of {check_pct}%. "
            f"The participant base is {male_pct}% male and {female_pct}% female, showing {'good gender diversity' if abs(male_pct - female_pct) < 20 else 'potential for improved gender outreach'}. "
            f"The {top_dept} department leads in participation, indicating strong domain-specific interest."
        ),
        "attendance_prediction": (
            f"Based on current registration patterns and historical check-in data, we predict a final attendance rate of "
            f"{min(check_pct + 15, 95):.0f}–{min(check_pct + 25, 98):.0f}%. "
            f"With {total - checked_in} registrants yet to check in, proactive reminder messages sent 24 hours and 2 hours before the event could increase actual attendance by an estimated 10–15%."
        ),
        "peak_registration_hours": (
            "Registration activity typically peaks between 10 AM–12 PM and 7 PM–9 PM on weekdays. "
            "A significant surge is observed in the 48 hours following announcement emails. "
            "Consider scheduling reminder communications in these windows to maximize response rates."
        ),
        "volunteer_suggestions": (
            f"Based on {total} registrations, we recommend deploying 6–8 volunteers at check-in counters to maintain an average wait time under 2 minutes. "
            f"Assign 2 dedicated volunteers to assist with dietary requirements and special needs. "
            f"A roving coordinator team of 3–4 people should handle floor logistics and Q&A support."
        ),
        "crowd_insights": (
            f"The majority of attendees originate from {top_college} and neighboring institutions, suggesting a strong local academic network. "
            "Attendee profiles indicate a high proportion of early-career professionals and students seeking networking and skill-building opportunities. "
            "Networking sessions and hands-on workshops are likely to see the highest engagement."
        ),
        "department_trends": (
            f"The {top_dept} department dominates with the highest registration share, reflecting current industry demand in this domain. "
            f"Cross-departmental registrations suggest interdisciplinary interest. "
            "Consider organizing breakout sessions segmented by department to deliver more targeted value and increase satisfaction scores."
        ),
        "event_recommendations": (
            "1. Send a personalized reminder to all non-checked-in registrants 24h before the event. "
            "2. Introduce a digital check-in QR system to reduce queue bottlenecks. "
            "3. Plan a dedicated networking lounge for attendees from top-represented colleges. "
            "4. Capture post-event feedback via a quick 3-question mobile survey to inform future editions. "
            "5. Leverage the existing attendee database to target invitations for follow-up events."
        ),
    }
