# Codebase Report: Scrag (Atlas Research)

**Date**: 2026-06-04
**Project Scope**: Full-stack Next.js (React) Frontend + Python (FastAPI/LangGraph) Backend.

## 1. Architectural Overview

The `scrag` project operates a robust decision intelligence pipeline:
- **Frontend (`my-app/`)**: Built on Next.js, it offers a sophisticated, highly responsive UI using Tailwind CSS for styling and Framer Motion for animations. It embraces modern "high-agency" UI patterns (collapsible layouts, comparison views, side-by-side split panes).
- **Backend (`backend/`)**: Built on Python/FastAPI, it exposes endpoints for `/research` and `/compare`. The core logic is powered by **LangGraph**, orchestrating complex multi-agent workflows (decomposition, evidence gathering, structural diffing, memory analysis).
- **Infrastructure**: 
  - **Relational DB**: Postgres (via Supabase) for persisting sessions, jobs, and memory documents.
  - **Vector DB**: Pinecone for semantic similarity search over historical memories.
  - **LLM/Embeddings**: Google Gemini API (`models/gemini-embedding-2` and text models via LiteLLM/Instructor).

---

## 2. Pros (Strengths)

* **Robust Multi-Agent Architecture**: The use of LangGraph enables non-linear, stateful workflows. By decomposing tasks into discrete nodes (e.g., `retrieve_memory`, `analyze_memory`, `normalize_documents`), the logic is highly testable and extensible.
* **Asynchronous UX Patterns**: Intensive LLM tasks are pushed to Fastapi `BackgroundTasks` (e.g., memory creation/upserts). This decoupling ensures the user is not blocked waiting for secondary vector processing after the primary decision is returned.
* **Deterministic Diffing**: In the `/compare` workflow, structural diffing avoids using the LLM for exact text matching, relying on deterministic JSON comparisons (`dictdiffer`), drastically reducing hallucinations and token costs.
* **Strong Typing**: The backend enforces structural outputs using `pydantic` schemas paired with `instructor` and `litellm`. The frontend maintains strict TypeScript interfaces (`types/index.ts`).
* **Design Engineering & Polish**: The graph report highlights significant focus on UX heuristics, motion design, typography, and accessibility (communities 12, 13, 14, 15, 23). The UI feels incredibly premium.

---

## 3. Cons (Weaknesses)

* **High Node Coupling (God Nodes)**: As highlighted by the `GRAPH_REPORT.md`, there are "God Nodes" (e.g., `generate_chat_completion()`, `ResearchState`) with 11-14 edges. This centralization means changes to these core structures have a high blast radius.
* **Fragmented Communities**: The graph report detected 112 communities, many of which are "thin" or weakly connected. This suggests fragmented documentation or isolated scripts that aren't cleanly integrated into the main pipeline.
* **Error Swallowing**: In background tasks (like `store_memory.py` and `tasks.py`), exceptions are currently caught and printed (via `[DEBUG]` logs), but there is no dead-letter queue or retry mechanism. If Pinecone fails, the memory is lost forever.
* **Lack of Automated Testing**: Beyond manual testing and edge-case console logging, there is no formal test suite (pytest/jest) visible in the core pipeline flow.

---

## 4. Vulnerabilities & Risks

> [!WARNING]
> **API Key Initialization Failures**
> Because Pinecone and Gemini initialize at the top level of `pinecone_service.py` on boot, if keys are missing or invalid, the backend silently degrades. The system handles this gracefully by returning empty arrays, but the user is never notified in the UI that memory features are disabled.

> [!CAUTION]
> **Unauthenticated Endpoints**
> The FastAPI routes currently do not enforce JWT or Bearer token authentication. Anyone with the API URL can trigger heavy LLM workflows, potentially exhausting OpenAI/Gemini credits and rate limits.

* **CORS Exposure**: Ensure FastAPI CORS middleware restricts origins to just the deployed Next.js frontend domain to prevent unauthorized cross-origin requests.
* **LLM Prompt Injection**: The `/research` endpoint accepts arbitrary strings as technical questions. While they are passed to an LLM, there is a risk of prompt injection where a user could manipulate the prompt to leak system instructions or bypass logic.

---

## 5. Potential Improvements

### Short Term
1. **Health Check Endpoint**: Add a `/health` endpoint that actively verifies connections to Supabase, Pinecone, and Gemini API, so developers know immediately if the environment is misconfigured.
2. **UI Error Surfacing**: If `retrieve_memory` short-circuits due to missing API keys, send a warning flag to the frontend so the user knows memory isn't functioning.
3. **Retry Logic**: Implement `tenacity` or `celery` for background tasks, ensuring failed Supabase/Pinecone inserts are retried.

### Medium/Long Term
1. **Authentication & Rate Limiting**: Implement a dependency in FastAPI to validate Supabase JWT tokens. Add rate-limiting middleware (e.g., `slowapi`) to protect expensive LangGraph routes.
2. **Abstracting the God Nodes**: Refactor the heavily connected `generate_chat_completion` node by injecting smaller, domain-specific prompt handlers to reduce the monolithic dependency graph.
3. **Automated Testing Suite**: Introduce `pytest` for the backend, specifically mocking `instructor` to test the state transitions of the `decision_graph` and `comparison_graph` deterministically.
