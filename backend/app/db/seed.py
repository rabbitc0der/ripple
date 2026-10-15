"""
Deterministic Seed Generator for Ripple SRE Digital Twin.
Builds a realistic 60-microservice graph topology with dependencies, teams,
engineers, historical incidents, failure modes, runbooks, and procedural memory.
"""
import time
import random
from typing import Dict, Any, List
from app.db.connection import db_manager
from app.config import settings

SERVICES_SPEC = [
    # Tier 1: Ingress & Gateways (High traffic, caller of Tier 2)
    {"id": "api-gateway", "name": "API Gateway", "tier": 1, "kind": "gateway", "slo_ms": 50.0},
    {"id": "web-frontend", "name": "Web Frontend BFF", "tier": 1, "kind": "bff", "slo_ms": 100.0},
    {"id": "mobile-bff", "name": "Mobile App BFF", "tier": 1, "kind": "bff", "slo_ms": 120.0},
    {"id": "public-ingress", "name": "Public Ingress Proxy", "tier": 1, "kind": "proxy", "slo_ms": 30.0},
    {"id": "cdn-origin", "name": "CDN Origin Shield", "tier": 1, "kind": "cdn", "slo_ms": 40.0},
    
    # Tier 2: Identity, Auth & Users
    {"id": "auth-service", "name": "Authentication Hub", "tier": 2, "kind": "auth", "slo_ms": 45.0},
    {"id": "session-mgr", "name": "Session Manager", "tier": 2, "kind": "auth", "slo_ms": 25.0},
    {"id": "jwt-vault", "name": "JWT Key Vault", "tier": 2, "kind": "crypto", "slo_ms": 15.0},
    {"id": "oauth-broker", "name": "OAuth2 / SSO Broker", "tier": 2, "kind": "auth", "slo_ms": 80.0},
    {"id": "user-directory", "name": "User Directory Service", "tier": 2, "kind": "domain", "slo_ms": 60.0},
    {"id": "profile-service", "name": "User Profile Service", "tier": 2, "kind": "domain", "slo_ms": 70.0},
    {"id": "preference-store", "name": "User Preferences Store", "tier": 2, "kind": "domain", "slo_ms": 40.0},

    # Tier 2: Commerce & Orders
    {"id": "cart-service", "name": "Shopping Cart Service", "tier": 2, "kind": "commerce", "slo_ms": 80.0},
    {"id": "checkout-service", "name": "Checkout Orchestrator", "tier": 2, "kind": "commerce", "slo_ms": 150.0},
    {"id": "order-processor", "name": "Order Processor Engine", "tier": 2, "kind": "commerce", "slo_ms": 120.0},
    {"id": "order-history", "name": "Order History Query Service", "tier": 2, "kind": "commerce", "slo_ms": 90.0},
    {"id": "invoice-service", "name": "Invoice Generator", "tier": 2, "kind": "billing", "slo_ms": 200.0},
    {"id": "tax-calculator", "name": "Tax & Duty Calculator", "tier": 2, "kind": "billing", "slo_ms": 65.0},
    {"id": "discount-engine", "name": "Promotions & Discounts", "tier": 2, "kind": "commerce", "slo_ms": 50.0},

    # Tier 2: Catalog & Search
    {"id": "catalog-service", "name": "Product Catalog Service", "tier": 2, "kind": "catalog", "slo_ms": 70.0},
    {"id": "search-indexer", "name": "Search & Query Engine", "tier": 2, "kind": "search", "slo_ms": 85.0},
    {"id": "recommendation-service", "name": "AI Recommendation Service", "tier": 2, "kind": "ml", "slo_ms": 110.0},
    {"id": "inventory-service", "name": "Inventory Tracker", "tier": 2, "kind": "catalog", "slo_ms": 60.0},
    {"id": "pricing-engine", "name": "Dynamic Pricing Engine", "tier": 2, "kind": "catalog", "slo_ms": 55.0},
    {"id": "review-service", "name": "Product Reviews & Ratings", "tier": 2, "kind": "catalog", "slo_ms": 90.0},

    # Tier 2: Payments & Fraud
    {"id": "payment-gateway", "name": "Payment Gateway Adapter", "tier": 2, "kind": "payment", "slo_ms": 180.0},
    {"id": "fraud-detector", "name": "Realtime Fraud Detector", "tier": 2, "kind": "security", "slo_ms": 90.0},
    {"id": "stripe-connector", "name": "Stripe API Connector", "tier": 2, "kind": "integration", "slo_ms": 250.0},
    {"id": "paypal-connector", "name": "PayPal API Connector", "tier": 2, "kind": "integration", "slo_ms": 280.0},
    {"id": "ledger-service", "name": "Double-Entry Ledger", "tier": 2, "kind": "accounting", "slo_ms": 100.0},
    {"id": "wallet-service", "name": "Customer Wallet & Credit", "tier": 2, "kind": "payment", "slo_ms": 75.0},

    # Tier 2: Fulfillment & Logistics
    {"id": "fulfillment-service", "name": "Fulfillment Coordinator", "tier": 2, "kind": "logistics", "slo_ms": 140.0},
    {"id": "warehouse-router", "name": "Warehouse Router", "tier": 2, "kind": "logistics", "slo_ms": 110.0},
    {"id": "shipping-service", "name": "Shipping Rate Calculator", "tier": 2, "kind": "logistics", "slo_ms": 130.0},
    {"id": "tracking-service", "name": "Package Tracking Service", "tier": 2, "kind": "logistics", "slo_ms": 95.0},
    {"id": "courier-gateway", "name": "FedEx/UPS Gateway", "tier": 2, "kind": "integration", "slo_ms": 300.0},

    # Tier 2: Notification & Messaging
    {"id": "notification-dispatcher", "name": "Notification Dispatcher", "tier": 2, "kind": "comms", "slo_ms": 80.0},
    {"id": "email-service", "name": "Transactional Email Sender", "tier": 2, "kind": "comms", "slo_ms": 150.0},
    {"id": "sms-gateway", "name": "SMS Alert Gateway", "tier": 2, "kind": "comms", "slo_ms": 200.0},
    {"id": "push-service", "name": "Push Notification Hub", "tier": 2, "kind": "comms", "slo_ms": 120.0},
    {"id": "webhook-dispatcher", "name": "Customer Webhook Dispatcher", "tier": 2, "kind": "comms", "slo_ms": 160.0},

    # Tier 3: Databases & Caches (Shared Backing Services)
    {"id": "postgres-primary", "name": "Postgres Primary DB", "tier": 3, "kind": "database", "slo_ms": 15.0},
    {"id": "postgres-replica-1", "name": "Postgres Read Replica 1", "tier": 3, "kind": "database", "slo_ms": 10.0},
    {"id": "postgres-replica-2", "name": "Postgres Read Replica 2", "tier": 3, "kind": "database", "slo_ms": 10.0},
    {"id": "redis-cluster-master", "name": "Redis Primary Cluster", "tier": 3, "kind": "cache", "slo_ms": 2.0},
    {"id": "redis-session-cache", "name": "Redis Session Cache", "tier": 3, "kind": "cache", "slo_ms": 2.5},
    {"id": "elasticsearch-cluster", "name": "Elasticsearch Search Cluster", "tier": 3, "kind": "search-db", "slo_ms": 30.0},
    {"id": "mongo-catalog-db", "name": "MongoDB Product Catalog", "tier": 3, "kind": "database", "slo_ms": 20.0},
    {"id": "timescale-metrics-db", "name": "TimescaleDB Telemetry Store", "tier": 3, "kind": "database", "slo_ms": 25.0},

    # Tier 3: Queues & Event Streaming
    {"id": "kafka-cluster", "name": "Kafka Event Bus", "tier": 3, "kind": "queue", "slo_ms": 8.0},
    {"id": "rabbitmq-tasks", "name": "RabbitMQ Worker Queue", "tier": 3, "kind": "queue", "slo_ms": 12.0},
    {"id": "event-stream-router", "name": "Event Stream Consumer", "tier": 3, "kind": "streaming", "slo_ms": 15.0},

    # Tier 3: Telemetry, Observability & Red Herrings
    {"id": "log-aggregator", "name": "Fluentd Log Aggregator", "tier": 3, "kind": "observability", "slo_ms": 50.0},
    {"id": "prom-metrics-collector", "name": "Prometheus Collector", "tier": 3, "kind": "observability", "slo_ms": 40.0},
    {"id": "jaeger-collector", "name": "Jaeger Trace Collector", "tier": 3, "kind": "observability", "slo_ms": 45.0},
    {"id": "audit-trail-logger", "name": "Compliance Audit Logger", "tier": 3, "kind": "observability", "slo_ms": 60.0},
    {"id": "analytics-sync-worker", "name": "Analytics Warehouse Sync", "tier": 3, "kind": "analytics", "slo_ms": 500.0},
    {"id": "health-checker-daemon", "name": "Global Synthetic Probe", "tier": 3, "kind": "monitoring", "slo_ms": 30.0},
]

