# EXECUTION SPEC

# F-001 — Generate Technical Decision Document

Mode: CODE IMPLEMENTATION ONLY

---

# RULES

Implement only what is explicitly requested.

Do NOT:

* redesign architecture
* add features
* optimize early
* add auth
* add retrieval
* add vector search
* improve UX
* add analytics
* introduce new libraries

Follow existing stack decisions.

If blocked:
implement minimal working fallback.

---

# FEATURE GOAL

Build the first complete Atlas workflow.

User enters a technical question.

System returns a reusable decision document.

Flow:

Question

↓

Generate

↓

Persist

↓

Display

No external retrieval.

No knowledge graph.

No history.

No evaluation.

No sources.

---

# IMPLEMENTATION ORDER

1.

Schemas

↓

2.

Backend API

↓

3.

LangGraph

↓

4.

Background execution

↓

5.

Persistence

↓

6.

Frontend

↓

7.

Testing

Do not change order.

---

# DIRECTORY OWNERSHIP

apps/

web/

api/

orchestrator/

worker/

Only modify files inside these areas.

---

# FILES TO CREATE

apps/api/

app/api/research.py

app/services/research_service.py

app/schemas/research.py

app/models/session.py

app/models/document.py

---

apps/orchestrator/

graph/decision_graph.py

nodes/decompose.py

nodes/generate.py

nodes/confidence.py

nodes/format.py

state/research_state.py

---

apps/worker/

tasks/research_task.py

celery_app.py

---

apps/web/

src/app/research/page.tsx

src/components/QuestionInput.tsx

src/components/ResearchProgress.tsx

src/components/DecisionDocument.tsx

src/lib/api.ts

---

# API CONTRACTS

POST /research

Request:

{
"question":"string"
}

Response:

{
"session_id":"uuid",
"job_id":"uuid",
"status":"started"
}

---

GET /research/jobs/{job_id}

Response:

{
"status":"queued|running|completed|failed",
"progress":0,
"step":""
}

---

GET /research/sessions/{session_id}

Response:

{
"document":{}
}

Do not modify response shape.

---

# VALIDATION

Question:

required

min=10

max=1000

Reject invalid requests.

---

# DATA MODEL

DecisionDocument

{
id,

question,

executive_summary,

recommendation_context,

tradeoffs,

alternatives,

confidence:{

evidence_coverage,

source_quality,

contradiction_risk,

decision_confidence

},

version,

created_at
}

Persist exact structure.

No markdown.

---

# LANGGRAPH FLOW

START

↓

decompose_question

↓

generate_decision

↓

build_confidence

↓

format_document

↓

END

No extra nodes.

---

# STATE OBJECT

{
question,

summary,

recommendation,

tradeoffs,

alternatives,

confidence,

status
}

---

# BACKGROUND EXECUTION

POST /research

must:

create session

enqueue task

return immediately

Worker:

run graph

save result

update progress

Retry:

max=2

Retry only:

timeout

temporary failure

---

# FRONTEND FLOW

/research

QuestionInput

↓

submit

↓

poll every 2 seconds

↓

show progress

↓

render document

No WebSockets.

---

# POLLING STATES

idle

queued

running

completed

failed

---

# PERSISTENCE

Create:

research_sessions

decision_documents

research_jobs

Store:

status

timestamps

payload

version

Autosave:

draft

↓

partial

↓

complete

---

# ERROR HANDLING

400

invalid input

---

500

generation failure

---

timeout

retry

---

unknown

generic error

---

# PERFORMANCE TARGET

submit <500ms

generate <20s

restore <2s

---

# TEST CASES

Question valid

→ document returned

---

Question empty

→ validation

---

Generation timeout

→ retry

---

Refresh

→ restore

---

# DONE CONDITION

Feature is done when:

Question can be submitted

Progress visible

Decision generated

Version stored

Refresh restores result

No crashes
