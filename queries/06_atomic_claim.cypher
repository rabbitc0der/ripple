// File: queries/06_atomic_claim.cypher
// Track: 02 (Multi-Agent State & Coordination)
// Purpose: Atomic, race-condition-free task claim for multi-agent swarms.
// Logic:
//   FalkorDB serializes transactions per graph.
//   If two agents execute this simultaneously for the same task,
//   the first wins and returns 1 row; the second gets 0 rows back.
// Parameters:
//   $task_id: Unique ID of the Task node (e.g., 'task-triage-42')
//   $agent_id: Identifier of the worker agent attempting the claim (e.g., 'agent-worker-03')

MATCH (t:Task {id: $task_id, status: 'ready'})
SET t.status = 'claimed',
    t.claimed_by = $agent_id,
    t.claimed_at = timestamp()
RETURN t.id AS claimed_task_id,
       t.name AS task_name,
       t.claimed_by AS assigned_agent,
       t.claimed_at AS claim_timestamp;
