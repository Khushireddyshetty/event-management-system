"""Agent orchestration facade for the Event Intelligence Engine."""

from intelligence import analyze


def run(conn, persist=True):
    """Run all lightweight agents and combine their data-backed findings."""
    result = analyze(conn, persist=persist)
    result["orchestration"] = {
        "status": "completed",
        "agents_consulted": [agent["agent_name"] for agent in result["agents"] if agent["used"]],
        "decision": "prioritized by risk severity and source module",
    }
    return result
