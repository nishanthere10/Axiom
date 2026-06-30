"use client";

import { useMemo, useState } from "react";
import ReactFlow, { Background, Controls, Node, Edge, MarkerType, NodeProps, Handle, Position } from "reactflow";
import "reactflow/dist/style.css";
import dagre from "dagre";
import { DecisionTreeSpec, DecisionNodeType } from "@/lib/visuals";
import { HelpCircle, Split, Flag, ChevronRight } from "lucide-react";

const nodeWidth = 240;
const nodeHeight = 85;

// Premium Color palette per node type
const NODE_STYLES: Record<DecisionNodeType, { bg: string; border: string; text: string; badge: string; Icon: React.FC<{ className?: string }> }> = {
  root:     { bg: "bg-blue-950/40",   border: "border-blue-500/50",   text: "text-blue-100",   badge: "bg-blue-500/20 text-blue-400 border border-blue-500/30", Icon: HelpCircle },
  decision: { bg: "bg-amber-950/40",  border: "border-amber-400/50",  text: "text-amber-100",  badge: "bg-amber-500/20 text-amber-400 border border-amber-500/30", Icon: Split },
  outcome:  { bg: "bg-emerald-950/40",border: "border-emerald-400/50",text: "text-emerald-100",badge: "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30", Icon: Flag },
  leaf:     { bg: "bg-stone-900/40",  border: "border-stone-500/50",  text: "text-stone-300",  badge: "bg-stone-500/20 text-stone-400 border border-stone-500/30", Icon: ChevronRight },
};

const NODE_TYPE_LABEL: Record<DecisionNodeType, string> = {
  root: "Question", decision: "Decision", outcome: "Outcome", leaf: "Step",
};

function DecisionNode({ data }: NodeProps) {
  const [showTooltip, setShowTooltip] = useState(false);
  const nodeType: DecisionNodeType = data.nodeType ?? "leaf";
  const s = NODE_STYLES[nodeType];
  const { Icon } = s;

  return (
    <div
      className={`relative rounded-xl border px-5 py-4 shadow-lg backdrop-blur-md ${s.bg} ${s.border} transition-all duration-300 hover:shadow-[0_0_20px_rgba(255,255,255,0.05)] hover:-translate-y-0.5 cursor-default flex flex-col justify-center`}
      style={{ width: nodeWidth, minHeight: nodeHeight }}
      onMouseEnter={() => data.description && setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <Handle type="target" position={Position.Top} className="!bg-transparent !border-0" />
      
      {/* Premium Badge */}
      <div className={`absolute -top-3 left-1/2 -translate-x-1/2 flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full shadow-sm backdrop-blur-xl ${s.badge}`}>
        <Icon className="w-3 h-3" />
        <span>{NODE_TYPE_LABEL[nodeType]}</span>
      </div>

      <p className={`text-[13px] font-medium text-center leading-relaxed mt-2 ${s.text}`}>{data.label}</p>

      {/* Tooltip */}
      {showTooltip && data.description && (
        <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-3 w-72 bg-popover/95 backdrop-blur-xl border border-border/60 rounded-xl p-3.5 shadow-2xl text-xs text-popover-foreground leading-relaxed pointer-events-none transform animate-in fade-in slide-in-from-bottom-2 duration-200">
          {data.description}
          <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-border/60" />
        </div>
      )}

      <Handle type="source" position={Position.Bottom} className="!bg-transparent !border-0" />
    </div>
  );
}

function getLayoutedElements(nodes: Node[], edges: Edge[], direction = "TB") {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ rankdir: direction, nodesep: 90, edgesep: 40, ranksep: 140 });
  nodes.forEach((node) => dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight }));
  edges.forEach((edge) => dagreGraph.setEdge(edge.source, edge.target));
  dagre.layout(dagreGraph);
  const layoutedNodes = nodes.map((node) => {
    const p = dagreGraph.node(node.id);
    return { ...node, position: { x: p.x - nodeWidth / 2, y: p.y - nodeHeight / 2 } };
  });
  return { nodes: layoutedNodes, edges };
}

const nodeTypes = { custom: DecisionNode };

export default function DecisionTreeRenderer({ spec }: { spec: DecisionTreeSpec }) {
  const { nodes: layoutedNodes, edges: layoutedEdges } = useMemo(() => {
    const initialNodes: Node[] = spec.nodes.map((n) => ({
      id: n.id,
      type: "custom",
      data: { label: n.label, nodeType: n.node_type ?? "leaf", description: n.description },
      position: { x: 0, y: 0 },
    }));

    const initialEdges: Edge[] = spec.edges.map((e, i) => ({
      id: `e-${e.source}-${e.target}-${i}`,
      source: e.source,
      target: e.target,
      label: e.label,
      animated: false,
      style: { stroke: "#64748b", strokeWidth: 1.5, opacity: 0.8 },
      labelStyle: { fill: "#cbd5e1", fontSize: 10, fontWeight: 600, letterSpacing: '0.05em' },
      labelBgStyle: { fill: "#0f172a", fillOpacity: 0.95, stroke: "#1e293b", strokeWidth: 1 },
      labelBgPadding: [8, 4] as [number, number],
      labelBgBorderRadius: 6,
      markerEnd: { type: MarkerType.ArrowClosed, color: "#64748b", width: 18, height: 18 },
    }));
    return getLayoutedElements(initialNodes, initialEdges);
  }, [spec]);

  return (
    <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-4">
      <div>
        <h4 className="font-semibold text-lg">{spec.title}</h4>
        {spec.subtitle && <p className="text-sm text-muted-foreground mt-0.5">{spec.subtitle}</p>}
      </div>
      
      {/* Legend */}
      <div className="flex flex-wrap gap-2 text-[10px] font-medium uppercase tracking-wider">
        {(["root","decision","outcome","leaf"] as DecisionNodeType[]).map(t => {
          const s = NODE_STYLES[t];
          const { Icon } = s;
          return (
            <span key={t} className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md border ${s.border} ${s.bg} ${s.text}`}>
              <Icon className="w-3.5 h-3.5 opacity-80" /> {NODE_TYPE_LABEL[t]}
            </span>
          );
        })}
        <span className="flex items-center text-muted-foreground/60 italic normal-case tracking-normal ml-auto text-xs">
          Hover nodes for details
        </span>
      </div>
      
      <div className="w-full h-[560px] bg-surface/30 rounded-xl border border-border/40 overflow-hidden shadow-inner">
        <ReactFlow
          nodes={layoutedNodes}
          edges={layoutedEdges}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.3 }}
          proOptions={{ hideAttribution: true }}
        >
          <Background color="#334155" gap={24} size={1.5} className="opacity-40" />
          <Controls showInteractive={false} className="bg-background border-border rounded-lg shadow-lg" />
        </ReactFlow>
      </div>
    </div>
  );
}
