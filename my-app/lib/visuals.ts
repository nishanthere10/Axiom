export type VisualType = "decision_tree" | "architecture_diagram" | "summary_card";

export interface DecisionTreeNode {
  id: string;
  label: string;
}

export interface DecisionTreeEdge {
  source: string;
  target: string;
  label?: string;
}

export interface DecisionTreeSpec {
  type: "decision_tree";
  title: string;
  nodes: DecisionTreeNode[];
  edges: DecisionTreeEdge[];
}

export interface ArchitectureDiagramSpec {
  type: "architecture_diagram";
  title: string;
  mermaid_syntax: string;
}

export interface SummaryCardHighlight {
  label: string;
  value: string;
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
