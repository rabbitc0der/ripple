import React from 'react';
import { X, ShieldAlert, ShieldCheck, Check, ArrowRight, GitFork } from 'lucide-react';
import { SimulationResult } from '../types';

interface SimulationModalProps {
  isOpen: boolean;
  onClose: () => void;
  simulation: SimulationResult | null;
  onApprove: () => void;
  isApproving: boolean;
}

export const SimulationModal: React.FC<SimulationModalProps> = ({
  isOpen,
  onClose,
  simulation,
  onApprove,
  isApproving
}) => {
  if (!isOpen || !simulation) return null;

  const isApproved = simulation.safety_status === 'APPROVED';

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
      background: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 110,
      padding: '20px'
    }}>
      <div className="glass-panel" style={{
        width: '560px',
        maxWidth: '100%',
        background: '#0d121c',
        border: '1px solid rgba(255, 255, 255, 0.12)',
        borderRadius: '16px',
        boxShadow: '0 20px 50px rgba(0, 0, 0, 0.8)',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Header */}
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <GitFork size={20} color="#6366f1" />
            <div>
              <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#f8fafc' }}>
                Counterfactual Simulation Diff
              </h2>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                Evaluated in Ephemeral Sandbox: <strong>{simulation.sandbox_id}</strong>
              </span>
            </div>
          </div>
          <button onClick={onClose} className="btn btn-secondary" style={{ padding: '6px' }}>
            <X size={16} />
          </button>
        </div>

        {/* Content */}
        <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Target & Action */}
          <div style={{ background: 'rgba(255,255,255,0.03)', padding: '14px', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 700 }}>
              Proposed Remediation Action
            </div>
            <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-main)', marginTop: '2px' }}>
              Action: <span style={{ color: '#818cf8' }}>{simulation.action}</span> on <span style={{ color: '#fbbf24' }}>{simulation.target_service}</span>
            </div>
          </div>

          {/* Before vs After Metric Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            {/* Pre */}
            <div style={{ background: 'rgba(239, 68, 68, 0.06)', padding: '16px', borderRadius: '10px', border: '1px solid rgba(239, 68, 68, 0.2)', textAlign: 'center' }}>
              <div style={{ fontSize: '11px', color: '#f87171', fontWeight: 700, textTransform: 'uppercase' }}>
                Pre-Simulation Blast
              </div>
              <div style={{ fontSize: '28px', fontWeight: 800, color: '#f8fafc', margin: '4px 0' }}>
                {simulation.pre_blast_radius}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Affected callers</div>
            </div>

            {/* Post */}
            <div style={{ background: isApproved ? 'rgba(16, 185, 129, 0.06)' : 'rgba(239, 68, 68, 0.1)', padding: '16px', borderRadius: '10px', border: `1px solid ${isApproved ? 'rgba(16, 185, 129, 0.25)' : 'rgba(239, 68, 68, 0.4)'}`, textAlign: 'center' }}>
              <div style={{ fontSize: '11px', color: isApproved ? '#34d399' : '#f87171', fontWeight: 700, textTransform: 'uppercase' }}>
                Post-Simulation Blast
              </div>
              <div style={{ fontSize: '28px', fontWeight: 800, color: '#f8fafc', margin: '4px 0' }}>
                {simulation.post_blast_radius}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                Delta: {simulation.delta_blast_radius >= 0 ? `+${simulation.delta_blast_radius}` : simulation.delta_blast_radius}
              </div>
            </div>
          </div>

          {/* Safety Status Banner */}
          <div style={{
            background: isApproved ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.12)',
            border: `1px solid ${isApproved ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.4)'}`,
            padding: '16px',
            borderRadius: '10px',
            display: 'flex',
            gap: '12px',
            alignItems: 'flex-start'
          }}>
            {isApproved ? (
              <ShieldCheck size={22} color="#10b981" style={{ flexShrink: 0, marginTop: '2px' }} />
            ) : (
              <ShieldAlert size={22} color="#ef4444" style={{ flexShrink: 0, marginTop: '2px' }} />
            )}
            <div>
              <div style={{ fontSize: '13px', fontWeight: 700, color: isApproved ? '#34d399' : '#f87171' }}>
                Policy Guardrail: {simulation.safety_status}
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px', lineHeight: 1.5 }}>
                {simulation.safety_reason}
              </div>
              {simulation.orphaned_services_created > 0 && (
                <div style={{ fontSize: '11px', color: '#fca5a5', marginTop: '6px' }}>
                  ⚠️ Critical side effect: <strong>{simulation.orphaned_services_created}</strong> services would be completely disconnected.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div style={{ padding: '16px 24px', borderTop: '1px solid var(--border-subtle)', background: 'rgba(0,0,0,0.2)', display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          <button onClick={onClose} className="btn btn-secondary">
            Cancel
          </button>
          {isApproved ? (
            <button
              onClick={onApprove}
              disabled={isApproving}
              className="btn btn-primary"
            >
              <Check size={16} />
              {isApproving ? "Executing & Learning..." : "Approve & Execute Fix"}
            </button>
          ) : (
            <button disabled className="btn btn-danger" style={{ opacity: 0.6 }}>
              Action Blocked by Safety Policy
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
