"""Milestone 4 intelligence and orchestration APIs."""

from flask import Blueprint, jsonify

from database import get_db
from intelligence import analyze
from orchestrator import run


intelligence_bp = Blueprint("intelligence", __name__)


def _latest(conn):
    row = conn.execute(
        "SELECT * FROM intelligence_analyses ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if not row:
        return None
    analysis = dict(row)
    analysis_id = analysis["id"]
    analysis["event_health"] = analysis.pop("health_score")
    analysis["health_status"] = analysis.pop("health_status")
    analysis["timestamp"] = analysis.pop("created_at")
    analysis["risks"] = [
        dict(item) for item in conn.execute(
            "SELECT title,description,severity,source,created_at AS detected_at,recommended_action FROM intelligence_risks WHERE analysis_id=? ORDER BY CASE severity WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END, id",
            (analysis_id,),
        ).fetchall()
    ]
    analysis["recommendations"] = [
        dict(item) for item in conn.execute(
            "SELECT recommendation,reason,priority,related_module,suggested_action FROM intelligence_recommendations WHERE analysis_id=? ORDER BY CASE priority WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END, id",
            (analysis_id,),
        ).fetchall()
    ]
    agents = []
    for item in conn.execute(
        "SELECT agent_name,status,findings,recommendations,created_at AS last_execution FROM agent_runs WHERE analysis_id=? ORDER BY id",
        (analysis_id,),
    ).fetchall():
        value = dict(item)
        import json
        try:
            value["recommendations"] = json.loads(value["recommendations"] or "[]")
        except (TypeError, ValueError):
            value["recommendations"] = []
        value["used"] = True
        agents.append(value)
    analysis["agents"] = agents
    # KPI and trend data stays live even when the page is viewing the last
    # persisted analysis snapshot.
    current = analyze(conn, persist=False)
    analysis["kpis"] = current["kpis"]
    analysis["trends"] = current["trends"]
    return analysis


def _fresh(persist=False):
    conn = get_db()
    try:
        return analyze(conn, persist=persist)
    finally:
        conn.close()


@intelligence_bp.route("/intelligence/overview", methods=["GET"])
def overview():
    # Overview is always calculated from current source tables so changes show
    # up immediately, even before the user presses Run Analysis.
    return jsonify(_fresh())


@intelligence_bp.route("/intelligence/health", methods=["GET"])
def health():
    result = _fresh()
    return jsonify({
        "event_health": result["event_health"], "health_status": result["health_status"],
        "summary": result["summary"], "timestamp": result["timestamp"],
    })


@intelligence_bp.route("/intelligence/kpis", methods=["GET"])
def kpis():
    return jsonify(_fresh()["kpis"])


@intelligence_bp.route("/intelligence/risks", methods=["GET"])
def risks():
    return jsonify({"risks": _fresh()["risks"]})


@intelligence_bp.route("/intelligence/recommendations", methods=["GET"])
def recommendations():
    return jsonify({"recommendations": _fresh()["recommendations"]})


@intelligence_bp.route("/intelligence/trends", methods=["GET"])
def trends():
    return jsonify({"trends": _fresh()["trends"]})


@intelligence_bp.route("/intelligence/analyze", methods=["POST"])
@intelligence_bp.route("/intelligence/refresh", methods=["POST"])
def analyze_now():
    conn = get_db()
    try:
        result = run(conn, persist=True)
        return jsonify(result)
    finally:
        conn.close()


@intelligence_bp.route("/orchestrator/analyze", methods=["POST"])
@intelligence_bp.route("/orchestrator/run", methods=["POST"])
def orchestrator_run():
    conn = get_db()
    try:
        return jsonify(run(conn, persist=True))
    finally:
        conn.close()


@intelligence_bp.route("/orchestrator/status", methods=["GET"])
def orchestrator_status():
    conn = get_db()
    try:
        latest = _latest(conn)
        return jsonify({
            "status": "ready",
            "last_analysis": latest["timestamp"] if latest else None,
            "agents": latest["agents"] if latest else [],
        })
    finally:
        conn.close()


@intelligence_bp.route("/intelligence/latest", methods=["GET"])
def latest():
    conn = get_db()
    try:
        result = _latest(conn)
        if result:
            return jsonify(result)
        return jsonify(_fresh(persist=False))
    finally:
        conn.close()
