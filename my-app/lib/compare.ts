export interface SuggestionItem {
  session_id: string;
  question: string;
  created_at: string;
  score: number;
}

export interface StructuralDiff {
  recommendation: string;
  tradeoffs: string;
  alternatives: string;
  confidence: string;
  evidence?: string;
  consensus?: string;
}

export interface KeyChange {
  field: string;
  before: string;
  after: string;
  change_type: "major" | "minor" | "improved" | "unchanged";
}

export interface DecisionEvolution {
  verdict: string;
  key_changes: KeyChange[];
  reasoning: string | string[];
}

export interface ImpactSummary {
  risk_level: "low" | "medium" | "high";
  action_items: string[];
  migration_needed: boolean;
  breaking_changes: boolean;
  memory_context?: any;
}

export interface Comparison {
  id: string;
  session_a: string;
  session_b: string;
  structural_diff: StructuralDiff;
  decision_evolution: DecisionEvolution;
  impact_summary: ImpactSummary;
  visuals?: any[];
  created_at: string;
}

import { apiFetch } from "@/lib/api";

export async function getRecentSessions(token: string, workspaceId?: string): Promise<{ id: string; question: string; created_at: string }[]> {
  let wsId = workspaceId;
  if (!wsId && typeof window !== "undefined") {
    wsId = localStorage.getItem("activeWorkspaceId") || undefined;
  }
  const endpoint = wsId ? `/workspaces/${wsId}/research/history` : "/research/history";
  const data = await apiFetch<{ sessions: any[] }>(endpoint, token, { cache: "no-store" });
  return data.sessions || [];
}

export async function getSuggestions(sessionId: string, token: string): Promise<SuggestionItem[]> {
  const data = await apiFetch<{ suggestions: SuggestionItem[] }>(`/compare/suggestions/${sessionId}`, token, { cache: "no-store" });
  return data.suggestions;
}

export async function submitComparison(sessionA: string, sessionB: string, token: string): Promise<{ comparison_id: string; comparison: Comparison }> {
  return apiFetch<{ comparison_id: string; comparison: Comparison }>("/compare", token, {
    method: "POST",
    body: JSON.stringify({ session_a: sessionA, session_b: sessionB }),
    cache: "no-store"
  });
}

export async function getComparison(comparisonId: string, token: string): Promise<Comparison> {
  const data = await apiFetch<{ comparison: Comparison }>(`/compare/${comparisonId}`, token, { cache: "no-store" });
  return data.comparison;
}

export async function saveComparison(comparisonId: string, token: string): Promise<boolean> {
  const data = await apiFetch<{ saved: boolean }>("/compare/save", token, {
    method: "POST",
    body: JSON.stringify({ comparison_id: comparisonId })
  });
  return data.saved;
}

export interface SavedComparisonItem {
  id: string;
  session_a: string;
  session_b: string;
  summary: string;
  created_at: string;
}

export async function getSavedComparisons(token: string): Promise<SavedComparisonItem[]> {
  const data = await apiFetch<{ comparisons: SavedComparisonItem[] }>("/compare/saved", token, { cache: "no-store" });
  return data.comparisons;
}