CALLS_SPEC = [
    # Ingress -> Gateways / BFFs
    ("public-ingress", "api-gateway", 12.0),
    ("cdn-origin", "public-ingress", 8.0),
    ("api-gateway", "web-frontend", 20.0),
    ("api-gateway", "mobile-bff", 22.0),

    # Gateways -> Domain Hubs
    ("web-frontend", "auth-service", 15.0),
    ("web-frontend", "cart-service", 35.0),
    ("web-frontend", "catalog-service", 25.0),
    ("web-frontend", "search-indexer", 30.0),
    ("web-frontend", "user-directory", 22.0),
    ("web-frontend", "order-history", 40.0),

    ("mobile-bff", "auth-service", 16.0),
    ("mobile-bff", "cart-service", 38.0),
    ("mobile-bff", "catalog-service", 28.0),
    ("mobile-bff", "checkout-service", 55.0),

    # Auth Hub Dependencies
    ("auth-service", "session-mgr", 10.0),
    ("auth-service", "jwt-vault", 6.0),
    ("auth-service", "oauth-broker", 35.0),
    ("auth-service", "user-directory", 18.0),
    ("session-mgr", "redis-session-cache", 2.0),
    ("user-directory", "postgres-primary", 8.0),
    ("user-directory", "postgres-replica-1", 5.0),
    ("profile-service", "user-directory", 12.0),
    ("preference-store", "postgres-replica-2", 7.0),

    # Commerce & Checkout Flow
    ("cart-service", "auth-service", 15.0),
    ("cart-service", "catalog-service", 18.0),
    ("cart-service", "pricing-engine", 14.0),
    ("cart-service", "redis-cluster-master", 3.0),
    ("checkout-service", "auth-service", 16.0),
    ("checkout-service", "cart-service", 25.0),
    ("checkout-service", "order-processor", 40.0),
    ("checkout-service", "tax-calculator", 20.0),
    ("checkout-service", "discount-engine", 15.0),
    ("checkout-service", "inventory-service", 28.0),
    ("order-processor", "payment-gateway", 70.0),
    ("order-processor", "fulfillment-service", 45.0),
    ("order-processor", "invoice-service", 30.0),
    ("order-processor", "notification-dispatcher", 20.0),
    ("order-processor", "kafka-cluster", 6.0),
    ("order-history", "postgres-replica-1", 12.0),
    ("invoice-service", "postgres-primary", 15.0),

    # Catalog & Search
    ("catalog-service", "mongo-catalog-db", 14.0),
    ("catalog-service", "redis-cluster-master", 2.8),
    ("catalog-service", "inventory-service", 18.0),
    ("search-indexer", "elasticsearch-cluster", 22.0),
    ("search-indexer", "catalog-service", 16.0),
    ("recommendation-service", "catalog-service", 20.0),
    ("recommendation-service", "elasticsearch-cluster", 28.0),
    ("pricing-engine", "redis-cluster-master", 3.2),
    ("review-service", "postgres-replica-2", 10.0),

    # Payments & Fraud
    ("payment-gateway", "fraud-detector", 35.0),
    ("payment-gateway", "ledger-service", 22.0),
    ("payment-gateway", "stripe-connector", 120.0),
    ("payment-gateway", "paypal-connector", 140.0),
    ("payment-gateway", "wallet-service", 30.0),
    ("fraud-detector", "redis-cluster-master", 4.0),
    ("fraud-detector", "postgres-replica-2", 14.0),
    ("ledger-service", "postgres-primary", 12.0),
    ("wallet-service", "postgres-primary", 10.0),

    # Fulfillment & Logistics
    ("fulfillment-service", "warehouse-router", 30.0),
    ("fulfillment-service", "shipping-service", 40.0),
    ("fulfillment-service", "rabbitmq-tasks", 8.0),
    ("shipping-service", "courier-gateway", 160.0),
    ("warehouse-router", "postgres-primary", 14.0),
    ("tracking-service", "courier-gateway", 150.0),

    # Notifications
    ("notification-dispatcher", "email-service", 45.0),
    ("notification-dispatcher", "sms-gateway", 60.0),
    ("notification-dispatcher", "push-service", 30.0),
    ("notification-dispatcher", "webhook-dispatcher", 50.0),
    ("notification-dispatcher", "rabbitmq-tasks", 5.0),

    # Event Streaming Consumers
    ("event-stream-router", "kafka-cluster", 4.0),
    ("event-stream-router", "analytics-sync-worker", 25.0),
    ("analytics-sync-worker", "timescale-metrics-db", 40.0),

    # Observability & Loggers (Mostly isolated sinks)
    ("audit-trail-logger", "postgres-primary", 18.0),
    ("log-aggregator", "elasticsearch-cluster", 35.0),
]

