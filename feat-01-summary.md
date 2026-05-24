# F-001 — Generate Technical Decision Document
# Summary for Developer Reference

---

## What This Feature Does

A user types a technical question (e.g., _"Should I use PostgreSQL or MongoDB for this project?"_).

Atlas runs an AI pipeline in the background, generates a structured **Decision Document**, saves it to the database, and shows it on screen. The user can refresh the page and the result is still there.

---

## The Full Flow (Plain English)

```
User types question
       ↓
Frontend sends POST /research
       ↓
Backend creates DB records (session + job) and queues a Celery task
       ↓
Backend responds immediately with { session_id, job_id }
       ↓
Frontend starts polling GET /research/jobs/{job_id} every 2 seconds
       ↓
Celery worker picks up the task and runs the LangGraph pipeline:
   Step 1 — decompose_question  : Groq breaks down the question
   Step 2 — generate_decision   : Groq writes the full decision
   Step 3 — build_confidence    : Groq scores the confidence
   Step 4 — format_document     : Assembles the final document
       ↓
Worker saves the document to Supabase
Worker marks job as "completed"
       ↓
Frontend detects "completed" status via polling
Frontend fetches GET /research/sessions/{session_id}
       ↓
Decision Document is rendered on screen
```

---

## What Gets Built

### Backend (Python / FastAPI)

| File | What it does |
|---|---|
| `backend/api/routes/research.py` | The 3 API endpoints |
| `backend/api/schemas/research.py` | Pydantic request/response shapes |
| `backend/models/research.py` | Pydantic DB models |
| `backend/agents/state/research_state.py` | LangGraph state definition |
| `backend/agents/nodes/decompose.py` | Node 1: breaks down the question |
| `backend/agents/nodes/generate.py` | Node 2: generates the decision content |
| `backend/agents/nodes/confidence.py` | Node 3: scores how confident we are |
| `backend/agents/nodes/format.py` | Node 4: assembles final document |
| `backend/agents/graph/decision_graph.py` | Wires all 4 nodes into a pipeline |
| `backend/workers/tasks.py` | Celery task that runs the pipeline |

### Frontend (Next.js / TypeScript)

| File | What it does |
|---|---|
| `my-app/app/research/page.tsx` | The `/research` page |
| `my-app/components/features/QuestionInput.tsx` | The question form |
| `my-app/components/features/ResearchProgress.tsx` | Polling + progress display |
| `my-app/components/features/DecisionDocument.tsx` | Renders the final document |
| `my-app/lib/api.ts` | Typed API client functions |

### Database (Supabase — run SQL manually in Dashboard)

| Table | What it stores |
|---|---|
| `research_sessions` | One row per research run (question, status) |
| `research_jobs` | Background job state (queued/running/completed/failed, progress %) |
| `decision_documents` | The final generated document (all fields) |

---

## The Decision Document Structure

Every completed research produces this exact JSON structure:

```json
{
  "id": "uuid",
  "question": "Should I use PostgreSQL or MongoDB?",
  "executive_summary": "...",
  "recommendation_context": "...",
  "tradeoffs": "...",
  "alternatives": "...",
  "confidence": {
    "evidence_coverage": 0.85,
    "source_quality": 0.70,
    "contradiction_risk": 0.20,
    "decision_confidence": 0.80
  },
  "version": 1,
  "created_at": "2025-01-01T00:00:00Z"
}
```

---

## The LangGraph Pipeline

```
START
  ↓
decompose_question    ← Groq breaks the question into: intent, concerns, criteria
  ↓
generate_decision     ← Groq writes: summary, recommendation, tradeoffs, alternatives
  ↓
build_confidence      ← Groq scores: evidence coverage, source quality, contradiction risk
  ↓
format_document       ← Assembles everything into the DecisionDocument structure
  ↓
END
```

Uses model: **llama-3.3-70b-versatile** via Groq.

---

## API Endpoints

| Method | Route | What it does |
|---|---|---|
| `POST` | `/research` | Submit a question. Returns `session_id` and `job_id`. |
| `GET` | `/research/jobs/{job_id}` | Check the background job status and progress. |
| `GET` | `/research/sessions/{session_id}` | Fetch the completed decision document. |

---

## Validation Rules

- Question is **required**
- Question must be **at least 10 characters**
- Question must be **at most 1000 characters**
- Anything else → 400 error

---

## Important Constraints (from feat spec)

- ❌ No authentication on any endpoint in this feature
- ❌ No vector search / retrieval / knowledge graph
- ❌ No WebSockets — polling only (every 2 seconds)
- ❌ No new libraries beyond existing stack
- ✅ Celery retries max 2 times (only on timeout or transient errors)
- ✅ Response shapes are fixed — do not modify

---

## Done When

- [ ] User can type a question and submit it
- [ ] User sees progress while it generates
- [ ] Decision document appears when complete
- [ ] Refreshing the page still shows the result
- [ ] No crashes on valid or invalid input
