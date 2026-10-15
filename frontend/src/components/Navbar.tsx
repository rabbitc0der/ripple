import React from 'react';
import { Activity, Database, RefreshCw, Zap } from 'lucide-react';

interface NavbarProps {
  dbLatency: number | null;
  onReset: () => void;
  isResetting: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ dbLatency, onReset, isResetting }) => {
  return (
    <header className="glass-panel" style={{ margin: '16px 20px 0', padding: '12px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', zIndex: 50 }}>
      {/* Brand */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{ 
          width: '38px', 
          height: '38px', 
          borderRadius: '10px', 
          background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          boxShadow: '0 0 20px rgba(99, 102, 241, 0.5)'
        }}>
          <Activity size={20} color="#ffffff" />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '18px', fontWeight: 800, letterSpacing: '-0.02em', background: 'linear-gradient(to right, #ffffff, #94a3b8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              RIPPLE
            </span>
            <span className="badge badge-purple">FalkorDB SRE</span>
          </div>
          <p style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
            Autonomous On-Call Agent & Digital Twin
          </p>
        </div>
      </div>

      {/* Database Telemetry & Reset */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 12px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <Database size={15} color="#10b981" />
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>FalkorDB Core:</span>
          <span className="badge badge-emerald">
            {dbLatency !== null ? `${dbLatency}ms ping` : 'Connected'}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 12px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <Zap size={14} color="#6366f1" />
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Tenant:</span>
          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-main)' }}>tenant_a</span>
        </div>

        <button 
          onClick={onReset} 
          disabled={isResetting}
          className="btn btn-secondary"
          title="Clone template_golden over tenant_a via GRAPH.COPY"
        >
          <RefreshCw size={14} className={isResetting ? "animate-spin" : ""} />
          {isResetting ? "Resetting..." : "Reset Demo"}
        </button>
      </div>
    </header>
  );
};
