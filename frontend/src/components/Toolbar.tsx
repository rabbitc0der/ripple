import React from 'react';
import { AlertTriangle, Play, Cpu, ShieldAlert, ToggleLeft, ToggleRight, Sparkles } from 'lucide-react';
import { Scenario } from '../types';

interface ToolbarProps {
  scenarios: Scenario[];
  selectedScenario: string;
  onSelectScenario: (id: string) => void;
  onInject: () => void;
  onDiagnose: () => void;
  isInjecting: boolean;
  isDiagnosing: boolean;
  graphMode: boolean;
  onToggleGraphMode: () => void;
  hasActiveIncident: boolean;
}

export const Toolbar: React.FC<ToolbarProps> = ({
  scenarios,
  selectedScenario,
  onSelectScenario,
  onInject,
  onDiagnose,
  isInjecting,
  isDiagnosing,
  graphMode,
  onToggleGraphMode,
  hasActiveIncident
}) => {
  return (
    <div className="glass-panel" style={{ margin: '12px 20px 0', padding: '14px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
      {/* Scenario Selector */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
        <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Hero Scenarios:
        </span>
        <div style={{ display: 'flex', gap: '6px' }}>
          {scenarios.map((s, idx) => {
            const isSelected = s.id === selectedScenario;
            return (
              <button
                key={s.id}
                onClick={() => onSelectScenario(s.id)}
                className={`btn ${isSelected ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '6px 12px', fontSize: '12px' }}
              >
                <span>{idx + 1}. {s.title.split('(')[0]}</span>
                {s.noise_count > 0 && (
                  <span className="badge badge-amber" style={{ padding: '1px 5px', fontSize: '10px' }}>
                    Noise
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Action Controls & Graph Toggle */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        {/* Graph ON / OFF Toggle */}
        <div 
          onClick={onToggleGraphMode}
          style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px', 
            padding: '6px 12px', 
            background: graphMode ? 'rgba(99, 102, 241, 0.12)' : 'rgba(239, 68, 68, 0.12)', 
            border: `1px solid ${graphMode ? 'rgba(99, 102, 241, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
            borderRadius: '8px',
            cursor: 'pointer',
            transition: 'all 0.2s'
          }}
          title="Compare FalkorDB Graph Engine vs Naive Alert Count Baseline"
        >
          {graphMode ? <ToggleRight size={20} color="#818cf8" /> : <ToggleLeft size={20} color="#f87171" />}
          <span style={{ fontSize: '12px', fontWeight: 700, color: graphMode ? '#818cf8' : '#f87171' }}>
            {graphMode ? "Graph Engine: ON" : "Graph Engine: OFF (Baseline)"}
          </span>
        </div>

        {/* Inject Button */}
        <button
          onClick={onInject}
          disabled={isInjecting}
          className="btn btn-danger"
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <AlertTriangle size={15} />
          {isInjecting ? "Injecting..." : "1. Inject Storm"}
        </button>

        {/* Diagnose Button */}
        <button
          onClick={onDiagnose}
          disabled={isDiagnosing}
          className="btn btn-primary"
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <Sparkles size={15} />
          {isDiagnosing ? "Diagnosing..." : "2. Run Diagnosis"}
        </button>
      </div>
    </div>
  );
};
