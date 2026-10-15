from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from app.config import settings
from app.db.connection import db_manager
from app.graph.fault_injector import inject_fault, SCENARIOS
from app.graph.sandbox import SandboxManager
from app.agent.engine import RippleAgent
from app.agent.baseline import run_flat_baseline

app = FastAPI(
    title="Ripple API",
    description="Autonomous SRE Agent & Explainable Digital Twin powered by FalkorDB",
    version="0.1.0"
)

# Enable CORS for local Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Request / Response Models ---
class InjectRequest(BaseModel):
    scenario_id: str
    graph_name: Optional[str] = "tenant_a"

class DiagnoseRequest(BaseModel):
    graph_mode: bool = True
    graph_name: Optional[str] = "tenant_a"

class SimulateRequest(BaseModel):
    action: str
    target_service: str
    graph_name: Optional[str] = "tenant_a"

class ApproveRequest(BaseModel):
    step_id: str
    failure_mode: str
    outcome: int = 1  # 1 for resolved, 0 for failed
    graph_name: Optional[str] = "tenant_a"


# --- API Routes ---
@app.get("/api/health")
def get_health():
    """Healthcheck endpoint returning FalkorDB connection status & latency."""
    health = db_manager.check_health()
    return {
        "app": "Ripple SRE Digital Twin",
        "version": "0.1.0",
        "llm_mode": settings.LLM_MODE,
        "falkordb": health
    }


@app.get("/api/scenarios")
def get_scenarios():
    """Returns available pre-configured hero scenarios."""
    return [
        {
            "id": k,
            "title": v["title"],
            "description": v["description"],
            "root_cause_service": v["root_cause_service"],
            "failure_mode": v["failure_mode"],
            "symptom_count": len(v["affected_services"]),
            "noise_count": len(v["red_herrings"])
        }
        for k, v in SCENARIOS.items()
    ]


@app.get("/api/topology")
def get_topology(graph_name: str = "tenant_a"):
    """
    Returns full graph topology formatted for Cytoscape.js canvas rendering.
    Includes nodes with tiers and active alert states, and directed CALLS edges.
    """
    g = db_manager.get_graph(graph_name)
    
    # 1. Fetch Services & their active alerts
    nodes_res = g.query("""
        MATCH (s:Service)
        OPTIONAL MATCH (a:Alert)-[:FIRED_ON]->(s)
        OPTIONAL MATCH (t:Team)-[:OWNS]->(s)
        RETURN s.id AS id,
               s.name AS name,
               s.tier AS tier,
               s.kind AS kind,
               s.slo_ms AS slo_ms,
               t.name AS team,
               collect(a.id) AS alert_ids,
               count(a) AS alert_count
    """)

    nodes = []
    for r in nodes_res.result_set:
        has_alerts = r[7] > 0
        nodes.append({
            "data": {
                "id": r[0],
                "name": r[1],
                "tier": r[2],
                "kind": r[3],
                "slo_ms": r[4],
                "team": r[5] or "Unassigned",
                "alert_count": r[7],
                "status": "alerting" if has_alerts else "healthy"
            }
        })

    # 2. Fetch Directed CALLS relationships
    edges_res = g.query("""
        MATCH (src:Service)-[r:CALLS]->(dst:Service)
        RETURN src.id AS source, dst.id AS target, r.p99_ms AS p99_ms
    """)

    edges = []
    for r in edges_res.result_set:
        edges.append({
            "data": {
                "id": f"{r[0]}->{r[1]}",
                "source": r[0],
                "target": r[1],
                "p99_ms": r[2]
            }
        })

    return {
        "nodes": nodes,
        "edges": edges,
        "total_nodes": len(nodes),
        "total_edges": len(edges)
    }


@app.post("/api/fault/inject")
def trigger_fault(req: InjectRequest):
    """Injects an incident alert storm into the digital twin topology."""
    try:
        res = inject_fault(req.scenario_id, req.graph_name or "tenant_a")
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/diagnose")
def run_diagnosis(req: DiagnoseRequest):
    """
    Diagnoses active incident.
    Supports 'graph_mode=True' (Ripple Agent) vs 'graph_mode=False' (Flat Baseline)
    for the hackathon Graph ON/OFF comparison.
    """
    target = req.graph_name or "tenant_a"
    if not req.graph_mode:
        return run_flat_baseline(target)

    agent = RippleAgent(target)
    return agent.diagnose()


@app.get("/api/stream/diagnose")
def stream_diagnosis(graph_name: str = "tenant_a"):
    """Server-Sent Events (SSE) endpoint streaming real-time agent reasoning steps."""
    agent = RippleAgent(graph_name)
    return StreamingResponse(agent.stream_diagnose(), media_type="text/event-stream")


@app.post("/api/simulate")
def run_simulation(req: SimulateRequest):
    """Executes a counterfactual 'what-if' simulation on an isolated GRAPH.COPY clone."""
    target = req.graph_name or "tenant_a"
    diff = SandboxManager.simulate_remediation(target, req.action, req.target_service)
    return diff


@app.post("/api/approve")
def approve_and_execute(req: ApproveRequest):
    """
    Executes human-approved remediation, updates procedural memory weights,
    and resolves the active incident in FalkorDB.
    """
    target = req.graph_name or "tenant_a"
    g = db_manager.get_graph(target)

    # 1. Update Bayesian procedural edge on FalkorDB
    update_res = g.query("""
        MATCH (st:Step {id: $step_id})-[e:EFFECTIVE_FOR]->(fm:FailureMode {name: $failure_mode})
        SET e.attempts = e.attempts + 1,
            e.successes = e.successes + $outcome,
            e.last_updated = timestamp()
        RETURN st.name AS remedy,
               fm.name AS failure_mode,
               e.attempts AS attempts,
               e.successes AS successes,
               round(((toFloat(e.successes) + 1.0) / (toFloat(e.attempts) + 2.0)) * 1000.0) / 1000.0 AS new_confidence
    """, {
        "step_id": req.step_id,
        "failure_mode": req.failure_mode,
        "outcome": req.outcome
    })

    # 2. Clear active alerts & resolve incident
    g.query("MATCH (a:Alert) DETACH DELETE a")
    g.query("MATCH (i:Incident {status: 'active'}) SET i.status = 'resolved'")

    if update_res.result_set:
        r = update_res.result_set[0]
        learning_update = {
            "remedy": r[0],
            "failure_mode": r[1],
            "attempts": r[2],
            "successes": r[3],
            "new_confidence": r[4]
        }
    else:
        learning_update = {"status": "edge_not_found"}

    return {
        "status": "resolved",
        "action_executed": req.step_id,
        "procedural_memory_update": learning_update
    }


@app.post("/api/reset")
def reset_to_golden(graph_name: str = "tenant_a"):
    """Resets the graph to the pristine golden state in < 15ms via GRAPH.COPY."""
    try:
        try:
            db_manager.execute_raw("GRAPH.DELETE", graph_name)
        except Exception:
            pass
        db_manager.execute_raw("GRAPH.COPY", "template_golden", graph_name)
        return {"status": "reset_successful", "graph": graph_name, "source": "template_golden"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

