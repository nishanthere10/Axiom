import {
  ResearchResponse,
  JobStatusResponse,
  SessionDocumentResponse,
  SessionHistoryResponse,
  SavedComparisonsResponse,
} from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.API_BASE_URL || "http://localhost:8000";

async function apiFetch<T>(path: string, token: string, options?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
      ...options,
    });
  } catch (err: any) {
    console.error(`Network or CORS error fetching ${path}:`, err);
    throw new Error(`Failed to reach the server. Please ensure the backend is running at ${API_BASE_URL}. Details: ${err.message}`);
  }

  if (!res.ok) {
    let message = `API error: ${res.status}`;
    try {
      const body = await res.json();
      message = body?.detail ?? message;
    } catch {
      // ignore parse errors
    }
    throw new Error(message);
  }

  return res.json() as Promise<T>;
}

/** Submit a technical question and start a research job. */
export async function submitResearch(question: string, forceRefresh: boolean = false, token: string): Promise<ResearchResponse> {
  return apiFetch<ResearchResponse>("/research", token, {
    method: "POST",
    body: JSON.stringify({ question, force_refresh: forceRefresh }),
  });
}

/** Poll the status of a background research job. */
export async function getJobStatus(jobId: string, token: string): Promise<JobStatusResponse> {
  return apiFetch<JobStatusResponse>(`/research/jobs/${jobId}`, token);
}

/** Fetch the completed decision document for a session. */
export async function getSessionDocument(sessionId: string, token: string): Promise<SessionDocumentResponse> {
  return apiFetch<SessionDocumentResponse>(`/research/sessions/${sessionId}`, token);
}

/** Fetch a paginated list of recent research sessions. */
export async function getSessionHistory(limit: number = 10, offset: number = 0, token: string): Promise<SessionHistoryResponse> {
  return apiFetch<SessionHistoryResponse>(`/research/history?limit=${limit}&offset=${offset}`, token);
}

/** Fetch all saved comparisons. */
export async function getSavedComparisons(token: string): Promise<SavedComparisonsResponse> {
  return apiFetch<SavedComparisonsResponse>("/compare/saved", token);
}
