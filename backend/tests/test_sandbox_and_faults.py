import pytest
from app.graph.fault_injector import inject_fault, SCENARIOS
from app.graph.sandbox import SandboxManager
from app.db.connection import db_manager

def test_inject_hub_cascade():
    res = inject_fault("hub_cascade", "tenant_a")
    assert res["status"] == "injected"
    assert res["ground_truth_root_cause"] == "auth-service"
    assert res["total_alerts"] >= 5

    # Verify Alert nodes exist in FalkorDB
    g = db_manager.get_graph("tenant_a")
    alert_count = g.query("MATCH (a:Alert) RETURN count(a)").result_set[0][0]
    assert alert_count == res["total_alerts"]

def test_inject_red_herring_noise():
    res = inject_fault("red_herring", "tenant_a")
    assert res["status"] == "injected"
    assert res["ground_truth_root_cause"] == "checkout-service"
    assert res["red_herring_count"] >= 5

    # Verify red herring alerts are flagged
    g = db_manager.get_graph("tenant_a")
    noise_count = g.query("MATCH (a:Alert {is_red_herring: true}) RETURN count(a)").result_set[0][0]
    assert noise_count == res["red_herring_count"]

def test_sandbox_lifecycle():
    # Test creation and deletion of GRAPH.COPY clone
    sandbox_id = SandboxManager.create_sandbox("tenant_a")
    assert sandbox_id.startswith("sim_")

    # Verify clone has same services
    sandbox = db_manager.get_graph(sandbox_id)
    svc_count = sandbox.query("MATCH (s:Service) RETURN count(s)").result_set[0][0]
    assert svc_count > 50

    # Destroy
    SandboxManager.destroy_sandbox(sandbox_id)

def test_simulation_safe_remedy():
    # Scaling replicas should be APPROVED
    diff = SandboxManager.simulate_remediation("tenant_a", "scale_replicas", "auth-service")
    assert diff["safety_status"] == "APPROVED"
    assert diff["action"] == "scale_replicas"
    assert diff["orphaned_services_created"] == 0

def test_simulation_risky_remedy_blocked():
    # Isolating a critical payment hub must be BLOCKED_HIGH_RISK by guard policy
    diff = SandboxManager.simulate_remediation("tenant_a", "isolate_service", "payment-gateway")
    assert diff["safety_status"] == "BLOCKED_HIGH_RISK"
    assert "severing" in diff["safety_reason"]
    assert diff["target_service"] == "payment-gateway"
