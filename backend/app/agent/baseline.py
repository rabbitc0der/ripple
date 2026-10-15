from typing import Dict, Any, List
from app.db.connection import db_manager

def run_flat_baseline(graph_name: str = "tenant_a") -> Dict[str, Any]:
    """
    Executes the Naive Non-Graph Baseline (Graph OFF Mode).
    Blames the service with the highest number of raw alert symptoms.
    Lacks topological reachability, cannot calculate blast radius,
    and consistently falls for red herring noisy neighbors.
    """
    g = db_manager.get_graph(graph_name)
    
    # 1. Fetch all active alerts without graph traversal
    res = g.query("""
        MATCH (a:Alert)-[:FIRED_ON]->(s:Service)
        RETURN s.id AS service_id, s.name AS service_name, count(a) AS alert_count
        ORDER BY alert_count DESC
    """)
    
    if not res.result_set:
        return {
            "mode": "GRAPH_OFF_BASELINE",
            "status": "no_alerts",
            "message": "No active alerts in the system."
        }

    rows = res.result_set
    top_culprit = rows[0]
    
    breakdown = [
        {"service_id": r[0], "service_name": r[1], "alert_count": r[2]}
        for r in rows
    ]

    return {
        "mode": "GRAPH_OFF_BASELINE",
        "predicted_root_cause": {
            "id": top_culprit[0],
            "name": top_culprit[1],
            "reason": f"Service emitted the highest raw alert count ({top_culprit[2]} alerts)",
            "confidence": 0.45,
            "flaw": "Naive count ignores dependency directions; vulnerable to observability spam & red herrings."
        },
        "all_candidates_by_count": breakdown,
        "blast_radius": "UNKNOWN (Cannot be computed without graph edge traversals)",
        "ruled_out_services": "NONE (Proof by path absence requires topological reachability)",
        "why_it_fails": (
            "A flat relational or vector store counts symptoms, mistaking high-volume logging "
            "or downstream caller timeouts for the actual root cause."
        )
    }
