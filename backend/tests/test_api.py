import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.connection import db_manager

client = TestClient(app)

def test_api_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["falkordb"]["status"] == "healthy"
    assert "latency_ms" in data["falkordb"]

def test_api_scenarios():
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    assert len(scenarios) == 4
    ids = [s["id"] for s in scenarios]
    assert "hub_cascade" in ids
    assert "red_herring" in ids

def test_api_topology():
    response = client.get("/api/topology")
    assert response.status_code == 200
    data = response.json()
    assert data["total_nodes"] >= 50
    assert data["total_edges"] >= 60
    assert "nodes" in data
    assert "edges" in data

def test_api_fault_injection_and_diagnosis_flow():
    # 1. Inject Hub Cascade fault
    inj_res = client.post("/api/fault/inject", json={"scenario_id": "hub_cascade"})
    assert inj_res.status_code == 200
    inj_data = inj_res.json()
    assert inj_data["ground_truth_root_cause"] == "auth-service"

    # 2. Run Graph-Native Diagnosis
    diag_res = client.post("/api/diagnose", json={"graph_mode": True})
    assert diag_res.status_code == 200
    diag_data = diag_res.json()
    assert diag_data["status"] == "diagnosed"
    assert diag_data["root_cause"]["service_id"] == "auth-service"
    assert diag_data["blast_radius"]["count"] > 0
    assert diag_data["proof_by_path_absence"]["ruled_out_count"] > 0
    assert "receipts" in diag_data

    # 3. Test Graph OFF Baseline Comparison
    base_res = client.post("/api/diagnose", json={"graph_mode": False})
    assert base_res.status_code == 200
    base_data = base_res.json()
    assert base_data["mode"] == "GRAPH_OFF_BASELINE"
    assert "flaw" in base_data["predicted_root_cause"]

def test_api_simulation_and_approval():
    # 1. Run counterfactual simulation
    sim_res = client.post("/api/simulate", json={
        "action": "scale_replicas",
        "target_service": "auth-service"
    })
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert sim_data["safety_status"] == "APPROVED"
    assert "delta_blast_radius" in sim_data

    # 2. Approve remediation
    appr_res = client.post("/api/approve", json={
        "step_id": "step-scale-up",
        "failure_mode": "THREADPOOL_EXHAUSTION",
        "outcome": 1
    })
    assert appr_res.status_code == 200
    appr_data = appr_res.json()
    assert appr_data["status"] == "resolved"
    assert "new_confidence" in appr_data["procedural_memory_update"]

def test_api_reset():
    res = client.post("/api/reset")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "reset_successful"
