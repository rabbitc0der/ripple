export interface ServiceNodeData {
  id: string;
  name: string;
  tier: number;
  kind: string;
  slo_ms: number;
  team: string;
  alert_count: number;
  status: 'healthy' | 'alerting' | 'root_cause' | 'blast_radius' | 'ruled_out';
}

export interface TopologyElement {
  data: any;
}

export interface Scenario {
  id: string;
  title: string;
  description: string;
  root_cause_service: string;
  failure_mode: string;
  symptom_count: number;
  noise_count: number;
}

export interface DiagnosisResult {
  status: string;
  execution_mode?: string;
  mode?: string;
  trace_id?: string;
  total_latency_ms?: number;
  incident?: {
    id: string;
    title: string;
    summary: string;
    failure_mode: string;
    alerts: Array<{
      alert_id: string;
      service_id: string;
      metric: string;
      value: number;
      is_red_herring: boolean;
    }>;
  };
  root_cause?: {
    service_id: string;
    name: string;
    tier: number;
    f1_score: number;
    recall: number;
    precision: number;
    pagerank_centrality: number;
    team: string;
    slack_channel: string;
    oncall_lead: string;
  };
  blast_radius?: {
    count: number;
    callers: Array<{
      service_id: string;
      name: string;
      tier: number;
      depth: number;
      path: string[];
    }>;
  };
  proof_by_path_absence?: {
    ruled_out_count: number;
    sample_ruled_out: Array<{
      service_id: string;
      name: string;
      tier: number;
      proof: string;
    }>;
  };
  procedural_remedy?: {
    recommended_step: {
      step_id: string;
      name: string;
      command: string;
      risk: string;
      attempts: number;
      successes: number;
      confidence: number;
    };
    all_candidates: Array<any>;
  };
  receipts?: {
    root_cause_cypher: string;
    rule_outs_cypher: string;
    blast_radius_cypher: string;
    centrality_cypher: string;
    procedural_cypher: string;
  };
  // Flat baseline response
  predicted_root_cause?: {
    id: string;
    name: string;
    reason: string;
    confidence: number;
    flaw: string;
  };
  all_candidates_by_count?: Array<{
    service_id: string;
    service_name: string;
    alert_count: number;
  }>;
  why_it_fails?: string;
}

export interface SimulationResult {
  sandbox_id: string;
  action: string;
  target_service: string;
  pre_blast_radius: number;
  post_blast_radius: number;
  delta_blast_radius: number;
  orphaned_services_created: number;
  severed_dependencies: number;
  safety_status: 'APPROVED' | 'BLOCKED_HIGH_RISK';
  safety_reason: string;
  simulation_verified_via: string;
}
