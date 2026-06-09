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

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function authHeaders(token: string): HeadersInit {
  return {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`,
  };
}

export async function getRecentSessions(token: string): Promise<{ id: string; question: string; created_at: string }[]> {
  const res = await fetch(`${API_BASE}/research/history`, {
    cache: "no-store",
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error("Failed to load history");
  const data = await res.json();
  return data.sessions;
}

export async function getSuggestions(sessionId: string, token: string): Promise<SuggestionItem[]> {
  const res = await fetch(`${API_BASE}/compare/suggestions/${sessionId}`, {
    cache: "no-store",
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error("Failed to load suggestions");
  const data = await res.json();
  return data.suggestions;
}

export async function submitComparison(sessionA: string, sessionB: string, token: string): Promise<{ comparison_id: string; comparison: Comparison }> {
  const res = await fetch(`${API_BASE}/compare`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ session_a: sessionA, session_b: sessionB }),
    cache: "no-store"
  });
  
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Comparison failed");
  }
  
  return res.json();
}

export async function getComparison(comparisonId: string, token: string): Promise<Comparison> {
  const res = await fetch(`${API_BASE}/compare/${comparisonId}`, {
    cache: "no-store",
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error("Comparison not found");
  const data = await res.json();
  return data.comparison;
}

export async function saveComparison(comparisonId: string, token: string): Promise<boolean> {
  const res = await fetch(`${API_BASE}/compare/save`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ comparison_id: comparisonId })
  });
  if (!res.ok) throw new Error("Failed to save comparison");
  const data = await res.json();
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
  const res = await fetch(`${API_BASE}/compare/saved`, {
    cache: "no-store",
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error("Failed to load saved comparisons");
  const data = await res.json();
  return data.comparisons;
}
