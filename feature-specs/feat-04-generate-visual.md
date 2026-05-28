# EXECUTION SPEC

# F-004 — Visual Decision Intelligence

# TARGET: Coding Agent

Status: READY FOR IMPLEMENTATION
Priority: P0
Depends On: F-001 + F-002 + F-003 Complete

---

# READ FIRST

Implement exactly this feature.

Do NOT:

* add AI image generation
* add WebSockets
* add workers
* add queues
* add vector DB
* add auth
* add editing
* add draggable diagram builders
* redesign research flow

If blocked:
implement simplest working version.

Research generation must continue working even if visual generation fails.

---

# FEATURE GOAL

Upgrade Atlas from text-based decision intelligence to visual decision intelligence.

Atlas should generate structured engineering visuals that help users understand:

* architecture
* reasoning
* tradeoffs
* recommendations
* decision flow

Visuals are generated only when relevant.

Visuals are NOT decorative.

---

# PRODUCT RULES

Accepted visual types:

Decision Trees

Architecture Diagrams

Research Summary Cards

Reject all other visual types.

---

Visual source:

Decision

*

Evidence

*

Confidence

Do NOT generate visuals from question alone.

---

Visual generation:

Conditional only.

Do not generate visuals for every research session.

---

Visual rendering:

Frontend renders from structured JSON spec.

Backend does NOT generate images.

---

Persistence:

Visuals must be stored in DB.

---

Editing:

No editing in V1.

---

Regeneration:

Supported.

User may regenerate visuals.

---

Failure handling:

If visual generation fails:

skip visuals

↓

continue research

Never fail research because visuals failed.

---

Visual count:

max 3 visuals

---

# IMPLEMENTATION ORDER

1.

Schemas

↓

2.

Database changes

↓

3.

Visual generation nodes

↓

4.

Validation layer

↓

5.

Graph integration

↓

6.

Frontend renderers

↓

7.

Regeneration flow

↓

8.

Testing

Do not change order.

---

# DIRECTORY OWNERSHIP

apps/

web/

api/

orchestrator/

Only modify files inside these folders.

---

# FILES TO CREATE

apps/orchestrator/

nodes/generate_visual_spec.py

nodes/validate_visual_spec.py

schemas/visuals.py

---

apps/web/

src/components/visuals/VisualRenderer.tsx

src/components/visuals/DecisionTreeRenderer.tsx

src/components/visuals/ArchitectureDiagramRenderer.tsx

src/components/visuals/ResearchSummaryCardRenderer.tsx

src/components/visuals/VisualErrorBoundary.tsx

src/components/visuals/RegenerateVisualButton.tsx

src/lib/visuals.ts

---

# FILES TO MODIFY

apps/orchestrator/

graph/decision_graph.py

nodes/format.py

---

apps/api/

research.py

schemas/research.py

---

apps/web/

src/components/DecisionDocument.tsx

---

# INSTALLATION

Frontend:

npm install reactflow

npm install mermaid

No image generation libraries.

---

# DATABASE CHANGES

Modify existing:

decision_documents

Add:

visuals JSONB

Optional:

visual_generated_at TIMESTAMP

No new tables.

---

# API CONTRACTS

Keep existing.

POST /research

Response now includes:

{
"visuals":[]
}

---

POST /research/regenerate-visuals

Request:

{
"session_id":""
}

Response:

{
"visuals":[]
}

Regenerates visuals only.

Does not rerun research.

---

# GRAPH FLOW

START

↓

decompose_question

↓

generate_queries

↓

collect_evidence

↓

extract_claims

↓

score_evidence

↓

generate_decision

↓

(parallel branch)
├── build_confidence
└── generate_visual_spec

↓

(join)
validate_visual_spec

↓

format_document

↓

END

Do not create separate visual graph.

Extend existing graph.

---

# VISUAL GENERATION FLOW

Input:

decision

evidence

confidence

↓

detect relevant visuals

↓

generate visual specs

