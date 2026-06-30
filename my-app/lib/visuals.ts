export type VisualType = "decision_tree" | "architecture_diagram" | "summary_card";

export type DecisionNodeType = "root" | "decision" | "outcome" | "leaf";
export type ArchNodeType = "service" | "database" | "queue" | "client" | "gateway" | "cache" | "component";
export type HighlightType = "metric" | "tradeoff" | "warning" | "recommendation";

export interface DecisionTreeNode {
  id: string;
  label: string;
  node_type?: DecisionNodeType;
  description?: string;
}

export interface DecisionTreeEdge {
  source: string;
  target: string;
  label?: string;
}

export interface DecisionTreeSpec {
  type: "decision_tree";
  title: string;
  subtitle?: string;
  nodes: DecisionTreeNode[];
  edges: DecisionTreeEdge[];
}

export interface ArchitectureNode {
  id: string;
  label: string;
  type: string;
  node_type?: ArchNodeType;
  description?: string;
  spec?: string;
  group?: string;
}

export interface ArchitectureEdge {
  source: string;
  target: string;
  label?: string;
  animated?: boolean;
}

export interface ArchitectureDiagramSpec {
  type: "architecture_diagram";
  title: string;
  subtitle?: string;
  nodes: ArchitectureNode[];
  edges: ArchitectureEdge[];
}

export interface SummaryCardHighlight {
  label: string;
  value: string;
  highlight_type?: HighlightType;
}

export interface SummaryCardSpec {
  type: "summary_card";
  title: string;
  summary: string;
  confidence: string;
  consensus: string;
  highlights: SummaryCardHighlight[];
}

export type VisualSpec = DecisionTreeSpec | ArchitectureDiagramSpec | SummaryCardSpec;

