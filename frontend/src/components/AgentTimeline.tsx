import React from 'react';
import { CheckCircle2, AlertOctagon, ArrowRight, ShieldCheck, HelpCircle, GitFork, Users, Zap } from 'lucide-react';
import { DiagnosisResult } from '../types';

interface AgentTimelineProps {
  diagnosis: DiagnosisResult | null;
  graphMode: boolean;
  onOpenWhy: () => void;
  onOpenSimulate: () => void;
  isSimulating: boolean;
}

export const AgentTimeline: React.FC<AgentTimelineProps> = ({
  diagnosis,
  graphMode,
  onOpenWhy,
  onOpenSimulate,
  isSimulating
}) => {
  if (!diagnosis) {
    return (
      <div className="glass-panel" style={{ padding: '24px', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', color: 'var(--text-muted)' }}>
        <Zap size={36} color="#6366f1" style={{ opacity: 0.6, marginBottom: '12px' }} />
        <h3 style={{ fontSize: '15px', color: 'var(--text-main)', marginBottom: '6px' }}>Diagnostic Engine Standing By</h3>
        <p style={{ fontSize: '12px', maxWidth: '280px', lineHeight: 1.6 }}>
          Select a hero scenario above and click <strong style={{ color: '#ef4444' }}>Inject Storm</strong> to begin.
        </p>
      </div>
    );
  }

  // Handle Flat Baseline Display (Graph OFF)
  if (!graphMode || diagnosis.mode === 'GRAPH_OFF_BASELINE') {
    const culprit = diagnosis.predicted_root_cause;
    return (
      <div className="glass-panel" style={{ padding: '20px', height: '100%', display: 'flex', flexDirection: 'column', gap: '16px', borderLeft: '4px solid #ef4444' }}>
        <div>
          <span className="badge badge-red" style={{ marginBottom: '8px' }}>Graph OFF Baseline</span>
          <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#f87171' }}>Naive Alert Count Blame</h3>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
            Without graph edge reachability, system relies purely on symptom volume.
          </p>
        </div>

        {culprit && (
          <div style={{ background: 'rgba(239, 68, 68, 0.08)', padding: '14px', borderRadius: '8px', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
            <div style={{ fontSize: '11px', color: '#f87171', fontWeight: 700, textTransform: 'uppercase' }}>Blamed Service:</div>
            <div style={{ fontSize: '16px', fontWeight: 800, color: 'var(--text-main)', margin: '4px 0' }}>{culprit.name}</div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{culprit.reason}</div>
            <div style={{ marginTop: '10px', fontSize: '11px', color: '#fca5a5', background: 'rgba(239, 68, 68, 0.15)', padding: '6px 10px', borderRadius: '6px' }}>
              ⚠️ <strong>Flaw:</strong> {culprit.flaw}
            </div>
          </div>
        )}

        <div style={{ background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-subtle)', fontSize: '12px', color: 'var(--text-dim)' }}>
          <p><strong>Blast Radius:</strong> Unknown (requires reverse directed traversal)</p>
          <p style={{ marginTop: '4px' }}><strong>Rule-Outs:</strong> None (requires path absence verification)</p>
        </div>
      </div>
    );
  }

  // Graph Native Diagnosis (Graph ON)
  const rc = diagnosis.root_cause;
  const blast = diagnosis.blast_radius;
  const remedy = diagnosis.procedural_remedy?.recommended_step;
  const ruleOutCount = diagnosis.proof_by_path_absence?.ruled_out_count || 0;

  return (
    <div className="glass-panel" style={{ padding: '20px', height: '100%', display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <span className="badge badge-emerald">Graph-Native Diagnosis</span>
          <h3 style={{ fontSize: '15px', fontWeight: 700, marginTop: '4px' }}>Isolated Root Cause</h3>
        </div>
        <div style={{ textAlign: 'right' }}>
          <span className="badge badge-purple">{diagnosis.total_latency_ms}ms</span>
        </div>
      </div>

      {/* Root Cause Card */}
      {rc && (
        <div style={{ background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(17, 24, 39, 0.6) 100%)', padding: '14px', borderRadius: '10px', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: '#fbbf24', textTransform: 'uppercase' }}>
              Tier {rc.tier} Critical Service
            </span>
            <span className="badge badge-amber">F1: {rc.f1_score}</span>
          </div>
          <div style={{ fontSize: '17px', fontWeight: 800, color: '#f8fafc', margin: '4px 0' }}>
            {rc.name}
          </div>
          <div style={{ display: 'flex', gap: '12px', fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
            <span>Recall: <strong>{rc.recall * 100}%</strong></span>
            <span>Precision: <strong>{rc.precision * 100}%</strong></span>
            <span>PageRank: <strong>{rc.pagerank_centrality}</strong></span>
          </div>

          {/* Track 03: Company Routing */}
          <div style={{ marginTop: '10px', paddingTop: '10px', borderTop: '1px solid rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11px', color: 'var(--text-dim)' }}>
            <Users size={13} color="#94a3b8" />
            <span>Owned by <strong style={{ color: 'var(--text-main)' }}>{rc.team}</strong> ({rc.slack_channel}) • Oncall: <strong style={{ color: 'var(--text-main)' }}>{rc.oncall_lead}</strong></span>
          </div>
        </div>
      )}

      {/* Mathematical Metrics (Blast Radius & Rule-outs) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
        <div style={{ background: 'rgba(6, 182, 212, 0.08)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(6, 182, 212, 0.2)' }}>
          <div style={{ fontSize: '10px', fontWeight: 700, color: '#22d3ee', textTransform: 'uppercase' }}>Blast Radius</div>
          <div style={{ fontSize: '20px', fontWeight: 800, color: '#f8fafc', margin: '2px 0' }}>{blast?.count || 0}</div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Callers affected</div>
        </div>

        <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: '10px', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase' }}>Rule-Outs</div>
          <div style={{ fontSize: '20px', fontWeight: 800, color: '#f8fafc', margin: '2px 0' }}>{ruleOutCount}</div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Proven innocent</div>
        </div>
      </div>

      {/* Procedural Memory & Recommended Remedy */}
      {remedy && (
        <div style={{ background: 'rgba(99, 102, 241, 0.08)', padding: '14px', borderRadius: '10px', border: '1px solid rgba(99, 102, 241, 0.25)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '10px', fontWeight: 700, color: '#818cf8', textTransform: 'uppercase' }}>Procedural Memory</span>
            <span className="badge badge-purple">{remedy.confidence * 100}% win rate</span>
          </div>
          <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-main)', marginTop: '4px' }}>
            {remedy.name}
          </div>
          <code style={{ display: 'block', fontSize: '11px', color: '#cbd5e1', background: '#090d16', padding: '6px 8px', borderRadius: '6px', marginTop: '6px', fontFamily: 'var(--font-mono)' }}>
            {remedy.command}
          </code>
          <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '6px' }}>
            Learned from {remedy.attempts} historical incident executions ({remedy.successes} successful).
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div style={{ display: 'flex', gap: '10px', marginTop: 'auto' }}>
        <button 
          onClick={onOpenSimulate} 
          disabled={isSimulating}
          className="btn btn-primary" 
          style={{ flex: 1, padding: '10px' }}
        >
          <GitFork size={15} />
          {isSimulating ? "Cloning Graph..." : "Simulate Fix (GRAPH.COPY)"}
        </button>

        <button 
          onClick={onOpenWhy} 
          className="btn btn-secondary" 
          style={{ padding: '10px' }}
          title="Inspect openCypher Receipts"
        >
          <HelpCircle size={15} />
          Receipts
        </button>
      </div>
    </div>
  );
};
