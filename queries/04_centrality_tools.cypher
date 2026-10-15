// File: queries/04_centrality_tools.cypher
// Track: 01 (Act on Connected Data - Algorithms as Tools)
// Purpose: Graph algorithms as agent tools to compute structural hub criticality and bridge bottlenecks.

// 1. PageRank on Directed Service Call Graph
CALL algo.pageRank('Service', 'CALLS') 
YIELD node, score
RETURN node.id AS service_id,
       node.name AS name,
       node.tier AS tier,
       round(score * 100000.0) / 100000.0 AS centrality_score
ORDER BY centrality_score DESC
LIMIT 10;

// 2. Betweenness Centrality (identifies communication bridges and transit chokepoints)
CALL algo.betweenness({nodeLabels: ['Service'], relationshipTypes: ['CALLS'], samplingSeed: 42})
YIELD node, score
RETURN node.id AS service_id,
       node.name AS name,
       round(score * 100000.0) / 100000.0 AS bridge_score
ORDER BY bridge_score DESC
LIMIT 10;