↓

validate specs

↓

persist

↓

frontend render

---

# NODE REQUIREMENTS

generate_visual_spec

LLM node.

Input:

question

decision

evidence

confidence

Output:

{
"visuals":[]
}

Rules:

max 3 visuals

Return empty array if visuals unnecessary.

Never generate unsupported visual types.

---

# VISUAL TYPE RULES

Decision Tree

Use when:

contextual recommendations exist

Example:

If scalability matters

↓

Use X

---

Architecture Diagram

Use when:

system architecture is discussed

Must represent:

user-specific architecture

NOT generic framework diagrams.

---

Research Summary Card

Use when:

research contains high-level insights

Must summarize:

recommendation

confidence

consensus

key insights

---

# VALIDATION NODE

validate_visual_spec

Deterministic.

No LLM.

Validate:

required fields

supported types

schema correctness

max visual count

Rules:

Invalid visuals must be skipped.

Never fail entire research.

---

# VISUAL SCHEMAS

DecisionTree

{
"type":"decision_tree",

"title":"",

"nodes":[],

"edges":[]
}

---

ArchitectureDiagram

{
"type":"architecture_diagram",

"title":"",

"components":[],

"connections":[]
}

---

ResearchSummaryCard

{
"type":"summary_card",

"title":"",

"summary":"",

"confidence":"",

"consensus":"",

"highlights":[]
}

---

# RELEVANCE DETECTION

Single LLM Step.

The `generate_visual_spec` LLM node evaluates relevance and generates the visual in one structured output call.

If the LLM determines no visuals are helpful or the topic does not warrant them, it returns an empty `visuals` array.

Rules:
No irrelevant visuals.
No duplicate visual types.

---

# FRONTEND RENDERING

Frontend renders visuals from JSON.

Never render raw LLM output.

Flow:

visual spec

↓

renderer

↓

React component

---

# RENDERERS

VisualRenderer

Master router.

Chooses renderer by type.

---

DecisionTreeRenderer

Use ReactFlow.
MUST use an auto-layout library (e.g., `dagre`) to automatically calculate x/y positions based on node relationships. Do NOT rely on the LLM to output spatial coordinates.

---

ArchitectureDiagramRenderer

Use Mermaid. Let Mermaid handle the auto-layout engine natively.

---

ResearchSummaryCardRenderer

Use native React UI components.

---

# UI ORDER

Decision

↓

Evidence

↓

Visuals

↓

Confidence

Do not reorder.

---

# REGENERATION FLOW

User clicks:

Regenerate Visuals

↓

Backend reruns:

generate_visual_spec

↓

validate_visual_spec

↓

persist

↓

return updated visuals

Do NOT rerun full research.

---

# VALIDATION RULES

Visual count:

max 3

---

Duplicate visual types:

reject duplicates

---

Unsupported types:

reject

---

Invalid schema:

skip visual

---

# PERFORMANCE TARGETS

research:

<25 sec

visual regeneration:

<10 sec

frontend render:

<1 sec

---

# ERROR HANDLING

If visual generation fails:

log

↓

skip visuals

↓

continue response

---

If renderer fails:

show fallback UI

Do not crash page.

---

# TEST CASES

Architecture question

↓

architecture diagram generated

---

Decision comparison

↓

decision tree generated

---

Research summary

↓

summary card generated

---

Invalid visual schema

↓

skipped safely

---

Regenerate visuals

↓

new visuals returned

---

Visual renderer failure

↓

fallback UI

---

# NON GOALS

Do NOT implement:

AI image generation

SVG export

drag-drop editing

interactive editing

diagram persistence outside DB

multi-user visual collaboration

PDF export

presentation mode

animated diagrams

real-time visual updates

---

# DONE CONDITION

Feature complete only if:

Relevant visuals generated

Visuals validated

Frontend renders correctly

Invalid visuals skipped safely

Regeneration works

Feature 1 works

Feature 2 works

Feature 3 works
