# EXECUTION SPEC

# F-005 — Research Memory System


# READ FIRST

Implement exactly this feature.

Do NOT:

* redesign memory architecture
* add agents
* add outcome tracking
* add knowledge graphs
* add Redis
* add WebSockets
* add MCP
* add multi-user memory sharing
* add memory editing
* add memory deletion workflows

If blocked:

implement simplest working version.

Previous features must continue functioning.

---

# FEATURE GOAL

Transform Atlas from a research engine into a research partner.

Atlas should remember:

* previous decisions
* previous comparisons
* previous evidence
* previous visuals
* inferred preferences

and use relevant historical context to improve future research.

Atlas memory must support:

* personalization
* contextual recall
* decision consistency

---

# PRODUCT PHILOSOPHY

Atlas owns memory.

LLMs do not.

Memory is created by:

store

↓

retrieve

↓

inject

Memory is not chat history.

Memory is reusable research intelligence.

---

# MEMORY TYPES

Supported:

Decision

Comparison

Evidence

Visual

Preference

All memory objects use a unified schema.

---

# MEMORY MODEL

Store:

Raw Artifact

*

Memory Summary

Raw artifact:

stored in Postgres

Memory summary:

stored in Postgres

*

embedded in Pinecone

Do not embed raw documents.

---

# MEMORY LIFECYCLE

Research Completed

↓

Generate Memory Summary

↓

Store Temporary Memory

↓

TTL 30 Days

↓

User Saves?

YES

↓

Permanent Memory

NO

↓

Expire

---

# MEMORY SCOPES

temporary

permanent

Temporary:

30 day expiration

Permanent:

never expires

---

# IMPLEMENTATION ORDER

1.

Schemas

↓

2.

Database

↓

3.

Pinecone Integration

↓

4.

Memory Services

↓

5.

Retrieval Nodes

↓

6.

Memory Analysis

↓

7.

Memory Creation

↓

8.

Frontend

↓

9.

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

apps/api/

app/api/memory.py

app/services/memory_service.py

app/services/pinecone_service.py

app/schemas/memory.py

app/models/memory.py

---

apps/orchestrator/

nodes/retrieve_memory.py

nodes/analyze_memory.py

nodes/create_memory.py

nodes/store_memory.py

state/memory_state.py

---

apps/web/

src/app/memory/page.tsx

src/components/memory/MemoryPanel.tsx

src/components/memory/MemoryCard.tsx

src/components/memory/MemorySources.tsx

src/components/memory/PreferenceInsights.tsx

src/components/memory/MemoryUsed.tsx

src/lib/memory.ts

---

# INSTALLATION

Backend:

pip install pinecone-client google-generativeai

Do not introduce additional vector databases.

Use Pinecone only. Uses Gemini models for embeddings (e.g. text-embedding-004).

---

# ENVIRONMENT VARIABLES

PINECONE_API_KEY=

PINECONE_INDEX=

GROQ_API_KEY=

GEMINI_API_KEY=

Existing variables remain unchanged.

---

# DATABASE CHANGES

Create:

memory_items

Fields:

id

memory_type

source_id

source_type

summary

metadata

scope

is_active

created_at

expires_at

---

Valid memory_type:

decision

comparison

evidence

visual

preference

---

Valid scope:

temporary

permanent

---

# PINECONE STORAGE

Store:

{
"id":"",

"summary":"",

"memory_type":"",

"confidence":0,

"created_at":"",

"metadata":{}
}

Do not store:

raw decisions

raw comparisons

raw evidence

raw visuals

Only summaries are embedded.

---

# MEMORY CREATION

Trigger:

Research completion

Automatically create memory.

No user action required.

Initial scope:

temporary

---

User saves research

↓

promote memory

↓

permanent

---

# MEMORY RETRIEVAL POLICY

Memory retrieval does NOT run for every request.

Rules:

Question

↓

Embedding (Gemini API)

↓

Vector Search

↓

Similarity Threshold (> 0.80)

↓

Pass threshold?

YES

↓

Retrieve -> analyze_memory

NO

↓

Skip memory (Short-circuit, skip analyze_memory)

---

# MEMORY RETRIEVAL LIMIT

Return:

maximum 5 memories

Ranking priority:

1 Semantic Similarity

2 Confidence

