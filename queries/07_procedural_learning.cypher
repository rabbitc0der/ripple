// File: queries/07_procedural_learning.cypher
// Track: 02 (Agent Memory - Procedural Memory on Edges)
// Purpose: Retrieves best remedy by failure mode using Bayesian Laplace smoothing,
//          and writes back execution outcomes to climb the learning curve.

// --- 1. Retrieval: Rank candidate remediation steps by learned success rate ---
// Parameters:
//   $failure_mode: e.g., 'BAD_DEPLOY' or 'CACHE_STAMPEDE'
MATCH (st:Step)-[e:EFFECTIVE_FOR]->(fm:FailureMode {name: $failure_mode})
WITH st, fm, e,
     ((toFloat(e.successes) + 1.0) / (toFloat(e.attempts) + 2.0)) AS bayesian_confidence
RETURN st.id AS step_id,
       st.name AS remedy_name,
       st.command AS execution_command,
       st.risk_level AS risk,
       e.attempts AS past_attempts,
       e.successes AS past_successes,
       round(bayesian_confidence * 1000.0) / 1000.0 AS confidence_score
ORDER BY confidence_score DESC;

// --- 2. Feedback Write-Back: Update edge weights after human-approved action ---
// Parameters:
//   $step_id: ID of the applied step (e.g., 'step-rollback')
//   $failure_mode: Failure mode name (e.g., 'BAD_DEPLOY')
//   $outcome_success: 1 if incident was resolved, 0 if it failed
MATCH (st:Step {id: $step_id})-[e:EFFECTIVE_FOR]->(fm:FailureMode {name: $failure_mode})
SET e.attempts = e.attempts + 1,
    e.successes = e.successes + $outcome_success,
    e.last_updated = timestamp()
RETURN st.name AS remedy,
       fm.name AS failure_mode,
       e.attempts AS total_attempts,
       e.successes AS total_successes,
       round(((toFloat(e.successes) + 1.0) / (toFloat(e.attempts) + 2.0)) * 1000.0) / 1000.0 AS new_confidence;
