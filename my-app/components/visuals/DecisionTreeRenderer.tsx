"use client";

import { useMemo } from "react";
import ReactFlow, { Background, Controls, Node, Edge, MarkerType } from "reactflow";
import "reactflow/dist/style.css";
import dagre from "dagre";
import { DecisionTreeSpec } from "@/lib/visuals";

const nodeWidth = 200;
const nodeHeight = 60;

function getLayoutedElements(nodes: Node[], edges: Edge[], direction = "TB") {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ rankdir: direction, nodesep: 50, edgesep: 30, ranksep: 80 });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

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
}

const nodeTypes = {};
const edgeTypes = {};

export default function DecisionTreeRenderer({ spec }: { spec: DecisionTreeSpec }) {
  const { nodes: layoutedNodes, edges: layoutedEdges } = useMemo(() => {
    const initialNodes: Node[] = spec.nodes.map((n) => ({
      id: n.id,
      data: { label: n.label },
      position: { x: 0, y: 0 },
      type: "default",
      style: {
        background: "#0c0a09", // tailwind stone-950
        color: "#d6d3d1", // tailwind stone-300
        border: "1px solid #292524", // tailwind stone-800
        borderRadius: "8px",
        padding: "12px",
        fontSize: "12px",
        fontWeight: "500",
        width: nodeWidth,
      }
    }));
    
    const initialEdges: Edge[] = spec.edges.map((e, i) => ({
      id: `e-${e.source}-${e.target}-${i}`,
      source: e.source,
      target: e.target,
      label: e.label,
      animated: true,
      style: { stroke: "#78716c" }, // tailwind stone-500
      labelStyle: { fill: "#a8a29e", fontSize: 11, fontWeight: 600 },
      labelBgStyle: { fill: "#1c1917", color: "#fff", fillOpacity: 0.8 },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: "#78716c",
      },
    }));

    return getLayoutedElements(initialNodes, initialEdges);
  }, [spec]);

  return (
    <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-4">
      <h4 className="font-semibold text-lg">{spec.title}</h4>
      
      <div className="w-full h-[400px] bg-background/50 rounded-lg border border-border/50 overflow-hidden">
        <ReactFlow 
          nodes={layoutedNodes} 
          edges={layoutedEdges}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          proOptions={{ hideAttribution: true }}
        >
          <Background color="#292524" gap={16} />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>
    </div>
  );
}
