import React, { useState } from 'react';
import { X, Code2, ShieldAlert, Cpu, CheckCircle } from 'lucide-react';
import { DiagnosisResult } from '../types';

interface WhyDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  diagnosis: DiagnosisResult | null;
}

export const WhyDrawer: React.FC<WhyDrawerProps> = ({ isOpen, onClose, diagnosis }) => {
  const [activeTab, setActiveTab] = useState<'cypher' | 'rule_outs' | 'procedural'>('cypher');

  if (!isOpen || !diagnosis) return null;

  const receipts = diagnosis.receipts;
  const ruledOut = diagnosis.proof_by_path_absence?.sample_ruled_out || [];
  const proceduralSteps = diagnosis.procedural_remedy?.all_candidates || [];

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      right: 0,
      width: '540px',
      maxWidth: '90vw',
      height: '100vh',
      background: '#0d111a',
      borderLeft: '1px solid rgba(255, 255, 255, 0.1)',
      boxShadow: '-10px 0 30px rgba(0, 0, 0, 0.7)',
      zIndex: 100,
      display: 'flex',
      flexDirection: 'column',
      animation: 'slideIn 0.25s ease-out'
    }}>
      {/* Header */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#f8fafc' }}>
            Explainability Receipts & Graph Proof
          </h2>
          <p style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Every claim mathematically verified in FalkorDB
          </p>
        </div>
        <button onClick={onClose} className="btn btn-secondary" style={{ padding: '6px' }}>
          <X size={16} />
        </button>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border-subtle)', background: 'rgba(0,0,0,0.2)' }}>
        <button
          onClick={() => setActiveTab('cypher')}
          style={{
            flex: 1,
            padding: '10px',
            fontSize: '12px',
            fontWeight: 600,
            background: 'none',
            border: 'none',
            color: activeTab === 'cypher' ? '#818cf8' : 'var(--text-muted)',
            borderBottom: activeTab === 'cypher' ? '2px solid #6366f1' : 'none',
            cursor: 'pointer'
          }}
        >
          openCypher Queries
        </button>
        <button
          onClick={() => setActiveTab('rule_outs')}
          style={{
            flex: 1,
            padding: '10px',
            fontSize: '12px',
            fontWeight: 600,
            background: 'none',
            border: 'none',
            color: activeTab === 'rule_outs' ? '#22d3ee' : 'var(--text-muted)',
            borderBottom: activeTab === 'rule_outs' ? '2px solid #06b6d4' : 'none',
            cursor: 'pointer'
          }}
        >
          Rule-Outs ({diagnosis.proof_by_path_absence?.ruled_out_count || 0})
        </button>
        <button
          onClick={() => setActiveTab('procedural')}
          style={{
            flex: 1,
            padding: '10px',
            fontSize: '12px',
            fontWeight: 600,
            background: 'none',
            border: 'none',
            color: activeTab === 'procedural' ? '#34d399' : 'var(--text-muted)',
            borderBottom: activeTab === 'procedural' ? '2px solid #10b981' : 'none',
            cursor: 'pointer'
          }}
        >
          Procedural Bayesian
        </button>
      </div>

      {/* Body Content */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {activeTab === 'cypher' && (
          <div>
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '11px', fontWeight: 700, color: '#fbbf24', textTransform: 'uppercase', marginBottom: '6px' }}>
                1. Root-Cause Ranking (Coverage vs Collateral F1)
              </div>
              <pre style={{ background: '#070a10', padding: '12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)', fontSize: '11px', color: '#93c5fd', fontFamily: 'var(--font-mono)', overflowX: 'auto' }}>
                {receipts?.root_cause_cypher}
              </pre>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '11px', fontWeight: 700, color: '#22d3ee', textTransform: 'uppercase', marginBottom: '6px' }}>
                2. Reverse Directed Blast Radius
              </div>
              <pre style={{ background: '#070a10', padding: '12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)', fontSize: '11px', color: '#67e8f9', fontFamily: 'var(--font-mono)', overflowX: 'auto' }}>
                {receipts?.blast_radius_cypher}
              </pre>
            </div>

            <div>
              <div style={{ fontSize: '11px', fontWeight: 700, color: '#34d399', textTransform: 'uppercase', marginBottom: '6px' }}>
                3. Linear Algebra PageRank Hub Criticality
              </div>
              <pre style={{ background: '#070a10', padding: '12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)', fontSize: '11px', color: '#6ee7b7', fontFamily: 'var(--font-mono)', overflowX: 'auto' }}>
                {receipts?.centrality_cypher}
              </pre>
            </div>
          </div>
        )}

        {activeTab === 'rule_outs' && (
          <div>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '12px', lineHeight: 1.6 }}>
              <strong>Proof by Path Absence:</strong> A flat LLM or vector system hallucinates correlations. Ripple verifies that <strong>zero directed dependency paths</strong> connect these services to any active alert symptom.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {ruledOut.map((ro, i) => (
                <div key={i} style={{ background: 'rgba(255,255,255,0.02)', padding: '10px 14px', borderRadius: '8px', border: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ fontSize: '13px', fontWeight: 600, color: '#cbd5e1' }}>{ro.name}</div>
                    <div style={{ fontSize: '11px', color: '#64748b' }}>Tier {ro.tier} • {ro.proof}</div>
                  </div>
                  <span className="badge" style={{ background: 'rgba(255,255,255,0.05)', color: '#94a3b8' }}>Ruled Out</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'procedural' && (
          <div>
            <div style={{ background: 'rgba(16, 185, 129, 0.08)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.25)', marginBottom: '14px', fontSize: '12px', color: '#a7f3d0' }}>
              <strong>Bayesian Laplace Smoothing Formula:</strong>
              <div style={{ fontFamily: 'var(--font-mono)', marginTop: '4px', color: '#ffffff' }}>
                P(Success) = (successes + 1.0) / (attempts + 2.0)
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {proceduralSteps.map((step, idx) => (
                <div key={idx} style={{ background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontSize: '13px', fontWeight: 700, color: '#f8fafc' }}>{step.name}</span>
                    <span className="badge badge-emerald">{step.confidence * 100}% Win Rate</span>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '4px' }}>
                    Past attempts: <strong>{step.attempts}</strong> • Past successes: <strong>{step.successes}</strong>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