TEAMS_SPEC = [
    {"id": "team-platform", "name": "Platform Core", "channel": "#platform-eng", "oncall": "Alice Chen"},
    {"id": "team-checkout", "name": "Checkout & Payments", "channel": "#payments-oncall", "oncall": "Marcus Vance"},
    {"id": "team-catalog", "name": "Catalog & Discovery", "channel": "#catalog-sre", "oncall": "Priya Sharma"},
    {"id": "team-auth", "name": "Identity & Security", "channel": "#sec-ops", "oncall": "David Kim"},
    {"id": "team-infra", "name": "Infra & Reliability", "channel": "#infra-war-room", "oncall": "Elena Rostova"},
]

PEOPLE_SPEC = [
    {"id": "p-alice", "name": "Alice Chen", "email": "alice@company.com", "role": "Principal SRE", "team": "team-platform"},
    {"id": "p-marcus", "name": "Marcus Vance", "email": "marcus@company.com", "role": "Staff Backend Engineer", "team": "team-checkout"},
    {"id": "p-priya", "name": "Priya Sharma", "email": "priya@company.com", "role": "Senior Infrastructure Eng", "team": "team-catalog"},
    {"id": "p-david", "name": "David Kim", "email": "david@company.com", "role": "Lead Security Engineer", "team": "team-auth"},
    {"id": "p-elena", "name": "Elena Rostova", "email": "elena@company.com", "role": "Site Reliability Lead", "team": "team-infra"},
    {"id": "p-sarah", "name": "Sarah Connor", "email": "sarah@company.com", "role": "DevOps Engineer", "team": "team-platform"},
]

