import React, { useState } from 'react';
import { ReactFlow, Background, Controls, MarkerType, Handle, Position, NodeProps } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from 'dagre';
import { ArchNodeType } from '@/lib/visuals';
import { ServerCog, Database, Mail, User, Route, Zap, Box } from "lucide-react";

// Color map and Lucide icons per architecture node type
const ARCH_STYLES: Record<ArchNodeType, { bg: string; border: string; text: string; iconBg: string; iconColor: string; Icon: React.FC<{ className?: string }> }> = {
  service:   { bg: "bg-violet-950/40", border: "border-violet-500/50", text: "text-violet-100", iconBg: "bg-violet-500/20", iconColor: "text-violet-400", Icon: ServerCog },
  database:  { bg: "bg-cyan-950/40",   border: "border-cyan-500/50",   text: "text-cyan-100",   iconBg: "bg-cyan-500/20",   iconColor: "text-cyan-400",   Icon: Database },
  queue:     { bg: "bg-amber-950/40",  border: "border-amber-400/50",  text: "text-amber-100",  iconBg: "bg-amber-500/20",  iconColor: "text-amber-400",  Icon: Mail },
  client:    { bg: "bg-pink-950/40",   border: "border-pink-400/50",   text: "text-pink-100",   iconBg: "bg-pink-500/20",   iconColor: "text-pink-400",   Icon: User },
  gateway:   { bg: "bg-orange-950/40", border: "border-orange-400/50", text: "text-orange-100", iconBg: "bg-orange-500/20", iconColor: "text-orange-400", Icon: Route },
  cache:     { bg: "bg-teal-950/40",   border: "border-teal-400/50",   text: "text-teal-100",   iconBg: "bg-teal-500/20",   iconColor: "text-teal-400",   Icon: Zap },
  component: { bg: "bg-slate-900/40",  border: "border-slate-500/50",  text: "text-slate-200",  iconBg: "bg-slate-500/20",  iconColor: "text-slate-400",  Icon: Box },
};

const ARCH_TYPE_LABEL: Record<ArchNodeType, string> = {
  service: "Service", database: "Database", queue: "Queue",
  client: "Client", gateway: "Gateway", cache: "Cache", component: "Component",
};

function ArchNode({ data }: NodeProps) {
  const [showTooltip, setShowTooltip] = useState(false);
  const nodeType: ArchNodeType = data.nodeType ?? "component";
  const s = ARCH_STYLES[nodeType];
  const { Icon } = s;

  return (
    <div
      className={`relative rounded-xl border px-4 py-3 shadow-lg backdrop-blur-md min-w-[170px] max-w-[220px] ${s.bg} ${s.border} transition-all duration-300 hover:shadow-[0_0_20px_rgba(255,255,255,0.05)] hover:-translate-y-0.5 cursor-default group`}
      onMouseEnter={() => data.description && setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <Handle type="target" position={Position.Top} className="!bg-transparent !border-0 !w-0 !h-0" />
      <Handle type="target" position={Position.Left} className="!bg-transparent !border-0 !w-0 !h-0" />

      <div className="flex flex-col items-center gap-2 text-center">
        {/* Icon container */}
        <div className={`p-2 rounded-lg ${s.iconBg} ring-1 ring-white/5 group-hover:ring-white/10 transition-all duration-300`}>
          <Icon className={`w-5 h-5 ${s.iconColor}`} />
        </div>
        
        {/* Text */}
        <div className="space-y-0.5">
          <p className={`text-sm font-bold leading-snug tracking-wide ${s.text}`}>{data.label}</p>
          <span className={`block text-[9px] uppercase tracking-widest font-bold opacity-70 ${s.iconColor}`}>
            {ARCH_TYPE_LABEL[nodeType]}
          </span>
        </div>
      </div>

      {showTooltip && data.description && (
        <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-3 w-72 bg-popover/95 backdrop-blur-xl border border-border/60 rounded-xl p-3.5 shadow-2xl text-xs text-popover-foreground leading-relaxed pointer-events-none transform animate-in fade-in slide-in-from-bottom-2 duration-200">
          {data.description}
          <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-border/60" />
        </div>
      )}

      <Handle type="source" position={Position.Bottom} className="!bg-transparent !border-0 !w-0 !h-0" />
      <Handle type="source" position={Position.Right} className="!bg-transparent !border-0 !w-0 !h-0" />
    </div>
  );
}

const getLayoutedElements = (nodes: any[], edges: any[], direction = 'TB') => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  const nodeWidth = 220;
  const nodeHeight = 110;
  dagreGraph.setGraph({ rankdir: direction, nodesep: 70, ranksep: 110 });
  nodes.forEach((node) => dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight }));
  edges.forEach((edge) => dagreGraph.setEdge(edge.source, edge.target));
  dagre.layout(dagreGraph);
  const layoutedNodes = nodes.map((node) => {
    const p = dagreGraph.node(node.id);
    return { ...node, position: { x: p.x - nodeWidth / 2, y: p.y - nodeHeight / 2 } };
  });
  return { nodes: layoutedNodes, edges };
};

