import time
import uuid
from typing import Dict, Any, List
from app.db.connection import db_manager

SCENARIOS = {
    "hub_cascade": {
        "title": "Platform Hub Cascade (Auth Exhaustion)",
        "description": "Flash sale traffic spike exhausted connection pool on auth-service, cascading up to BFFs and Commerce.",
        "root_cause_service": "auth-service",
        "failure_mode": "THREADPOOL_EXHAUSTION",
        "affected_services": [
            {"service_id": "auth-service", "metric": "threadpool.active_threads", "value": 99.8},
            {"service_id": "web-frontend", "metric": "http.latency_p99_ms", "value": 1820.0},
            {"service_id": "mobile-bff", "metric": "http.latency_p99_ms", "value": 2100.0},
            {"service_id": "cart-service", "metric": "http.5xx_rate", "value": 8.5},
            {"service_id": "checkout-service", "metric": "http.5xx_rate", "value": 12.1},
        ],
        "red_herrings": []
    },
    "red_herring": {
        "title": "The Red Herring Storm (Noisy Observability vs Hidden Deploy)",
        "description": "Log aggregator buffer overflow fires 12 noisy alerts, while subtle checkout schema deploy breaks order processing.",
        "root_cause_service": "checkout-service",
        "failure_mode": "BAD_DEPLOY",
        "affected_services": [
            {"service_id": "checkout-service", "metric": "order.serialization_errors", "value": 45.0},
            {"service_id": "order-processor", "metric": "queue.dlq_rate", "value": 32.0},
            {"service_id": "mobile-bff", "metric": "http.5xx_rate", "value": 9.4},
        ],
        "red_herrings": [
            {"service_id": "log-aggregator", "metric": "buffer.overflow_events", "value": 1250.0},
            {"service_id": "log-aggregator", "metric": "disk.io_saturation", "value": 98.4},
            {"service_id": "log-aggregator", "metric": "memory.heap_used_pct", "value": 94.2},
            {"service_id": "prom-metrics-collector", "metric": "scrape.timeout_count", "value": 310.0},
            {"service_id": "prom-metrics-collector", "metric": "cpu.utilization", "value": 92.0},
            {"service_id": "audit-trail-logger", "metric": "queue.backlog_size", "value": 4200.0},
        ]
    },
    "cache_stampede": {
        "title": "Catalog Redis Cache Stampede",
        "description": "Simultaneous TTL expiration on top 100 SKUs causes thundering herd to mongo-catalog-db.",
        "root_cause_service": "catalog-service",
        "failure_mode": "CACHE_STAMPEDE",
        "affected_services": [
            {"service_id": "catalog-service", "metric": "cache.hit_ratio", "value": 0.12},
            {"service_id": "cart-service", "metric": "http.latency_p99_ms", "value": 1450.0},
            {"service_id": "search-indexer", "metric": "http.5xx_rate", "value": 11.2},
            {"service_id": "recommendation-service", "metric": "http.timeout_rate", "value": 18.0},
            {"service_id": "web-frontend", "metric": "http.latency_p99_ms", "value": 2400.0},
        ],
        "red_herrings": []
    },
    "risky_remedy": {
        "title": "Payment Gateway Timeout & Risky Remediation",
        "description": "Third-party payment connector latency spike. Isolating payment-gateway isolates order processing and wallet.",
        "root_cause_service": "payment-gateway",
        "failure_mode": "CIRCUIT_BREAKER_TRIPPED",
        "affected_services": [
            {"service_id": "payment-gateway", "metric": "upstream.timeout_rate", "value": 34.0},
            {"service_id": "order-processor", "metric": "payment.declined_retry_count", "value": 520.0},
            {"service_id": "wallet-service", "metric": "http.latency_p99_ms", "value": 1100.0},
            {"service_id": "checkout-service", "metric": "http.5xx_rate", "value": 28.0},
        ],
        "red_herrings": []
    }
}


def inject_fault(scenario_id: str, graph_name: str = "tenant_a") -> Dict[str, Any]:
    """
    Injects a real-time alert storm into the specified FalkorDB graph.
    Cleans previous active alerts and attaches new Alert nodes to affected Services.
    """
    if scenario_id not in SCENARIOS:
        raise ValueError(f"Unknown scenario '{scenario_id}'. Available: {list(SCENARIOS.keys())}")

    scenario = SCENARIOS[scenario_id]
    g = db_manager.get_graph(graph_name)

    # 1. Clean previous active alerts & active incident
    g.query("MATCH (a:Alert) DETACH DELETE a")
    g.query("MATCH (i:Incident) WHERE i.status = 'active' OR i.id STARTS WITH 'inc_active' DETACH DELETE i")

    # 2. Create Active Incident node
    incident_id = f"inc_active_{scenario_id}"
    now = int(time.time())
    g.query("""
        CREATE (i:Incident {
            id: $id,
            title: $title,
            summary: $summary,
            status: 'active',
            ts: $ts,
            ground_truth_root_cause: $root_cause,
            failure_mode: $mode
        })
    """, {
        "id": incident_id,
        "title": scenario["title"],
        "summary": scenario["description"],
        "ts": now,
        "root_cause": scenario["root_cause_service"],
        "mode": scenario["failure_mode"]
    })

    # 3. Create Alert nodes and link to Services and Incident
    all_alerts = scenario["affected_services"] + scenario["red_herrings"]
    created_alerts = []

    for idx, alert_spec in enumerate(all_alerts):
        alert_id = f"alt_{scenario_id}_{idx+1:02d}"
        is_red_herring = alert_spec in scenario["red_herrings"]
        
        g.query("""
            MATCH (i:Incident {id: $inc_id})
            MATCH (s:Service {id: $svc_id})
            CREATE (a:Alert {
                id: $alert_id,
                metric: $metric,
                value: $value,
                severity: 'critical',
                is_red_herring: $is_noise,
                ts: $ts
            })
            CREATE (i)-[:HAD_ALERT]->(a)
            CREATE (a)-[:FIRED_ON]->(s)
        """, {
            "inc_id": incident_id,
            "svc_id": alert_spec["service_id"],
            "alert_id": alert_id,
            "metric": alert_spec["metric"],
            "value": float(alert_spec["value"]),
            "is_noise": is_red_herring,
            "ts": now
        })
        created_alerts.append({
            "alert_id": alert_id,
            "service_id": alert_spec["service_id"],
            "metric": alert_spec["metric"],
            "value": alert_spec["value"],
            "is_red_herring": is_red_herring
        })

    return {
        "status": "injected",
        "scenario_id": scenario_id,
        "incident_id": incident_id,
        "title": scenario["title"],
        "ground_truth_root_cause": scenario["root_cause_service"],
        "total_alerts": len(created_alerts),
        "red_herring_count": len(scenario["red_herrings"]),
        "alerts": created_alerts
    }
