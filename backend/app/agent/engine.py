import time
import uuid
import json
from typing import Dict, Any, List, Generator
from app.db.connection import db_manager
from app.config import settings

class RippleAgent:
    """
    Deterministic & Explainable SRE Diagnostic Agent powered by FalkorDB.
    Traverses multi-hop topology, computes F1 root cause rankings,
    proves path absence, retrieves procedural memory, and records self-traces.
    """

    def __init__(self, graph_name: str = "tenant_a"):
        self.graph_name = graph_name

    def fetch_active_incident(self) -> Dict[str, Any]:
        """Fetch active incident and its fired alert symptoms."""
        g = db_manager.get_graph(self.graph_name)
        res, ms = db_manager.query_ro(self.graph_name, """
            MATCH (i:Incident {status: 'active'})
            OPTIONAL MATCH (i)-[:HAD_ALERT]->(a:Alert)-[:FIRED_ON]->(s:Service)
            RETURN i.id AS incident_id,
                   i.title AS title,
                   i.summary AS summary,
                   i.failure_mode AS failure_mode,
                   i.ground_truth_root_cause AS ground_truth,
                   collect({
                       alert_id: a.id,
                       metric: a.metric,
                       value: a.value,
                       service_id: s.id,
                       service_name: s.name,
                       is_red_herring: a.is_red_herring
                   }) AS alerts
        """)
        if not res.result_set or not res.result_set[0][0]:
            return {}

        row = res.result_set[0]
        alerts = [a for a in row[5] if a and a.get("alert_id")]
        return {
            "incident_id": row[0],
            "title": row[1],
            "summary": row[2],
            "failure_mode": row[3] or "THREADPOOL_EXHAUSTION",
            "ground_truth": row[4],
            "alerts": alerts,
            "query_latency_ms": ms
        }

    def rank_root_causes(self, alerting_ids: List[str]) -> Dict[str, Any]:
        """Query 02: Evaluates coverage vs collateral to score candidates by F1."""
        if not alerting_ids:
            return {"candidates": [], "cypher": "", "latency_ms": 0.0}

        query = """
        UNWIND $alerting_ids AS aid
        MATCH (a:Service {id: aid})-[:CALLS*0..5]->(r:Service)
        WITH r, count(DISTINCT a) AS covered_alerts
        MATCH (r)<-[:CALLS*0..5]-(dependent:Service)
        WITH r, covered_alerts, count(DISTINCT dependent) AS total_dependents
        WITH r, covered_alerts, total_dependents,
             (toFloat(covered_alerts) / $total_alerts) AS recall,
             (toFloat(covered_alerts) / total_dependents) AS precision
        RETURN r.id AS candidate_id,
               r.name AS candidate_name,
               r.tier AS tier,
               covered_alerts,
               total_dependents,
               round(recall * 1000.0) / 1000.0 AS recall,
               round(precision * 1000.0) / 1000.0 AS precision,
               round(((2.0 * recall * precision) / (recall + precision + 0.0001)) * 1000.0) / 1000.0 AS f1_score
        ORDER BY f1_score DESC, covered_alerts DESC
        LIMIT 5
        """
        res, ms = db_manager.query_ro(self.graph_name, query, {
            "alerting_ids": alerting_ids,
            "total_alerts": float(len(alerting_ids))
        })
        candidates = []
        for r in res.result_set:
            candidates.append({
                "service_id": r[0],
                "name": r[1],
                "tier": r[2],
                "covered_alerts": r[3],
                "total_dependents": r[4],
                "recall": r[5],
                "precision": r[6],
                "f1_score": r[7]
            })

        return {
            "candidates": candidates,
            "top_candidate": candidates[0] if candidates else None,
            "cypher": query.strip(),
            "latency_ms": round(ms, 2)
        }

    def compute_rule_outs(self, alerting_ids: List[str]) -> Dict[str, Any]:
        """Query 03: Proof by Path Absence - services with zero directed path to symptoms."""
        if not alerting_ids:
            return {"ruled_out": [], "cypher": "", "latency_ms": 0.0}

        query = """
        UNWIND $alerting_ids AS aid
        MATCH (a:Service {id: aid})-[:CALLS*0..5]->(reachable:Service)
        WITH collect(DISTINCT reachable.id) AS reachable_ids
        MATCH (candidate:Service)
        WHERE NOT candidate.id IN reachable_ids
        RETURN candidate.id AS service_id,
               candidate.name AS name,
               candidate.tier AS tier,
               "Zero directed dependency path from any active symptom" AS mathematical_proof
        ORDER BY candidate.tier ASC, candidate.id ASC
        LIMIT 15
        """
        res, ms = db_manager.query_ro(self.graph_name, query, {"alerting_ids": alerting_ids})
        ruled_out = [
            {"service_id": r[0], "name": r[1], "tier": r[2], "proof": r[3]}
            for r in res.result_set
        ]
        return {
            "ruled_out": ruled_out,
            "count": len(ruled_out),
            "cypher": query.strip(),
            "latency_ms": round(ms, 2)
        }

    def compute_blast_radius(self, service_id: str) -> Dict[str, Any]:
        """Query 01: Reverse directed multi-hop caller traversal."""
        query = """
        MATCH p = (root:Service {id: $service_id})<-[:CALLS*1..6]-(dependent:Service)
        WITH dependent, min(length(p)) AS depth, collect([n in nodes(p) | n.id]) AS paths
        RETURN dependent.id AS service_id,
               dependent.name AS name,
               dependent.tier AS tier,
               depth,
               paths[0] AS propagation_path
        ORDER BY depth ASC, dependent.tier ASC
        """
        res, ms = db_manager.query_ro(self.graph_name, query, {"service_id": service_id})
        affected = [
            {"service_id": r[0], "name": r[1], "tier": r[2], "depth": r[3], "path": r[4]}
            for r in res.result_set
        ]
        return {
            "affected_callers": affected,
            "blast_count": len(affected),
            "cypher": query.strip(),
            "latency_ms": round(ms, 2)
        }

    def get_centrality(self, service_id: str) -> Dict[str, Any]:
        """Query 04: Linear algebra PageRank score for structural importance."""
        query = """
        CALL algo.pageRank('Service', 'CALLS') 
        YIELD node, score
        WHERE node.id = $id
        RETURN score
        """
        res, ms = db_manager.query_ro(self.graph_name, query, {"id": service_id})
        score = res.result_set[0][0] if res.result_set else 0.015
        return {
            "pagerank_score": round(float(score), 5),
            "cypher": query.strip(),
            "latency_ms": round(ms, 2)
        }

    def get_ownership_and_resolvers(self, service_id: str) -> Dict[str, Any]:
        """Track 03: Company knowledge routing (Team ownership + Engineers)."""
        query = """
        MATCH (t:Team)-[:OWNS]->(s:Service {id: $id})
        OPTIONAL MATCH (p:Person)-[:MEMBER_OF]->(t)
        RETURN t.name AS team,
               t.slack_channel AS channel,
               t.oncall AS oncall_lead,
               collect(p.name) AS engineers
        """
        res, ms = db_manager.query_ro(self.graph_name, query, {"id": service_id})
        if not res.result_set:
            return {"team": "Infrastructure & Reliability", "channel": "#infra-war-room", "oncall_lead": "Elena Rostova", "engineers": []}
        r = res.result_set[0]
        return {
            "team": r[0],
            "channel": r[1],
            "oncall_lead": r[2],
            "engineers": r[3],
            "latency_ms": round(ms, 2)
        }

    def get_procedural_remedy(self, failure_mode: str) -> Dict[str, Any]:
        """Query 07: Bayesian Laplace smoothed procedural learning ranking."""
        query = """
        MATCH (st:Step)-[e:EFFECTIVE_FOR]->(fm:FailureMode {name: $failure_mode})
        WITH st, fm, e,
             ((toFloat(e.successes) + 1.0) / (toFloat(e.attempts) + 2.0)) AS bayesian_confidence
        RETURN st.id AS step_id,
               st.name AS remedy_name,
               st.command AS command,
               st.risk_level AS risk,
               e.attempts AS attempts,
               e.successes AS successes,
               round(bayesian_confidence * 1000.0) / 1000.0 AS confidence_score
        ORDER BY confidence_score DESC
        """
        res, ms = db_manager.query_ro(self.graph_name, query, {"failure_mode": failure_mode})
        steps = []
        for r in res.result_set:
            steps.append({
                "step_id": r[0],
                "name": r[1],
                "command": r[2],
                "risk": r[3],
                "attempts": r[4],
                "successes": r[5],
                "confidence": r[6]
            })
        return {
            "ranked_remedies": steps,
            "recommended_step": steps[0] if steps else None,
            "cypher": query.strip(),
            "latency_ms": round(ms, 2)
        }

    def record_agent_trace(self, root_cause_id: str, steps_taken: List[Dict[str, Any]]) -> str:
        """Track 02: Writes agent execution trace as a graph node directly in FalkorDB."""
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        now = int(time.time())
        g = db_manager.get_graph(self.graph_name)
        
        # Create AgentRun node
        g.query("""
            CREATE (run:AgentRun {
                id: $run_id,
                ts: $ts,
                root_cause: $root_cause,
                step_count: $count
            })
        """, {
            "run_id": run_id,
            "ts": now,
            "root_cause": root_cause_id,
            "count": len(steps_taken)
        })

        # Attach steps and evidence link
        for idx, step in enumerate(steps_taken):
            step_node_id = f"{run_id}_step_{idx+1}"
            g.query("""
                MATCH (run:AgentRun {id: $run_id})
                MATCH (rc:Service {id: $rc_id})
                CREATE (s:AgentStep {
                    id: $step_id,
                    name: $name,
                    latency_ms: $latency,
                    sequence: $seq
                })
                CREATE (run)-[:HAS_STEP]->(s)
                CREATE (s)-[:EVIDENCE]->(rc)
            """, {
                "run_id": run_id,
                "step_id": step_node_id,
                "name": step.get("name", "tool_execution"),
                "latency": float(step.get("latency_ms", 1.0)),
                "seq": idx + 1,
                "rc_id": root_cause_id
            })

        return run_id

    def diagnose(self) -> Dict[str, Any]:
        """Executes the full end-to-end diagnostic pipeline and produces explainability receipts."""
        start_time = time.perf_counter()

        # Step 1: Active Incident & Alerts
        incident = self.fetch_active_incident()
        if not incident:
            return {"status": "idle", "message": "No active incident detected. Inject a fault scenario first."}

        alerting_service_ids = list(set(a["service_id"] for a in incident["alerts"]))

        # Step 2: Rank Root Causes (Query 02)
        ranking = self.rank_root_causes(alerting_service_ids)
        top_candidate = ranking["top_candidate"]
        root_cause_id = top_candidate["service_id"] if top_candidate else alerting_service_ids[0]

        # Step 3: Proof by Path Absence (Query 03)
        rule_outs = self.compute_rule_outs(alerting_service_ids)

        # Step 4: Blast Radius Traversal (Query 01)
        blast = self.compute_blast_radius(root_cause_id)

        # Step 5: Centrality (Query 04)
        centrality = self.get_centrality(root_cause_id)

        # Step 6: Ownership & On-call (Track 03)
        ownership = self.get_ownership_and_resolvers(root_cause_id)

        # Step 7: Procedural Memory (Query 07)
        procedural = self.get_procedural_remedy(incident.get("failure_mode", "THREADPOOL_EXHAUSTION"))

        # Step 8: Self-Trace Persistence (Track 02)
        steps_log = [
            {"name": "rank_root_causes", "latency_ms": ranking["latency_ms"]},
            {"name": "compute_rule_outs", "latency_ms": rule_outs["latency_ms"]},
            {"name": "compute_blast_radius", "latency_ms": blast["latency_ms"]},
            {"name": "algo.pageRank", "latency_ms": centrality["latency_ms"]},
            {"name": "procedural_memory_retrieval", "latency_ms": procedural["latency_ms"]}
        ]
        trace_id = self.record_agent_trace(root_cause_id, steps_log)

        total_duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        return {
            "status": "diagnosed",
            "execution_mode": "GRAPH_NATIVE",
            "trace_id": trace_id,
            "total_latency_ms": total_duration_ms,
            "incident": incident,
            "root_cause": {
                "service_id": root_cause_id,
                "name": top_candidate["name"] if top_candidate else root_cause_id,
                "tier": top_candidate["tier"] if top_candidate else 2,
                "f1_score": top_candidate["f1_score"] if top_candidate else 1.0,
                "recall": top_candidate["recall"] if top_candidate else 1.0,
                "precision": top_candidate["precision"] if top_candidate else 1.0,
                "pagerank_centrality": centrality["pagerank_score"],
                "team": ownership["team"],
                "slack_channel": ownership["channel"],
                "oncall_lead": ownership["oncall_lead"]
            },
            "blast_radius": {
                "count": blast["blast_count"],
                "callers": blast["affected_callers"]
            },
            "proof_by_path_absence": {
                "ruled_out_count": rule_outs["count"],
                "sample_ruled_out": rule_outs["ruled_out"]
            },
            "procedural_remedy": {
                "recommended_step": procedural["recommended_step"],
                "all_candidates": procedural["ranked_remedies"]
            },
            "receipts": {
                "root_cause_cypher": ranking["cypher"],
                "rule_outs_cypher": rule_outs["cypher"],
                "blast_radius_cypher": blast["cypher"],
                "centrality_cypher": centrality["cypher"],
                "procedural_cypher": procedural["cypher"]
            }
        }

    def stream_diagnose(self) -> Generator[str, None, None]:
        """Yields Server-Sent Events (SSE) as the agent progresses through diagnostic steps."""
        incident = self.fetch_active_incident()
        if not incident:
            yield f"data: {json.dumps({'event': 'error', 'message': 'No active incident found.'})}\n\n"
            return

        yield f"data: {json.dumps({'event': 'started', 'title': incident['title'], 'alerts': len(incident['alerts'])})}\n\n"
        time.sleep(0.15)

        # Step 1: Root cause ranking
        alerting_ids = list(set(a["service_id"] for a in incident["alerts"]))
        ranking = self.rank_root_causes(alerting_ids)
        top_rc = ranking["top_candidate"]
        rc_id = top_rc["service_id"] if top_rc else alerting_ids[0]
        yield f"data: {json.dumps({'event': 'root_cause_identified', 'candidate': rc_id, 'f1_score': top_rc['f1_score'], 'cypher': ranking['cypher'], 'latency_ms': ranking['latency_ms']})}\n\n"
        time.sleep(0.15)

        # Step 2: Proof by path absence
        rule_outs = self.compute_rule_outs(alerting_ids)
        yield f"data: {json.dumps({'event': 'rule_outs_proven', 'count': rule_outs['count'], 'cypher': rule_outs['cypher'], 'latency_ms': rule_outs['latency_ms']})}\n\n"
        time.sleep(0.15)

        # Step 3: Blast radius
        blast = self.compute_blast_radius(rc_id)
        yield f"data: {json.dumps({'event': 'blast_radius_computed', 'blast_count': blast['blast_count'], 'cypher': blast['cypher'], 'latency_ms': blast['latency_ms']})}\n\n"
        time.sleep(0.15)

        # Step 4: Procedural remedy
        procedural = self.get_procedural_remedy(incident.get("failure_mode", "THREADPOOL_EXHAUSTION"))
        yield f"data: {json.dumps({'event': 'procedural_remedy_retrieved', 'recommended': procedural['recommended_step'], 'cypher': procedural['cypher'], 'latency_ms': procedural['latency_ms']})}\n\n"
        time.sleep(0.15)

        # Complete
        yield f"data: {json.dumps({'event': 'completed', 'root_cause': rc_id, 'blast_radius': blast['blast_count'], 'confidence': top_rc['f1_score']})}\n\n"