const nodeTypes = { custom: ArchNode };

export default function ArchitectureDiagramRenderer({ spec }: { spec: any }) {
  const initialNodes = (spec.nodes || []).map((n: any) => ({
    id: n.id,
    type: 'custom',
    data: { label: n.label, nodeType: n.node_type ?? 'component', description: n.description },
  }));

  const initialEdges = (spec.edges || []).map((e: any, idx: number) => ({
    id: `e-${e.source}-${e.target}-${idx}`,
    source: e.source,
    target: e.target,
    label: e.label,
    animated: e.animated ?? false,
    markerEnd: { type: MarkerType.ArrowClosed, width: 20, height: 20, color: e.animated ? '#38bdf8' : '#475569' },
    style: { stroke: e.animated ? '#38bdf8' : '#475569', strokeWidth: e.animated ? 2 : 1.5, opacity: 0.8 },
    labelBgPadding: [8, 4] as [number, number],
    labelBgBorderRadius: 6,
    labelBgStyle: { fill: '#0f172a', fillOpacity: 0.95, stroke: '#1e293b', strokeWidth: 1 },
    labelStyle: { fontWeight: 600, fontSize: 10, fill: '#cbd5e1', letterSpacing: '0.05em' },
  }));

  const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(initialNodes, initialEdges);

  // Build legend from unique node types present
  const presentTypes = [...new Set((spec.nodes || []).map((n: any) => n.node_type ?? 'component'))] as ArchNodeType[];

  return (
    <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-4">
      <div>
        <h4 className="font-semibold text-lg">{spec.title}</h4>
        {spec.subtitle && <p className="text-sm text-muted-foreground mt-0.5">{spec.subtitle}</p>}
      </div>
      
      {/* Dynamic legend */}
      <div className="flex flex-wrap gap-2 text-[10px] font-medium uppercase tracking-wider">
        {presentTypes.map(t => {
          const s = ARCH_STYLES[t];
          const { Icon } = s;
          return (
            <span key={t} className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md border ${s.border} ${s.bg} ${s.text}`}>
              <Icon className="w-3.5 h-3.5 opacity-80" /> {ARCH_TYPE_LABEL[t]}
            </span>
          );
        })}
        <span className="flex items-center text-muted-foreground/60 italic normal-case tracking-normal ml-auto text-xs">
          Hover for details · Animated = real-time flow
        </span>
      </div>
      
      <div className="w-full h-[600px] border border-border/40 rounded-xl bg-surface/30 overflow-hidden shadow-inner">
        <ReactFlow
          nodes={layoutedNodes}
          edges={layoutedEdges}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.25 }}
          attributionPosition="bottom-right"
          proOptions={{ hideAttribution: true }}
        >
          <Background gap={24} color="#334155" size={1.5} className="opacity-40" />
          <Controls className="bg-background border-border text-foreground rounded-lg overflow-hidden shadow-lg" />
        </ReactFlow>
      </div>
    </div>
  );
}
