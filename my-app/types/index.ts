export interface ConfidenceScore {
  evidence_coverage: number;
  source_quality: number;
  contradiction_risk: number;
  decision_confidence: number;
}

export interface Evidence {
  title: string;
  url: string;
  claim: string;
  trust_score: number;
}

export interface DecisionDocument {
  id: string;
  question: string;
  executive_summary: string;
  recommendation_context: string;
  tradeoffs: string;
  alternatives: string;
  confidence: ConfidenceScore;
  evidence?: Evidence[];
  consensus?: string;
  evidence_generated_at?: string;
  version: number;
  created_at: string;
}

export interface ResearchResponse {
  session_id: string;
  job_id: string;
  status: string;
}

export interface JobStatusResponse {
  status: "queued" | "running" | "completed" | "failed";
  progress: number;
  step: string;
}

export interface SessionDocumentResponse {
  document: DecisionDocument | null;
}

export type PollingState = "idle" | "queued" | "running" | "completed" | "failed";

