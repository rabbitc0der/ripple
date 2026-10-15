// File: queries/02_rank_root_causes.cypher
// Track: 01 (Act on Connected Data)
// Purpose: Isolates the true root cause during a multi-alert storm using topological coverage vs collateral.
// Logic:
//   - Coverage: How many of the alerting services depend on candidate 'r'.
//   - Collateral: Total services in the graph that depend on candidate 'r'.
//   - Precision: coverage / collateral
//   - Recall: coverage / total_alerts
// Parameters:
//   $alerting_ids: List of service IDs firing alerts (e.g. ['cart-service', 'checkout-service', 'web-frontend'])
//   $total_alerts: Total number of alerts in the storm (float, e.g. 3.0)

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
LIMIT 5;
