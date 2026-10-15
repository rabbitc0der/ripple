import pytest
from app.db.connection import db_manager

GRAPH_NAME = "tenant_a"

def test_blast_radius():
    g = db_manager.get_graph(GRAPH_NAME)
    query = """
    MATCH p = (root:Service {id: $service_id})<-[:CALLS*1..6]-(dependent:Service)
    WITH dependent, min(length(p)) AS depth
    RETURN dependent.id AS service_id, depth
    ORDER BY depth ASC
    """
    res = g.query(query, {"service_id": "auth-service"})
    assert len(res.result_set) > 0
    services = [row[0] for row in res.result_set]
    # Web frontend and mobile bff call auth-service directly
    assert "web-frontend" in services or "mobile-bff" in services

def test_root_cause_ranking():
    g = db_manager.get_graph(GRAPH_NAME)
    query = """
    UNWIND $alerting_ids AS aid
    MATCH (a:Service {id: aid})-[:CALLS*0..5]->(r:Service)
    WITH r, count(DISTINCT a) AS covered_alerts
    MATCH (r)<-[:CALLS*0..5]-(dependent:Service)
    WITH r, covered_alerts, count(DISTINCT dependent) AS total_dependents
    WITH r, covered_alerts, total_dependents,
         (toFloat(covered_alerts) / $total_alerts) AS recall,
         (toFloat(covered_alerts) / total_dependents) AS precision
    RETURN r.id AS candidate_id, recall, precision
    ORDER BY covered_alerts DESC, precision DESC
    LIMIT 5
    """
    # Simulate alerts firing on callers of auth-service
    alerts = ["web-frontend", "mobile-bff", "api-gateway"]
    res = g.query(query, {"alerting_ids": alerts, "total_alerts": len(alerts)})
    assert len(res.result_set) > 0
    top_candidates = [row[0] for row in res.result_set]
    # Common callee must be in the candidates
    assert any(c in top_candidates for c in ["auth-service", "cart-service", "api-gateway"])

def test_rule_outs_path_absence():
    g = db_manager.get_graph(GRAPH_NAME)
    query = """
    UNWIND $alerting_ids AS aid
    MATCH (a:Service {id: aid})-[:CALLS*0..5]->(reachable:Service)
    WITH collect(DISTINCT reachable.id) AS reachable_ids
    MATCH (candidate:Service)
    WHERE NOT candidate.id IN reachable_ids
    RETURN candidate.id AS ruled_out_id
    LIMIT 10
    """
    alerts = ["cart-service"]
    res = g.query(query, {"alerting_ids": alerts})
    assert len(res.result_set) > 0
    ruled_out = [row[0] for row in res.result_set]
    # Ingress and web frontend do NOT depend on cart-service (cart-service is downstream of them)
    assert "public-ingress" in ruled_out or "api-gateway" in ruled_out

def test_procedural_memory_ranking():
    g = db_manager.get_graph(GRAPH_NAME)
    query = """
    MATCH (st:Step)-[e:EFFECTIVE_FOR]->(fm:FailureMode {name: $failure_mode})
    WITH st, fm, e,
         ((toFloat(e.successes) + 1.0) / (toFloat(e.attempts) + 2.0)) AS bayesian_confidence
    RETURN st.id AS step_id, bayesian_confidence
    ORDER BY bayesian_confidence DESC
    """
    res = g.query(query, {"failure_mode": "BAD_DEPLOY"})
    assert len(res.result_set) >= 2
    top_step = res.result_set[0][0]
    # Rollback must beat Restart for BAD_DEPLOY
    assert top_step == "step-rollback"
