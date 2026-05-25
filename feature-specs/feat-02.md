# EXECUTION SPEC

# F-002 — Historical Decision Comparison

---

# READ FIRST

Implement exactly this feature.

Do NOT:

* redesign product
* introduce queues
* add auth
* add retrieval
* add vectors
* add WebSockets
* add evaluation
* add observability
* add new persistence models beyond this spec

If blocked:
implement simplest working version.

Feature 1 behavior must remain unchanged.

---

# FEATURE GOAL

Allow users to compare two previous Atlas research sessions and understand:

* what changed
* why it changed
* whether action is required

Comparison must be explainable.

Atlas does NOT decide for the user.

Atlas explains decision evolution.

---

# PRODUCT RULES

Session selection:

Supported:

Manual selection

*

Suggested sessions

User always chooses.

Never auto-compare.

---

Persistence:

Comparison generation:

temporary

Saving:

optional

User decides.

---

Explanation:

Generated using:

Decision Document A

*

Decision Document B

*

Structural Diff

Never generate explanation from diff only.

---

# IMPLEMENTATION ORDER

1.

Schemas

↓

2.

Database

↓

3.

Backend API

↓

4.

LangGraph

↓

5.

Comparison Service

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

Only modify files inside these areas.

---

# FILES TO CREATE

apps/api/

app/api/compare.py

app/services/compare_service.py

app/services/suggestion_service.py

app/schemas/compare.py

app/models/comparison.py

---

apps/orchestrator/

graph/comparison_graph.py

nodes/load_sessions.py

nodes/normalize_documents.py

nodes/generate_structural_diff.py

nodes/generate_explanation.py

nodes/generate_impact.py

nodes/format_comparison.py

state/comparison_state.py

---

apps/web/

src/app/compare/page.tsx

src/components/compare/SessionSelector.tsx

src/components/compare/SuggestedSessions.tsx

src/components/compare/ComparisonProgress.tsx

src/components/compare/StructuralDiff.tsx

src/components/compare/DecisionEvolution.tsx

src/components/compare/ImpactSummary.tsx

src/components/compare/SaveComparison.tsx

src/lib/compare.ts

---

# DATABASE CHANGES

Create one table.

comparisons

Fields:

id

session_a

session_b

summary

structural_diff

decision_evolution

impact_summary

saved

created_at

Rules:

saved=false by default

No comparison jobs table.

No versioning.

No soft delete.

---

# API CONTRACTS

POST /compare

Request:

{
"session_a":"uuid",

"session_b":"uuid"
}

Response:

{
"comparison_id":"uuid",

"comparison":{
}
}

Run synchronously.

No jobs.

No polling.

---

GET /compare/{comparison_id}

Response:

{
"comparison":{
}
}

404 if not found.

---

POST /compare/save

Request:

{
"comparison_id":"uuid"
}

Response:

{
"saved":true
}

---

GET /compare/suggestions/{session_id}

Response:

{
"suggestions":[]
}

Return max 5.

---

# SESSION SUGGESTION LOGIC

Score:

0.5 × Question Similarity

*

0.3 × Recommendation Similarity

*

0.2 × Time Proximity

No LLM.

No embeddings.

Deterministic only.

Return top 5.

---

# COMPARISON FLOW

Load Session A

↓

Load Session B

↓

Normalize

↓

Structural Diff

↓

Generate Explanation

↓

Generate Impact

↓

Format

↓

Return

↓

Optional Save

---

# LANGGRAPH FLOW

START

↓

load_sessions

↓

normalize_documents

↓

generate_structural_diff

↓

generate_explanation

↓

generate_impact

↓

format_comparison

↓

END

No extra nodes.

---

# NODE REQUIREMENTS

load_sessions

Input:

session ids

Output:

decision docs

---

normalize_documents

Convert both:

{
recommendation_context,

tradeoffs,

alternatives,

confidence
}

to comparable structure.

No generation.

---

generate_structural_diff

Compute:

recommendation changes

tradeoff changes

alternative changes

confidence changes

Deterministic.

No LLM.

---

generate_explanation

Input:

Document A

Document B

Structural Diff

Generate:

why decision changed

decision evolution

confidence commentary

Use model.

---

generate_impact

Generate:

recommended action

migration needed

follow-up suggestions

Use model.

---

format_comparison

Produce final schema.

---

# COMPARISON OUTPUT

{
"id":"",

"session_a":"",

"session_b":"",

"structural_diff":{

"recommendation":"",

"tradeoffs":"",

"alternatives":"",

"confidence":""

},

"decision_evolution":"",

"impact_summary":"",

"created_at":""
}

No markdown.

Store JSON.

---

# FRONTEND FLOW

Route:

/compare

User selects:

session A

session B

↓

submit

↓

show progressive rendering

↓

show comparison

↓

offer save

---

# RENDER ORDER

Render in this order.

1.

Structural Diff

↓

2.

Decision Evolution

↓

3.

Impact Summary

↓

4.

Save Comparison

Do not change order.

---

# PROGRESS STATES

Comparing Decisions...

↓

Analyzing Differences...

↓

Explaining Decision Changes...

↓

Generating Impact...

↓

Complete

No percentages.

No streaming tokens.

UI controlled.

---

# ERROR STATES

400

invalid session ids

---

404

session not found

---

500

comparison failed

---

unknown

generic error

Do not retry.

---

# VALIDATION

session_a:

required

UUID

---

session_b:

required

UUID

---

Reject same session comparison.

Return 400.

---

# PERFORMANCE TARGET

suggestions:

<500ms

comparison:

<20 sec

save:

<1 sec

---

# TEST CASES

Compare valid sessions

→ comparison returned

---

Compare same session

→ validation error

---

Save comparison

→ persists

---

Refresh compare page

→ comparison reloads

---

Suggested sessions

→ returns <=5

---

# NON GOALS

Do NOT implement:

history timeline

multi-compare

auth

sharing

vector similarity

confidence recalculation

real streaming

background workers

evaluation

analytics

---

# DONE CONDITION

Feature is complete only if:

User can compare two sessions

Suggestions appear

Explanation generated

Impact generated

Save optional

Refresh restores saved comparisons

Feature 1 still works
