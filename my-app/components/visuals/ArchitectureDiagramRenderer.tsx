import React, { useMemo } from 'react';
import { ReactFlow, Background, Controls, MarkerType, Handle, Position } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from 'dagre';

// 1. Premium Custom Node Design
const CustomNode = ({ data }: any) => (
  <div className="px-4 py-2 shadow-sm rounded-md bg-background border border-border text-sm font-medium text-foreground min-w-[150px] text-center">
    <Handle type="target" position={Position.Top} className="w-2 h-2" />
    {data.label}
    <Handle type="source" position={Position.Bottom} className="w-2 h-2" />
  </div>
);

// 2. Dagre Auto-Layout Engine
const getLayoutedElements = (nodes: any[], edges: any[], direction = 'TB') => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  
  const nodeWidth = 180;
  const nodeHeight = 50;

  dagreGraph.setGraph({ rankdir: direction, nodesep: 50, ranksep: 80 });

  // Add nodes to dagre
  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

  // Add edges to dagre
  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - nodeWidth / 2,
        y: nodeWithPosition.y - nodeHeight / 2,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
};

// Move nodeTypes outside the component for stable memory reference
const nodeTypes = { custom: CustomNode };

// 3. Main Renderer Component
export default function ArchitectureDiagramRenderer({ spec }: { spec: any }) {

  // Map backend JSON to React Flow format
  const initialNodes = (spec.nodes || []).map((n: any) => ({
    id: n.id,
    type: 'custom',
    data: { label: n.label },
    // We intentionally omit `parentNode` here because React Flow expects 
    // relative coordinates for children, which conflicts with Dagre's absolute coordinate layout.
    // Keeping them flat ensures the layout engine always produces a stable graph.
  }));

  const initialEdges = (spec.edges || []).map((e: any, idx: number) => ({
    id: `e-${e.source}-${e.target}-${idx}`,
    source: e.source,
    target: e.target,
    label: e.label,
    animated: e.animated,
    markerEnd: { type: MarkerType.ArrowClosed, width: 20, height: 20, color: '#64748b' },
    style: { stroke: '#64748b', strokeWidth: 1.5 },
    labelBgPadding: [8, 4],
    labelBgBorderRadius: 4,
    labelStyle: { fontWeight: 500 },
  }));

  // Apply auto-layout
  const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
    initialNodes,
    initialEdges
  );

  return (
    <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-4">
      <h4 className="font-semibold text-lg">{spec.title}</h4>
      <div className="w-full h-[600px] border border-border/50 rounded-lg bg-muted/20 overflow-hidden">
        <ReactFlow
          nodes={layoutedNodes}
          edges={layoutedEdges}
          nodeTypes={nodeTypes}
          fitView
          attributionPosition="bottom-right"
        >
          <Background gap={16} color="currentColor" className="text-muted-foreground/20" />
          <Controls className="bg-background border-border text-foreground" />
        </ReactFlow>
      </div>
    </div>
  );
}
