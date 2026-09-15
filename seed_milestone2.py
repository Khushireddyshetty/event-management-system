"""Add safe Milestone 2 demo data without overwriting user records."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from database import get_db, init_db


def seed():
    init_db()
    conn = get_db()
    venues = [
        ("Grand Hall", 500, "Auditorium", "Main campus", "Projector, Wi-Fi, Audio System, Stage, AC", "Step-free access"),
        ("Innovation Lab", 120, "Lab", "North wing", "Projector, Wi-Fi, Video Conferencing, AC", "Accessible workstations"),
        ("Tech Room 1", 80, "Seminar Hall", "Learning center", "Projector, Wi-Fi, Audio System, AC", "Step-free access"),
        ("Tech Room 2", 60, "Workshop Room", "Learning center", "Projector, Wi-Fi, Whiteboard, AC", "Step-free access"),
        ("Executive Room", 24, "Conference Room", "Administration block", "Wi-Fi, Video Conferencing, AC", "Elevator access"),
        ("Conference Room", 90, "Conference Room", "Innovation wing", "Projector, Wi-Fi, Audio System, Video Conferencing, AC", "Step-free access"),
    ]
    for venue in venues:
        conn.execute(
            """INSERT OR IGNORE INTO venues
            (name, capacity, venue_type, location, facilities, accessibility)
            VALUES (?, ?, ?, ?, ?, ?)""",
            venue,
        )

    speakers = [
        ("Dr. Ananya Sharma", "AI Research Lead", "Future Labs", "ananya.sharma@example.com", "+91 90000 10001", "Artificial Intelligence, Machine Learning, LLMs", "09:00", "17:00", 4.9, "Researcher and keynote speaker focused on practical AI adoption."),
        ("Rahul Verma", "Product Director", "DataWorks", "rahul.verma@example.com", "+91 90000 10002", "Data Analytics, Product Strategy, Leadership", "10:00", "18:00", 4.7, "Product leader helping teams turn data into measurable decisions."),
        ("Priya Singh", "Startup Mentor", "LaunchPad Network", "priya.singh@example.com", "+91 90000 10003", "Entrepreneurship, Startups, Fundraising", "09:00", "16:00", 4.8, "Mentor and founder with experience taking products from idea to market."),
        ("Aman Kapoor", "Solutions Architect", "CloudScale", "aman.kapoor@example.com", "+91 90000 10004", "Cloud Computing, Software Architecture, AI", "11:00", "19:00", 4.6, "Architect who builds scalable systems and developer platforms."),
    ]
    for speaker in speakers:
        conn.execute(
            """INSERT OR IGNORE INTO speakers
            (name, designation, organization, email, phone, expertise,
             availability_start, availability_end, rating, biography)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            speaker,
        )

    sessions = [
        ("Opening Keynote: Future of AI", "2026-08-11T09:30", "2026-08-11T10:30", 420, "Keynote", "Projector, Wi-Fi, Audio System", "Artificial Intelligence", "Confirmed"),
        ("Building with LLMs", "2026-08-11T11:00", "2026-08-11T12:00", 100, "Seminar", "Projector, Wi-Fi", "Artificial Intelligence, LLMs", "Draft"),
        ("Data-Driven Decisions", "2026-08-11T13:30", "2026-08-11T14:30", 75, "Workshop", "Projector, Wi-Fi", "Data Analytics", "Draft"),
        ("From Idea to Startup", "2026-08-11T15:00", "2026-08-11T16:00", 90, "Panel", "Projector, Wi-Fi, Audio System", "Entrepreneurship, Startups", "Draft"),
    ]
    for title, start, end, attendees, session_type, equipment, expertise, status in sessions:
        if not conn.execute("SELECT 1 FROM sessions WHERE title = ?", (title,)).fetchone():
            conn.execute(
                """INSERT INTO sessions
                (title, start_time, end_time, expected_attendees, session_type,
                 required_equipment, required_expertise, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (title, start, end, attendees, session_type, equipment, expertise, status),
            )

    conn.commit()
    counts = {
        "venues": conn.execute("SELECT COUNT(*) AS count FROM venues").fetchone()["count"],
        "speakers": conn.execute("SELECT COUNT(*) AS count FROM speakers").fetchone()["count"],
        "sessions": conn.execute("SELECT COUNT(*) AS count FROM sessions").fetchone()["count"],
    }
    conn.close()
    print("Milestone 2 demo data is ready.")
    print("Existing records were preserved.")
    print(f"Totals: {counts['venues']} venues, {counts['speakers']} speakers, {counts['sessions']} sessions")


if __name__ == "__main__":
    seed()