FAILURE_MODES = [
    {"name": "THREADPOOL_EXHAUSTION", "category": "compute", "description": "Worker threads depleted by hung downstream calls"},
    {"name": "BAD_DEPLOY", "category": "release", "description": "New binary version crashes on specific schema or syntax"},
    {"name": "CACHE_STAMPEDE", "category": "caching", "description": "Key expiration causes thundering herd to primary database"},
    {"name": "CONNECTION_LEAK", "category": "database", "description": "Unclosed connections exhaust connection pool"},
    {"name": "REDIS_OOM", "category": "memory", "description": "Eviction policy failure under memory saturation"},
    {"name": "CIRCUIT_BREAKER_TRIPPED", "category": "resilience", "description": "Cascade triggered by cascading latency spikes"},
]

STEPS_SPEC = [
    {"id": "step-restart", "name": "Restart Service Pods", "command": "kubectl rollout restart deployment/{service}", "risk": "low"},
    {"id": "step-rollback", "name": "Rollback Recent Deployment", "command": "kubectl rollout undo deployment/{service}", "risk": "medium"},
    {"id": "step-warm-cache", "name": "Warm Cache & Graceful Reload", "command": "python scripts/warm_cache.py && kubectl rollout restart", "risk": "low"},
    {"id": "step-scale-up", "name": "Scale Deployment Replicas", "command": "kubectl scale deployment/{service} --replicas=+5", "risk": "low"},
    {"id": "step-trip-breaker", "name": "Trip Dependency Circuit Breaker", "command": "consul kv put services/{service}/breaker_open true", "risk": "high"},
    {"id": "step-kill-conns", "name": "Kill Idle Database Connections", "command": "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state='idle';", "risk": "medium"},
]

