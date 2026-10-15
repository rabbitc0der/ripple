// File: queries/01_blast_radius.cypher
// Track: 01 (Act on Connected Data)
// Purpose: Calculates the cascading blast radius if a microservice degrades or fails.
// Logic: Traverses incoming :CALLS relationships in reverse (caller <- callee).
// Parameters:
//   $service_id: The ID of the degraded service (e.g., 'auth-service' or 'postgres-primary')

MATCH p = (root:Service {id: $service_id})<-[:CALLS*1..6]-(dependent:Service)
WITH dependent, min(length(p)) AS depth, collect([n in nodes(p) | n.id]) AS paths
RETURN dependent.id AS service_id,
       dependent.name AS name,
       dependent.tier AS tier,
       depth,
       paths[0] AS shortest_propagation_path
ORDER BY depth ASC, dependent.tier ASC;
