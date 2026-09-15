"""
Database initialization and connection management.
Uses SQLite for simplicity and portability.
"""

import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "database", "events.db")


def get_db():
    """Get a database connection with row_factory for dict-like access."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database and create tables if they don't exist."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            age INTEGER,
            gender TEXT,
            role TEXT,
            department TEXT,
            college TEXT,
            city TEXT,
            state TEXT,
            event_name TEXT,
            registration_type TEXT,
            food_preference TEXT,
            special_requirements TEXT,
            registration_date TEXT DEFAULT (datetime('now','localtime')),
            status TEXT DEFAULT 'registered',
            checkin_time TEXT DEFAULT NULL,
            registration_id TEXT,
            unique_pin TEXT,
            checked_in INTEGER DEFAULT 0
        )
    """)

    # --- Migration: add new columns to existing databases ---
    existing_cols = {row[1] for row in cursor.execute("PRAGMA table_info(attendees)")}
    migrations = [
        ("registration_id", "TEXT"),
        ("unique_pin",      "TEXT"),
        ("checked_in",      "INTEGER DEFAULT 0"),
    ]
    for col, col_type in migrations:
        if col not in existing_cols:
            cursor.execute(f"ALTER TABLE attendees ADD COLUMN {col} {col_type}")
            print(f"[DB] Migration: added column '{col}'")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS venues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            capacity INTEGER NOT NULL CHECK (capacity > 0),
            venue_type TEXT NOT NULL,
            location TEXT NOT NULL,
            facilities TEXT DEFAULT '',
            accessibility TEXT DEFAULT '',
            availability_start TEXT DEFAULT '08:00',
            availability_end TEXT DEFAULT '22:00',
            status TEXT DEFAULT 'Available',
            utilization REAL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS speakers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            designation TEXT DEFAULT '',
            organization TEXT DEFAULT '',
            email TEXT NOT NULL UNIQUE,
            phone TEXT DEFAULT '',
            expertise TEXT DEFAULT '',
            availability_start TEXT DEFAULT '09:00',
            availability_end TEXT DEFAULT '17:00',
            rating REAL DEFAULT 4.5,
            biography TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            speaker_id INTEGER,
            venue_id INTEGER,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            expected_attendees INTEGER NOT NULL DEFAULT 0 CHECK (expected_attendees >= 0),
            session_type TEXT DEFAULT 'General',
            required_equipment TEXT DEFAULT '',
            required_expertise TEXT DEFAULT '',
            status TEXT DEFAULT 'Draft',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (speaker_id) REFERENCES speakers(id) ON DELETE SET NULL,
            FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE SET NULL
        )
    """)

    # Milestone 3: sponsorship, incident response, and operational monitoring.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sponsors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            company TEXT NOT NULL,
            contact_person TEXT DEFAULT '',
            email TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            tier TEXT DEFAULT 'Silver',
            amount REAL DEFAULT 0,
            contract_status TEXT DEFAULT 'Prospect',
            payment_status TEXT DEFAULT 'Pending',
            benefits TEXT DEFAULT '',
            deliverables TEXT DEFAULT '',
            deliverable_status TEXT DEFAULT 'Pending',
            event_name TEXT DEFAULT '',
            start_date TEXT DEFAULT '',
            end_date TEXT DEFAULT '',
            performance_score REAL DEFAULT 0,
            roi REAL DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            category TEXT DEFAULT 'Other',
            location TEXT DEFAULT '',
            event_name TEXT DEFAULT '',
            reported_by TEXT DEFAULT '',
            assigned_to TEXT DEFAULT '',
            priority TEXT DEFAULT 'Medium',
            severity TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'Open',
            due_date TEXT DEFAULT '',
            resolution_date TEXT DEFAULT '',
            resolution_notes TEXT DEFAULT '',
            escalation_level INTEGER DEFAULT 0,
            comments TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS operational_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_type TEXT NOT NULL,
            message TEXT NOT NULL,
            severity TEXT DEFAULT 'Medium',
            related_id INTEGER,
            status TEXT DEFAULT 'New',
            recommended_action TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    # Milestone 4 stores analysis snapshots separately from operational records.
    # This keeps existing Milestone 1–3 data intact while making analysis history
    # available to the intelligence center.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS intelligence_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            health_score REAL NOT NULL DEFAULT 0,
            health_status TEXT NOT NULL DEFAULT 'Critical',
            summary TEXT DEFAULT '',
            source_mode TEXT DEFAULT 'rule-based',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS intelligence_risks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            severity TEXT NOT NULL DEFAULT 'Medium',
            source TEXT DEFAULT '',
            recommended_action TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (analysis_id) REFERENCES intelligence_analyses(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS intelligence_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER NOT NULL,
            recommendation TEXT NOT NULL,
            reason TEXT DEFAULT '',
            priority TEXT NOT NULL DEFAULT 'Medium',
            related_module TEXT DEFAULT '',
            suggested_action TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (analysis_id) REFERENCES intelligence_analyses(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER NOT NULL,
            agent_name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'completed',
            findings TEXT DEFAULT '',
            recommendations TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (analysis_id) REFERENCES intelligence_analyses(id) ON DELETE CASCADE
        )
    """)

    # Small, deterministic demo dataset makes a fresh checkout immediately useful.
    # Each section is guarded independently so a partially populated real
    # database is never overwritten or reset.
    if cursor.execute("SELECT COUNT(*) FROM venues").fetchone()[0] == 0:
        cursor.executemany("""INSERT INTO venues
            (name, capacity, venue_type, location, facilities, accessibility)
            VALUES (?, ?, ?, ?, ?, ?)""", [
            ("Grand Hall", 500, "Auditorium", "Main campus", "Projector, Wi-Fi, Audio System, Stage, AC", "Step-free access"),
            ("Innovation Lab", 120, "Lab", "North wing", "Projector, Wi-Fi, Video Conferencing, AC", "Accessible workstations"),
            ("Tech Room 1", 80, "Seminar Hall", "Learning center", "Projector, Wi-Fi, Audio System, AC", "Step-free access"),
            ("Tech Room 2", 60, "Workshop Room", "Learning center", "Projector, Wi-Fi, Whiteboard, AC", "Step-free access"),
            ("Executive Room", 24, "Conference Room", "Administration block", "Wi-Fi, Video Conferencing, AC", "Elevator access"),
        ])
    if cursor.execute("SELECT COUNT(*) FROM speakers").fetchone()[0] == 0:
        cursor.executemany("""INSERT INTO speakers
            (name, designation, organization, email, phone, expertise,
             availability_start, availability_end, rating, biography)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", [
            ("Dr. Ananya Sharma", "AI Research Lead", "Future Labs", "ananya.sharma@example.com", "+91 90000 10001", "Artificial Intelligence, Machine Learning, LLMs", "09:00", "17:00", 4.9, "Researcher and keynote speaker focused on practical AI adoption."),
            ("Rahul Verma", "Product Director", "DataWorks", "rahul.verma@example.com", "+91 90000 10002", "Data Analytics, Product Strategy, Leadership", "10:00", "18:00", 4.7, "Product leader helping teams turn data into measurable decisions."),
            ("Priya Singh", "Startup Mentor", "LaunchPad Network", "priya.singh@example.com", "+91 90000 10003", "Entrepreneurship, Startups, Fundraising", "09:00", "16:00", 4.8, "Mentor and founder with experience taking products from idea to market."),
            ("Aman Kapoor", "Solutions Architect", "CloudScale", "aman.kapoor@example.com", "+91 90000 10004", "Cloud Computing, Software Architecture, AI", "11:00", "19:00", 4.6, "Architect who builds scalable systems and developer platforms."),
        ])
    if cursor.execute("SELECT COUNT(*) FROM attendees").fetchone()[0] == 0:
        demo_attendees = [
            ("Aditi Rao", "aditi.rao@example.com", "9876500001", 27, "Female", "Professional", "Engineering", "Future Labs", "Bengaluru", "Karnataka", "Innovation Summit", "Standard", "Vegetarian", "", "REG-DEMO-001", "checked_in"),
            ("Vikram Nair", "vikram.nair@example.com", "9876500002", 31, "Male", "Professional", "Product", "DataWorks", "Mumbai", "Maharashtra", "Innovation Summit", "Standard", "Non-vegetarian", "", "REG-DEMO-002", "checked_in"),
            ("Neha Joshi", "neha.joshi@example.com", "9876500003", 23, "Female", "Student", "Computer Science", "LaunchPad University", "Pune", "Maharashtra", "Innovation Summit", "Student", "Vegetarian", "", "REG-DEMO-003", "checked_in"),
            ("Arjun Menon", "arjun.menon@example.com", "9876500004", 29, "Male", "Professional", "Engineering", "CloudScale", "Chennai", "Tamil Nadu", "Innovation Summit", "Standard", "Vegetarian", "", "REG-DEMO-004", "checked_in"),
            ("Ishita Shah", "ishita.shah@example.com", "9876500005", 21, "Female", "Student", "Design", "Design Institute", "Ahmedabad", "Gujarat", "Innovation Summit", "Student", "Vegetarian", "", "REG-DEMO-005", "registered"),
            ("Rohan Das", "rohan.das@example.com", "9876500006", 35, "Male", "Professional", "Operations", "EventWorks", "Delhi", "Delhi", "Innovation Summit", "Standard", "Non-vegetarian", "", "REG-DEMO-006", "registered"),
            ("Sara Khan", "sara.khan@example.com", "9876500007", 26, "Female", "Professional", "Marketing", "GreenGrid", "Hyderabad", "Telangana", "Innovation Summit", "Standard", "Vegetarian", "", "REG-DEMO-007", "registered"),
            ("Manav Patel", "manav.patel@example.com", "9876500008", 24, "Male", "Student", "Computer Science", "Tech College", "Surat", "Gujarat", "Innovation Summit", "Student", "Vegetarian", "", "REG-DEMO-008", "registered"),
        ]
        cursor.executemany("""INSERT INTO attendees
            (full_name,email,phone,age,gender,role,department,college,city,state,
             event_name,registration_type,food_preference,special_requirements,
             registration_id,status,checked_in,checkin_time)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,
                    CASE WHEN ? = 'checked_in' THEN 1 ELSE 0 END,
                    CASE WHEN ? = 'checked_in' THEN datetime('now','localtime') ELSE NULL END)""",
            [item[:-1] + (item[-1], item[-1], item[-1]) for item in demo_attendees])
    if cursor.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0:
        venues_by_name = {row["name"]: row["id"] for row in cursor.execute("SELECT id,name FROM venues")}
        speakers_by_name = {row["name"]: row["id"] for row in cursor.execute("SELECT id,name FROM speakers")}
        cursor.executemany("""INSERT INTO sessions
            (title,speaker_id,venue_id,start_time,end_time,expected_attendees,
             session_type,required_equipment,required_expertise,status)
            VALUES (?,?,?,?,?,?,?,?,?,?)""", [
            ("Opening Keynote: Future of AI", speakers_by_name.get("Dr. Ananya Sharma"), venues_by_name.get("Grand Hall"), "2026-08-11T09:30", "2026-08-11T10:30", 420, "Keynote", "Projector, Wi-Fi, Audio System", "Artificial Intelligence", "Confirmed"),
            ("Building with LLMs", speakers_by_name.get("Dr. Ananya Sharma"), venues_by_name.get("Innovation Lab"), "2026-08-11T11:00", "2026-08-11T12:00", 100, "Seminar", "Projector, Wi-Fi", "Artificial Intelligence, LLMs", "Confirmed"),
            ("Data-Driven Decisions", speakers_by_name.get("Rahul Verma"), venues_by_name.get("Tech Room 1"), "2026-08-11T13:30", "2026-08-11T14:30", 75, "Workshop", "Projector, Wi-Fi", "Data Analytics", "Confirmed"),
            ("From Idea to Startup", speakers_by_name.get("Priya Singh"), venues_by_name.get("Tech Room 2"), "2026-08-11T15:00", "2026-08-11T16:00", 90, "Panel", "Projector, Wi-Fi, Audio System", "Entrepreneurship, Startups", "Confirmed"),
        ])
    if cursor.execute("SELECT COUNT(*) FROM sponsors").fetchone()[0] == 0:
        cursor.executemany("""INSERT INTO sponsors
            (name, company, contact_person, email, tier, amount, contract_status,
             payment_status, deliverables, deliverable_status, performance_score, roi, event_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", [
            ("Aarav Mehta", "NovaTech", "Aarav Mehta", "aarav@novatech.example", "Gold", 25000, "Active", "Paid", "Keynote stage, logo wall", "Complete", 92, 3.8, "Innovation Summit"),
            ("Meera Iyer", "GreenGrid", "Meera Iyer", "meera@greengrid.example", "Silver", 12000, "Confirmed", "Pending", "Eco lounge, social posts", "In Progress", 74, 2.4, "Innovation Summit"),
            ("Kabir Shah", "CloudNine", "Kabir Shah", "kabir@cloudnine.example", "Bronze", 6000, "Negotiating", "Overdue", "Booth, attendee list", "Overdue", 55, 1.2, "Tech Connect"),
        ])
    if cursor.execute("SELECT COUNT(*) FROM incidents").fetchone()[0] == 0:
        cursor.executemany("""INSERT INTO incidents
            (title, description, category, location, event_name, reported_by, assigned_to, priority, severity, status, escalation_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", [
            ("Badge printer offline", "Registration desk printer is not responding.", "Technical", "Registration desk", "Innovation Summit", "Front desk", "IT Team", "High", "High", "Investigating", 1),
            ("Crowd build-up at Hall B", "Queue is blocking the east entrance.", "Crowd Management", "Hall B entrance", "Tech Connect", "Security", "Operations Team", "Critical", "Critical", "Escalated", 2),
            ("First-aid request", "Attendee requested assistance after feeling unwell.", "Medical", "Food court", "Innovation Summit", "Volunteer", "Medical Team", "Medium", "Medium", "Resolved", 0),
        ])
    if cursor.execute("SELECT COUNT(*) FROM operational_alerts").fetchone()[0] == 0:
        cursor.executemany("""INSERT INTO operational_alerts
            (alert_type, message, severity, related_id, recommended_action)
            VALUES (?, ?, ?, ?, ?)""", [
            ("Critical incident", "Crowd build-up at Hall B requires immediate response.", "Critical", 2, "Keep security lead on site and redirect arrivals."),
            ("Payment overdue", "CloudNine sponsorship payment is overdue.", "High", 3, "Contact sponsor and update payment plan."),
        ])

    conn.commit()
    conn.close()
    print(f"[DB] Database initialized at {DATABASE_PATH}")