# Procedural Memory: Bayesian prior attempts & successes
PROCEDURAL_EDGES = [
    # (Step ID, Failure Mode Name, Attempts, Successes)
    ("step-rollback", "BAD_DEPLOY", 45, 43),              # 93.6% win rate
    ("step-restart", "BAD_DEPLOY", 30, 8),                # 28.1% win rate (restart won't fix bad code!)
    ("step-warm-cache", "CACHE_STAMPEDE", 38, 36),        # 92.5% win rate
    ("step-restart", "CACHE_STAMPEDE", 25, 6),            # 25.9% win rate (plain restart re-triggers stampede)
    ("step-scale-up", "THREADPOOL_EXHAUSTION", 40, 35),   # 85.7% win rate
    ("step-kill-conns", "CONNECTION_LEAK", 32, 29),       # 88.2% win rate
    ("step-trip-breaker", "CIRCUIT_BREAKER_TRIPPED", 20, 18),
]


def apply_schema_constraints(graph):
    """Create constraints and indexes on the FalkorDB graph."""
    constraints = [
        "CREATE CONSTRAINT FOR (s:Service) REQUIRE s.id IS UNIQUE",
        "CREATE CONSTRAINT FOR (t:Team) REQUIRE t.id IS UNIQUE",
        "CREATE CONSTRAINT FOR (p:Person) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT FOR (fm:FailureMode) REQUIRE fm.name IS UNIQUE",
        "CREATE CONSTRAINT FOR (st:Step) REQUIRE st.id IS UNIQUE",
        "CREATE CONSTRAINT FOR (i:Incident) REQUIRE i.id IS UNIQUE",
        "CREATE CONSTRAINT FOR (a:Alert) REQUIRE a.id IS UNIQUE",
        "CREATE CONSTRAINT FOR (d:Deploy) REQUIRE d.id IS UNIQUE",
        "CREATE CONSTRAINT FOR (tk:Task) REQUIRE tk.id IS UNIQUE",
    ]
    for c in constraints:
        try:
            graph.query(c)
        except Exception:
            pass  # Constraint already exists

    indexes = [
        "CREATE INDEX FOR (s:Service) ON (s.tier)",
        "CREATE INDEX FOR (a:Alert) ON (a.ts)",
        "CREATE INDEX FOR (d:Deploy) ON (d.ts)",
        "CREATE INDEX FOR (i:Incident) ON (i.ts)",
        "CREATE INDEX FOR (tk:Task) ON (tk.status)",
    ]
    for idx in indexes:
        try:
            graph.query(idx)
        except Exception:
            pass


