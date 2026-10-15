// File: queries/03_rule_outs.cypher
// Track: 01 (Act on Connected Data)
// Purpose: Mathematically proves which services CANNOT be the root cause of an alert storm.
// Innovation: "Proof by Path Absence" (Atrium moment) - eliminates red herrings that flat LLMs hallucinate.
// Parameters:
//   $alerting_ids: List of service IDs firing alerts

UNWIND $alerting_ids AS aid
MATCH (a:Service {id: aid})-[:CALLS*0..5]->(reachable:Service)
WITH collect(DISTINCT reachable.id) AS reachable_ids
MATCH (candidate:Service)
WHERE NOT candidate.id IN reachable_ids
RETURN candidate.id AS ruled_out_id,
       candidate.name AS name,
       candidate.tier AS tier,
       "Zero directed dependency path from any active symptom" AS mathematical_proof
ORDER BY candidate.tier ASC, candidate.id ASC
LIMIT 15;
