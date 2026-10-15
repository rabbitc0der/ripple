// File: queries/05_jaccard_similarity.cypher
// Track: 02 (Agent Memory - Episodic Memory Retrieval)
// Purpose: Finds structurally similar historical incidents using topological Jaccard similarity in pure Cypher.
// Parameters:
//   $current_incident_id: ID of the active incident being diagnosed

MATCH (curr:Incident {id: $current_incident_id})-[:HAD_ALERT]->(:Alert)-[:FIRED_ON]->(s:Service)
WITH curr, collect(DISTINCT s.id) AS current_services
MATCH (past:Incident)-[:HAD_ALERT]->(:Alert)-[:FIRED_ON]->(t:Service)
WHERE past <> curr
WITH curr, current_services, past, collect(DISTINCT t.id) AS past_services
WITH past, current_services, past_services,
     [x IN current_services WHERE x IN past_services] AS intersection
WITH past,
     size(intersection) AS inter_size,
     (size(current_services) + size(past_services) - size(intersection)) AS union_size
WHERE union_size > 0
MATCH (past)-[:ROOT_CAUSE]->(rc:Service)
MATCH (past)-[:MODE]->(fm:FailureMode)
MATCH (past)-[:APPLIED]->(st:Step)
RETURN past.id AS incident_id,
       past.title AS title,
       past.summary AS summary,
       rc.id AS historical_root_cause,
       fm.name AS failure_mode,
       st.name AS successful_step,
       round((toFloat(inter_size) / union_size) * 1000.0) / 1000.0 AS jaccard_similarity
ORDER BY jaccard_similarity DESC
LIMIT 3;
