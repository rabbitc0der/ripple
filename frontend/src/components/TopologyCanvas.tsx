import React, { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';

interface TopologyCanvasProps {
  nodes: any[];
  edges: any[];
  rootCauseId?: string;
  blastRadiusIds: string[];
  ruledOutIds: string[];
  alertingIds: string[];
  onSelectNode: (nodeId: string) => void;
}

export const TopologyCanvas: React.FC<TopologyCanvasProps> = ({
  nodes,
  edges,
  rootCauseId,
  blastRadiusIds,
  ruledOutIds,
  alertingIds,
  onSelectNode
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

  useEffect(() => {
    if (!containerRef.current || nodes.length === 0) return;

    // Build Cytoscape elements with dynamic styling classes
    const elements: cytoscape.ElementDefinition[] = [
      ...nodes.map(n => {
        const id = n.data.id;
        let statusClass = 'healthy';
        if (id === rootCauseId) {
          statusClass = 'root-cause';
        } else if (blastRadiusIds.includes(id)) {
          statusClass = 'blast-radius';
        } else if (alertingIds.includes(id)) {
          statusClass = 'alerting';
        } else if (ruledOutIds.includes(id)) {
          statusClass = 'ruled-out';
        }

        return {
          group: 'nodes' as const,
          data: {
            ...n.data,
            label: n.data.name || id
          },
          classes: `${statusClass} tier-${n.data.tier || 2}`
        };
      }),
      ...edges.map(e => {
        const isBlastEdge = 
          (rootCauseId && (e.data.target === rootCauseId || blastRadiusIds.includes(e.data.target))) ||
          (blastRadiusIds.includes(e.data.source) && blastRadiusIds.includes(e.data.target));

        return {
          group: 'edges' as const,
          data: {
            ...e.data
          },
          classes: isBlastEdge ? 'blast-edge' : 'normal-edge'
        };
      })
    ];

    if (!cyRef.current) {
      cyRef.current = cytoscape({
        container: containerRef.current,
        elements,
        boxSelectionEnabled: false,
        autounselectify: false,
        style: [
          {
            selector: 'node',
            style: {
              'label': 'data(label)',
              'color': '#f8fafc',
              'font-family': 'Plus Jakarta Sans, sans-serif',
              'font-size': '10px',
              'font-weight': 600,
              'text-valign': 'bottom',
              'text-margin-y': 6,
              'background-color': '#1e293b',
              'border-width': 2,
              'border-color': '#475569',
              'width': 32,
              'height': 32,
              'transition-property': 'background-color, border-color, width, height, opacity',
              'transition-duration': 300
            }
          },
          {
            selector: 'node.tier-1',
            style: {
              'border-color': '#6366f1',
              'border-width': 2.5
            }
          },
          {
            selector: 'node.tier-3',
            style: {
              'border-color': '#10b981',
              'shape': 'round-rectangle'
            }
          },
          {
            selector: 'node.alerting',
            style: {
              'background-color': '#ef4444',
              'border-color': '#f87171',
              'border-width': 3,
              'width': 38,
              'height': 38
            }
          },
          {
            selector: 'node.blast-radius',
            style: {
              'background-color': '#06b6d4',
              'border-color': '#22d3ee',
              'border-width': 3,
              'width': 36,
              'height': 36
            }
          },
          {
            selector: 'node.root-cause',
            style: {
              'background-color': '#f59e0b',
              'border-color': '#ffffff',
              'border-width': 4,
              'width': 50,
              'height': 50,
              'font-size': '12px',
              'font-weight': 800,
              'z-index': 999
            }
          },
          {
            selector: 'node.ruled-out',
            style: {
              'opacity': 0.22,
              'border-color': '#334155'
            }
          },
          {
            selector: 'edge',
            style: {
              'width': 1.5,
              'line-color': '#334155',
              'target-arrow-color': '#475569',
              'target-arrow-shape': 'triangle',
              'curve-style': 'bezier',
              'arrow-scale': 0.8,
              'opacity': 0.6
            }
          },
          {
            selector: 'edge.blast-edge',
            style: {
              'width': 3,
              'line-color': '#06b6d4',
              'target-arrow-color': '#06b6d4',
              'opacity': 0.95,
              'z-index': 99
            }
          }
        ],
        layout: {
          name: 'concentric',
          concentric: (node: any) => {
            const tier = node.data('tier') || 2;
            return 4 - tier; // Tier 1 on outside, Tier 3 core in center
          },
          levelWidth: () => 1,
          padding: 30,
          animate: true,
          animationDuration: 500
        }
      });

      cyRef.current.on('tap', 'node', (evt) => {
        const node = evt.target;
        onSelectNode(node.id());
      });
    } else {
      // Smoothly update elements in-place
      cyRef.current.elements().remove();
      cyRef.current.add(elements);
      cyRef.current.layout({
        name: 'concentric',
        concentric: (node: any) => 4 - (node.data('tier') || 2),
        levelWidth: () => 1,
        padding: 30,
        animate: false
      }).run();
    }
  }, [nodes, edges, rootCauseId, blastRadiusIds, ruledOutIds, alertingIds]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', minHeight: '520px', borderRadius: '12px', overflow: 'hidden' }}>
      <div ref={containerRef} style={{ width: '100%', height: '100%', position: 'absolute', top: 0, left: 0 }} />

      {/* Floating Canvas Legend */}
      <div 
        className="glass-panel" 
        style={{ 
          position: 'absolute', 
          bottom: '16px', 
          left: '16px', 
          padding: '10px 14px', 
          display: 'flex', 
          gap: '12px', 
          alignItems: 'center',
          fontSize: '11px',
          fontWeight: 600,
          pointerEvents: 'none'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#ef4444', display: 'inline-block' }} />
          <span>Alerting</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#f59e0b', display: 'inline-block' }} />
          <span>Root Cause</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#06b6d4', display: 'inline-block' }} />
          <span>Blast Radius</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#334155', opacity: 0.5, display: 'inline-block' }} />
          <span>Ruled Out</span>
        </div>
      </div>
    </div>
  );
};
