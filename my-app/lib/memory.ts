export interface MemoryItem {
  id: string;
  memory_type: "decision" | "comparison" | "evidence" | "visual" | "preference";
  source_id: string;
  source_type: string;
  summary: string;
  metadata: Record<string, any>;
  scope: "temporary" | "permanent";
  is_active: boolean;
  created_at: string;
  expires_at: string | null;
}

export interface PreferenceInsight {
  type: "preference_candidate";
  value: string;
  reason: string;
}

export interface MemoryContext {
  preferences: PreferenceInsight[];
  historical_patterns: string[];
  related_decisions: string[];
  consistency_warnings: string[];
}