def seed_graph(graph_name: str = "tenant_a") -> Dict[str, Any]:
    """Seed the full 60-microservice topology into the specified FalkorDB graph."""
    g = db_manager.get_graph(graph_name)
    
    # 1. Clean existing graph
    g.query("MATCH (n) DETACH DELETE n")
    
    # 2. Constraints & Indexes
    apply_schema_constraints(g)

    # 3. Create Services
    for s in SERVICES_SPEC:
        g.query("""
            CREATE (:Service {
                id: $id, 
                name: $name, 
                tier: $tier, 
                kind: $kind, 
                slo_ms: $slo_ms
            })
        """, s)

    # 4. Create CALLS edges
    for caller, callee, p99 in CALLS_SPEC:
        g.query("""
            MATCH (src:Service {id: $caller}), (dst:Service {id: $callee})
            CREATE (src)-[:CALLS {p99_ms: $p99, error_rate: 0.001, valid_from: 1700000000, valid_to: 0}]->(dst)
        """, {"caller": caller, "callee": callee, "p99": p99})

    # 5. Create Teams & Ownership
    for t in TEAMS_SPEC:
        g.query("""
            CREATE (:Team {
                id: $id, 
                name: $name, 
                slack_channel: $channel, 
                oncall: $oncall
            })
        """, t)

    # Assign team ownerships
    ownership_map = {
        "team-platform": ["api-gateway", "web-frontend", "mobile-bff", "public-ingress", "cdn-origin", "kafka-cluster", "rabbitmq-tasks"],
        "team-auth": ["auth-service", "session-mgr", "jwt-vault", "oauth-broker", "user-directory", "profile-service", "preference-store"],
        "team-checkout": ["cart-service", "checkout-service", "order-processor", "order-history", "invoice-service", "payment-gateway", "fraud-detector", "stripe-connector", "paypal-connector", "ledger-service", "wallet-service"],
        "team-catalog": ["catalog-service", "search-indexer", "recommendation-service", "inventory-service", "pricing-engine", "review-service"],
        "team-infra": ["postgres-primary", "postgres-replica-1", "postgres-replica-2", "redis-cluster-master", "redis-session-cache", "elasticsearch-cluster", "mongo-catalog-db", "timescale-metrics-db", "log-aggregator", "prom-metrics-collector"]
    }
    for team_id, service_ids in ownership_map.items():
        for s_id in service_ids:
            g.query("""
                MATCH (t:Team {id: $t_id}), (s:Service {id: $s_id})
                CREATE (t)-[:OWNS {since: 1680000000}]->(s)
            """, {"t_id": team_id, "s_id": s_id})

    # 6. Create People & Team Membership
    for p in PEOPLE_SPEC:
        g.query("""
            MATCH (t:Team {id: $team})
            CREATE (person:Person {id: $id, name: $name, email: $email, role: $role})
            CREATE (person)-[:MEMBER_OF {role: $role}]->(t)
        """, p)

    # 7. Create Failure Modes
    for fm in FAILURE_MODES:
        g.query("""
            CREATE (:FailureMode {
                name: $name, 
                category: $category, 
                description: $description
            })
        """, fm)

    # 8. Create Remediation Steps & Procedural Memory Weights
    for st in STEPS_SPEC:
        g.query("""
            CREATE (:Step {
                id: $id, 
                name: $name, 
                command: $command, 
                risk_level: $risk
            })
        """, st)

    for step_id, fm_name, attempts, successes in PROCEDURAL_EDGES:
        g.query("""
            MATCH (st:Step {id: $step_id}), (fm:FailureMode {name: $fm_name})
            CREATE (st)-[:EFFECTIVE_FOR {attempts: $attempts, successes: $successes}]->(fm)
        """, {"step_id": step_id, "fm_name": fm_name, "attempts": attempts, "successes": successes})

    # 9. Create Sample Historical Incidents (Episodic Memory)
    historical_incidents = [
        {
            "id": "inc-2026-084",
            "title": "Auth Hub Thread Exhaustion Cascading to Cart",
            "summary": "High traffic spike during flash sale overwhelmed auth-service connection pool",
            "ts": 1724000000,
            "root_cause": "auth-service",
            "mode": "THREADPOOL_EXHAUSTION",
            "resolver": "p-david",
            "step": "step-scale-up"
        },
        {
            "id": "inc-2026-092",
            "title": "Bad Config Rollout on Checkout Service",
            "summary": "Syntax error in payment serialization schema caused checkout drops",
            "ts": 1726000000,
            "root_cause": "checkout-service",
            "mode": "BAD_DEPLOY",
            "resolver": "p-marcus",
            "step": "step-rollback"
        },
        {
            "id": "inc-2026-101",
            "title": "Catalog Redis Cache Stampede",
            "summary": "Key eviction caused 10,000 req/sec to hit primary database simultaneously",
            "ts": 1728000000,
            "root_cause": "catalog-service",
            "mode": "CACHE_STAMPEDE",
            "resolver": "p-priya",
            "step": "step-warm-cache"
        }
    ]

    for inc in historical_incidents:
        g.query("""
            MATCH (rc:Service {id: $root_cause})
            MATCH (fm:FailureMode {name: $mode})
            MATCH (p:Person {id: $resolver})
            MATCH (st:Step {id: $step})
            CREATE (i:Incident {
                id: $id, 
                title: $title, 
                summary: $summary, 
                ts: $ts, 
                severity: 'critical'
            })
            CREATE (i)-[:ROOT_CAUSE]->(rc)
            CREATE (i)-[:MODE]->(fm)
            CREATE (p)-[:RESOLVED {ttr_min: 14}]->(i)
            CREATE (i)-[:APPLIED {outcome: 'success', ttr_min: 14}]->(st)
        """, inc)

    # 10. Compute Summary Stats
    node_count = g.query("MATCH (n) RETURN count(n)").result_set[0][0]
    edge_count = g.query("MATCH ()-[r]->() RETURN count(r)").result_set[0][0]

    return {
        "status": "success",
        "graph": graph_name,
        "nodes": node_count,
        "relationships": edge_count,
        "services": len(SERVICES_SPEC),
        "dependencies": len(CALLS_SPEC)
    }

if __name__ == "__main__":
    print("Seeding FalkorDB graph 'tenant_a'...")
    res = seed_graph("tenant_a")
    print("Seed complete:", res)