3 Recency

4 Memory Weight

---

# MEMORY WEIGHTS

Decision

1.0

---

Comparison

0.9

---

Evidence

0.7

---

Visual

0.5

---

Preference

1.1

Preference memories rank highest.

---

# GRAPH CHANGES

Modify existing decision graph.

New flow:

START

↓

decompose_question

↓

retrieve_memory (Short-circuits if no matches)

↓

analyze_memory (Skipped if retrieve_memory returns empty)

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

*Note: create_memory and store_memory are removed from the synchronous graph flow. They will be triggered as a FastAPI BackgroundTask immediately after the graph completes to ensure blazing fast response times for the user.*

---

# NODE REQUIREMENTS

retrieve_memory

Input:

question

Process:

embedding

↓

pinecone search

↓

top 5 memories

Output:

memory candidates

No LLM.

---

analyze_memory

Input:

retrieved memories

Output:

memory context

preference insights

consistency insights

Use LLM.

Purpose:

Convert raw memories into useful context.

---

create_memory

Input:

decision

comparison

evidence

visuals

Output:

memory summary

Use LLM.

Summary should be optimized for retrieval.

Not human readability.

---

store_memory

Input:

memory summary

Output:

database

*

pinecone

Deterministic.

No LLM.

---

# MEMORY ANALYSIS OUTPUT

{
"preferences":[],

"historical_patterns":[],

"related_decisions":[],

"consistency_warnings":[]
}

---

# PREFERENCE LEARNING

Atlas must never silently create preferences.

Atlas may suggest:

{
"type":"preference_candidate",

"value":"LangGraph",

"reason":"Repeated selection"
}

User decides.

---

# MEMORY INJECTION

Memory must NOT go directly into decision generation.

Required flow:

retrieve_memory

↓

analyze_memory

↓

decision_generation

Decision generation consumes analyzed memory.

Not raw memory.

---

# API CONTRACTS

GET /memory

Response:

{
"memories":[]
}

---

GET /memory/{id}

Response:

{
"memory":{}
}

---

POST /memory/promote

Request:

{
"memory_id":""
}

Response:

{
"promoted":true
}

Converts:

temporary

↓

permanent

---

# FRONTEND FLOW

Research Page

↓

Decision

↓

Evidence

↓

Visuals

↓

Memory Used

User must see:

which memories influenced decision

---

# MEMORY USED COMPONENT

Display:

Using Memory

Decision #12

Comparison #4

Preference #2

---

# TRANSPARENCY REQUIREMENT

Atlas must explain:

why memory was retrieved

Example:

Previously preferred deterministic workflows.

Previously selected LangGraph.

Previous comparison found reliability important.

Users should understand memory influence.

---

# MEMORY PAGE

Route:

/memory

Display:

Temporary Memories

Permanent Memories

Preference Suggestions

Memory Sources

---

# MEMORY AGING

Temporary memories:

30 day TTL

Expired memories:

inactive

Not retrieved

---

Permanent memories:

never expire

---

# VALIDATION RULES

Maximum memories retrieved:

5

---

Duplicate memory ids:

reject

---

Invalid memory types:

reject

---

Empty summaries:

reject

---

# PERFORMANCE TARGETS

Memory retrieval:

<1 second

---

Pinecone search:

<500ms

---

Research generation:

<30 seconds

---

Memory promotion:

<1 second

---

# TEST CASES

Research completed

↓

memory created

---

Memory embedded

↓

pinecone entry exists

---

Relevant question

↓

memory retrieved

---

Irrelevant question

↓

memory skipped

---

Memory promotion

↓

scope permanent

---

Expired memory

↓

not retrieved

---

Preference suggestion

↓

visible

---

Memory transparency

↓

displayed

---

# NON GOALS

Do NOT implement:

Outcome Tracking

Memory Editing

Memory Sharing

Cross-user memory

Knowledge Graph

Redis

WebSockets

Agent Collaboration

Memory Deletion UI

Memory Versioning

---

# DONE CONDITION

Feature complete only if:

Memory created automatically

Memory embedded in Pinecone

Memory retrieved when relevant

Memory analyzed before use

Memory influences decisions

Memory transparency visible

Temporary/permanent memory works

Preference suggestions work

Features F-001 through F-004 continue working
