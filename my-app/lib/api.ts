import {
  ResearchResponse,
  JobStatusResponse,
  SessionDocumentResponse,
  SessionHistoryResponse,
  SavedComparisonsResponse,
  DecisionRecord,
  DecisionListResponse,
} from "@/types";

const RAW_API_URL = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.API_BASE_URL || (process.env.NODE_ENV === "production" ? "https://atlas-1sr4.onrender.com" : "http://127.0.0.1:8000");
export const API_BASE_URL = RAW_API_URL.replace(/\/$/, "");

export async function apiFetch<T>(
  endpoint: string,
  token: string,
  options?: RequestInit & { getToken?: () => Promise<string | null> },
): Promise<T> {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${API_BASE_URL}${cleanEndpoint}`;

  // Extract getToken before spreading options into fetch
  const { getToken, ...fetchOptions } = options ?? {};

  async function doFetch(bearerToken: string): Promise<Response> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${bearerToken}`,
    };
    
    if (typeof window !== "undefined") {
      const workspaceId = localStorage.getItem("activeWorkspaceId");
      if (workspaceId) {
        headers["x-workspace-id"] = workspaceId;
      }
    }

    return fetch(url, {
      headers: headers,
      ...fetchOptions,
    });
  }

  let res: Response;
  try {
    res = await doFetch(token);
  } catch (err: any) {
    console.error(`Network or CORS error fetching ${url}:`, err);
    // Gracefully catch network errors and return a safe fallback state
    return {
      status: "offline",
      sessions: [],
      comparisons: [],
      error: "Failed to reach the server. Backend may be offline."
    } as any as T;
  }

  // On 401, silently refresh the Clerk token and retry once
  if (res.status === 401 && getToken) {
    try {
      const freshToken = await getToken();
      if (freshToken) {
        res = await doFetch(freshToken);
      }
    } catch {
      // If refresh itself fails, fall through to the error below
    }
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

  if (res.status === 204) {
    return {} as T;
  }

  return res.json() as Promise<T>;
}

/** Submit a technical question and start a research job. (DEPRECATED) */
export async function submitResearch(question: string, forceRefresh: boolean = false, token: string, getToken?: () => Promise<string | null>): Promise<ResearchResponse> {
  return apiFetch<ResearchResponse>("/research", token, {
    method: "POST",
    body: JSON.stringify({ question, force_refresh: forceRefresh }),
    getToken,
  });
}

/** Poll the status of a background research job. */
export async function getJobStatus(jobId: string, token: string, getToken?: () => Promise<string | null>): Promise<JobStatusResponse> {
  return apiFetch<JobStatusResponse>(`/research/jobs/${jobId}`, token, { getToken });
}

/** Fetch the completed decision document for a session. */
export async function getSessionDocument(sessionId: string, token: string, getToken?: () => Promise<string | null>): Promise<SessionDocumentResponse> {
  return apiFetch<SessionDocumentResponse>(`/research/sessions/${sessionId}`, token, { getToken });
}

/** Fetch all saved comparisons. */
export async function getSavedComparisons(token: string, getToken?: () => Promise<string | null>): Promise<SavedComparisonsResponse> {
  return apiFetch<SavedComparisonsResponse>("/compare/saved", token, { getToken });
}

/** Submit research within a workspace (workspace-scoped route) */
export async function submitWorkspaceResearch(
  workspaceId: string,
  question: string,
  forceRefresh: boolean = false,
  token: string,
  getToken?: () => Promise<string | null>,
  projectId?: string
): Promise<ResearchResponse> {
  return apiFetch<ResearchResponse>(`/workspaces/${workspaceId}/research`, token, {
    method: "POST",
    body: JSON.stringify({ 
      question, 
      force_refresh: forceRefresh,
      project_id: projectId || undefined 
    }),
    getToken,
  });
}

/** Get research history within a workspace */
export async function getWorkspaceResearchHistory(
  workspaceId: string,
  limit: number = 10,
  offset: number = 0,
  token: string,
  getToken?: () => Promise<string | null>
): Promise<SessionHistoryResponse> {
  return apiFetch<SessionHistoryResponse>(
    `/workspaces/${workspaceId}/research/history?limit=${limit}&offset=${offset}`,
    token,
    { getToken }
  );
}

/** List decisions within a workspace */
export async function listWorkspaceDecisions(
  workspaceId: string,
  token: string,
  getToken?: () => Promise<string | null>
): Promise<DecisionListResponse> {
  return apiFetch<DecisionListResponse>(`/workspaces/${workspaceId}/decisions`, token, { getToken });
}

/** Get workspace activity feed */
export async function getWorkspaceActivity(
  workspaceId: string,
  limit: number = 20,
  token: string,
  getToken?: () => Promise<string | null>
): Promise<{ activity: any[] }> {
  return apiFetch<{ activity: any[] }>(
    `/workspaces/${workspaceId}/activity?limit=${limit}`,
    token,
    { getToken }
  );
}

/** Search decisions within a workspace */
export async function searchWorkspaceDecisions(
  workspaceId: string,
  q: string,
  status: string = "",
  limit: number = 20,
  token: string,
  getToken?: () => Promise<string | null>
): Promise<{ results: any[]; total: number }> {
  const params = new URLSearchParams({ q, limit: String(limit) });
  if (status) params.set("status", status);
  return apiFetch<{ results: any[]; total: number }>(
    `/workspaces/${workspaceId}/decisions/search?${params}`,
    token, { getToken }
  );
}

/** Get full decision detail with research context and history */
export async function getDecisionFull(
  workspaceId: string,
  decisionId: string,
  token: string,
  getToken?: () => Promise<string | null>
): Promise<{ decision: any; research: any; history: any[] }> {
  return apiFetch(
    `/workspaces/${workspaceId}/decisions/${decisionId}/full`,
    token, { getToken }
  );
}

/** Update decision status with optional note */
export async function updateDecisionStatus(
  workspaceId: string,
  decisionId: string,
  status: string,
  note?: string,
  token: string = "",
  getToken?: () => Promise<string | null>
): Promise<any> {
  return apiFetch(
    `/workspaces/${workspaceId}/decisions/${decisionId}`,
    token,
    {
      method: "PATCH",
      body: JSON.stringify({ status, note }),
      getToken,
    }
  );
}

/** Create a decision within a workspace */
export async function createDecision(
  workspaceId: string,
  data: any,
  token: string,
  getToken?: () => Promise<string | null>
): Promise<any> {
  return apiFetch(
    `/workspaces/${workspaceId}/decisions`,
    token,
    {
      method: "POST",
      body: JSON.stringify(data),
      getToken,
    }
  );
}
