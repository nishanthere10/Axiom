import {
  ResearchResponse,
  JobStatusResponse,
  SessionDocumentResponse,
} from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

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
export async function submitResearch(question: string, forceRefresh: boolean = false): Promise<ResearchResponse> {
  return apiFetch<ResearchResponse>("/research", {
    method: "POST",
    body: JSON.stringify({ question, force_refresh: forceRefresh }),
  });
}

/** Poll the status of a background research job. */
export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  return apiFetch<JobStatusResponse>(`/research/jobs/${jobId}`);
}

/** Fetch the completed decision document for a session. */
export async function getSessionDocument(sessionId: string): Promise<SessionDocumentResponse> {
  return apiFetch<SessionDocumentResponse>(`/research/sessions/${sessionId}`);
}
