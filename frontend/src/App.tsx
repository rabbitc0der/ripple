import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Toolbar } from './components/Toolbar';
import { TopologyCanvas } from './components/TopologyCanvas';
import { AgentTimeline } from './components/AgentTimeline';
import { WhyDrawer } from './components/WhyDrawer';
import { SimulationModal } from './components/SimulationModal';
import { Scenario, DiagnosisResult, SimulationResult } from './types';

export const App: React.FC = () => {
  const [dbLatency, setDbLatency] = useState<number | null>(null);
  const [topology, setTopology] = useState<{ nodes: any[]; edges: any[] }>({ nodes: [], edges: [] });
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string>('hub_cascade');
  const [hasActiveIncident, setHasActiveIncident] = useState<boolean>(false);
  const [graphMode, setGraphMode] = useState<boolean>(true);

  const [diagnosis, setDiagnosis] = useState<DiagnosisResult | null>(null);
  const [simulation, setSimulation] = useState<SimulationResult | null>(null);

  const [isInjecting, setIsInjecting] = useState<boolean>(false);
  const [isDiagnosing, setIsDiagnosing] = useState<boolean>(false);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [isApproving, setIsApproving] = useState<boolean>(false);
  const [isResetting, setIsResetting] = useState<boolean>(false);

  const [isWhyOpen, setIsWhyOpen] = useState<boolean>(false);
  const [isSimModalOpen, setIsSimModalOpen] = useState<boolean>(false);

  // Load initial health, topology, and scenarios
  useEffect(() => {
    fetchHealth();
    fetchTopology();
    fetchScenarios();
  }, []);

  const fetchHealth = async () => {
    try {
      const res = await fetch('/api/health');
      const data = await res.json();
      if (data.falkordb?.latency_ms !== undefined) {
        setDbLatency(data.falkordb.latency_ms);
      }
    } catch (err) {
      console.error('Failed to fetch health', err);
    }
  };

  const fetchTopology = async () => {
    try {
      const res = await fetch('/api/topology');
      const data = await res.json();
      setTopology({ nodes: data.nodes || [], edges: data.edges || [] });
    } catch (err) {
      console.error('Failed to fetch topology', err);
    }
  };

  const fetchScenarios = async () => {
    try {
      const res = await fetch('/api/scenarios');
      const data = await res.json();
      setScenarios(data || []);
    } catch (err) {
      console.error('Failed to fetch scenarios', err);
    }
  };

  const handleInject = async () => {
    setIsInjecting(true);
    setDiagnosis(null);
    try {
      const res = await fetch('/api/fault/inject', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_id: selectedScenario })
      });
      const data = await res.json();
      if (res.ok) {
        setHasActiveIncident(true);
        await fetchTopology();
      }
    } catch (err) {
      console.error('Inject failed', err);
    } finally {
      setIsInjecting(false);
    }
  };

  const handleDiagnose = async () => {
    setIsDiagnosing(true);
    try {
      const res = await fetch('/api/diagnose', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ graph_mode: graphMode })
      });
      const data = await res.json();
      if (res.ok) {
        setDiagnosis(data);
      }
    } catch (err) {
      console.error('Diagnosis failed', err);
    } finally {
      setIsDiagnosing(false);
    }
  };

  const handleSimulate = async () => {
    if (!diagnosis?.root_cause) return;
    setIsSimulating(true);

    const targetService = diagnosis.root_cause.service_id;
    // For scenario 4, simulate risky isolation; otherwise simulate recommended action
    const action = selectedScenario === 'risky_remedy' ? 'isolate_service' : 'scale_replicas';

    try {
      const res = await fetch('/api/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action,
          target_service: targetService
        })
      });
      const data = await res.json();
      if (res.ok) {
        setSimulation(data);
        setIsSimModalOpen(true);
      }
    } catch (err) {
      console.error('Simulation failed', err);
    } finally {
      setIsSimulating(false);
    }
  };

  const handleApprove = async () => {
    if (!diagnosis?.procedural_remedy?.recommended_step) return;
    setIsApproving(true);
    try {
      const step = diagnosis.procedural_remedy.recommended_step;
      const res = await fetch('/api/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          step_id: step.step_id,
          failure_mode: diagnosis.incident?.failure_mode || 'THREADPOOL_EXHAUSTION',
          outcome: 1
        })
      });
      if (res.ok) {
        setIsSimModalOpen(false);
        setHasActiveIncident(false);
        setDiagnosis(null);
        await fetchTopology();
      }
    } catch (err) {
      console.error('Approval failed', err);
    } finally {
      setIsApproving(false);
    }
  };

  const handleReset = async () => {
    setIsResetting(true);
    try {
      const res = await fetch('/api/reset', { method: 'POST' });
      if (res.ok) {
        setDiagnosis(null);
        setHasActiveIncident(false);
        await fetchTopology();
      }
    } catch (err) {
      console.error('Reset failed', err);
    } finally {
      setIsResetting(false);
    }
  };

  // Derive active styling arrays for Cytoscape
  const rootCauseId = diagnosis?.root_cause?.service_id;
  const blastRadiusIds = diagnosis?.blast_radius?.callers?.map(c => c.service_id) || [];
  const ruledOutIds = diagnosis?.proof_by_path_absence?.sample_ruled_out?.map(r => r.service_id) || [];
  const alertingIds = topology.nodes.filter(n => n.data.alert_count > 0).map(n => n.data.id);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar 
        dbLatency={dbLatency} 
        onReset={handleReset} 
        isResetting={isResetting} 
      />

      <Toolbar
        scenarios={scenarios}
        selectedScenario={selectedScenario}
        onSelectScenario={setSelectedScenario}
        onInject={handleInject}
        onDiagnose={handleDiagnose}
        isInjecting={isInjecting}
        isDiagnosing={isDiagnosing}
        graphMode={graphMode}
        onToggleGraphMode={() => {
          setGraphMode(!graphMode);
          if (hasActiveIncident) {
            handleDiagnose();
          }
        }}
        hasActiveIncident={hasActiveIncident}
      />

      {/* Main Workspace Layout */}
      <main style={{ 
        flex: 1, 
        margin: '16px 20px 20px', 
        display: 'grid', 
        gridTemplateColumns: 'minmax(0, 1.8fr) minmax(360px, 1fr)', 
        gap: '16px' 
      }}>
        {/* Left: Interactive Graph Canvas */}
        <section className="glass-panel" style={{ padding: '4px', height: 'calc(100vh - 200px)', minHeight: '520px', position: 'relative' }}>
          <TopologyCanvas
            nodes={topology.nodes}
            edges={topology.edges}
            rootCauseId={rootCauseId}
            blastRadiusIds={blastRadiusIds}
            ruledOutIds={ruledOutIds}
            alertingIds={alertingIds}
            onSelectNode={(id) => console.log('Selected node:', id)}
          />
        </section>

        {/* Right: Agent Diagnostic Timeline */}
        <section style={{ height: 'calc(100vh - 200px)', minHeight: '520px' }}>
          <AgentTimeline
            diagnosis={diagnosis}
            graphMode={graphMode}
            onOpenWhy={() => setIsWhyOpen(true)}
            onOpenSimulate={handleSimulate}
            isSimulating={isSimulating}
          />
        </section>
      </main>

      {/* Modals & Drawers */}
      <WhyDrawer
        isOpen={isWhyOpen}
        onClose={() => setIsWhyOpen(false)}
        diagnosis={diagnosis}
      />

      <SimulationModal
        isOpen={isSimModalOpen}
        onClose={() => setIsSimModalOpen(false)}
        simulation={simulation}
        onApprove={handleApprove}
        isApproving={isApproving}
      />
    </div>
  );
};
