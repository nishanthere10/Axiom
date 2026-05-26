# EXECUTION SPEC

# F-003 — Evidence Grounded Research

# TARGET: Coding Agent

Status: READY FOR IMPLEMENTATION

---

# READ FIRST

Implement exactly this feature.

Do NOT:

* redesign architecture
* introduce queues
* add vector DB
* add MCP
* add workers
* add auth
* add WebSockets
* add observability
* add RAG

If blocked:
implement simplest working version.

Previous features must remain functional.

---

# FEATURE GOAL

Upgrade Atlas research quality.

Research must no longer generate decisions from model knowledge alone.

All decisions must be grounded using external evidence.

New flow:

Question

↓

Collect Evidence

↓

Extract Claims

↓

Score Evidence

↓

Generate Decision

↓

Attach Evidence

↓

Persist

---

# PRODUCT RULES

Evidence sources:

Official

*

Community

Priority:

Official > Community

---

Community allowed:

GitHub Discussions

Reddit

Hacker News

StackOverflow

Dev.to

Reject:

Medium

Random SEO sites

---

Evidence count:

Top 5 maximum

---

Freshness:

Prefer latest

Do not exclude old sources.

Freshness affects ranking.

---

Evidence disagreement:

Detect

↓

Explain

↓

Reduce confidence

↓

Recommend contexts

Never ask user to resolve.

---

Evidence storage:

Store:

title

url

claim

trust_score

timestamp

Do NOT store:

raw html

markdown

chunks

---

Evidence scope:

Reusable across sessions

Cache TTL:

24 hours

User may refresh manually.

---

# IMPLEMENTATION ORDER

1.

Schemas

↓

2.

Evidence Cache

↓

3.

Search Integration

↓

4.

Evidence Extraction

↓

5.

LangGraph

↓

6.

Decision Generation

↓

7.

Frontend

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

apps/api/

app/services/evidence_service.py

app/services/search_provider.py

app/schemas/evidence.py

---

apps/orchestrator/

nodes/canonicalize_topic.py

nodes/generate_queries.py

nodes/collect_and_score_evidence.py

---

apps/web/

src/components/EvidenceCard.tsx

src/components/EvidenceConsensus.tsx

src/components/SourceList.tsx

src/components/RefreshEvidence.tsx

---

# FILES TO MODIFY

apps/orchestrator/

graph/decision_graph.py

nodes/generate.py

nodes/confidence.py

nodes/format.py

---

apps/api/

research.py

---

# ENVIRONMENT VARIABLES

Backend:

TAVILY_API_KEY=

GROQ_API_KEY=

Do not expose to frontend.

---

# INSTALLATION

pip install tavily-python

pip install tiktoken

---

# DATABASE CHANGES

Modify existing:

decision_documents

Add:

evidence JSONB

consensus TEXT

evidence_generated_at TIMESTAMP

No new tables.

---

# API CONTRACT

Keep existing.

POST /research

Request:

{
"question":"..."
}

Response:

{
"session_id":"",

"document":{}
}

Do not create evidence routes.

Research owns evidence.

---

POST /research/refresh-evidence

Request:

{
"session_id":""
}

Response:

{
"refreshed":true
}

Bypass cache.

---

# GRAPH FLOW

START

↓

decompose_question

↓

canonicalize_topic

↓

generate_queries

↓

collect_and_score_evidence

↓

generate_decision

↓

build_confidence

↓

format_document

↓

END

No additional graphs.

Extend existing graph.

---

# NODE REQUIREMENTS

generate_queries

Input:

question

Output:

3–5 search queries

Example:

[
"langgraph production",

"crewai scalability"
]

No web calls.

---

collect_and_score_evidence

Input:

queries

Flow:

Tavily Search (with raw_content=True)

↓

LLM Extract & Score Claims

Output:

[
{
"title":"",

"url":"",

"claim":"",

"trust_score":0
}
]

Rules:

Top 5 only. Skip Firecrawl. Prefer official. Score simultaneously.

---

generate_decision

Modify existing.

Input:

question

*

evidence

Output:

decision

Decision MUST cite evidence.

---

build_confidence

Modify existing.

Add:

evidence_strength

consensus

Rules:

Weak consensus

↓

lower confidence

Strong consensus

↓

increase confidence

---

format_document

Modify.

Add:

evidence

consensus

Return final schema.

---

# CACHE STRATEGY

Cache key:

canonical_topic_slug

Never cache raw question.

Example:

LangGraph vs CrewAI

CrewAI or LangGraph

↓

same cache

TTL:

24h

Cache stores:

evidence only

No decision caching.

---

# DECISION DOCUMENT OUTPUT

Add:

{
"evidence":[

{

"title":"",

"url":"",

"claim":"",

"trust_score":0

}

],

"consensus":""

}

Keep existing fields.

No markdown.

Store JSON.

---

# FRONTEND FLOW

/research

submit

↓

show research phases

↓

render decision

↓

render evidence

↓

render consensus

↓

allow refresh

---

# UI ORDER

Decision

↓

Evidence Cards

↓

Consensus

↓

Refresh Evidence

Do not reorder.

---

# CONSENSUS VALUES

Strong Consensus

Weak Consensus

Conflicting Evidence

Insufficient Evidence

Display visually.

---

# VALIDATION

Question:

required

10–1000 chars

Reject empty.

---

Evidence:

max 5

Reject duplicates.

---

# PERFORMANCE TARGETS

cache hit:

<2 sec

fresh research:

<20 sec

refresh:

<25 sec

---

# TEST CASES

Question

↓

decision generated

---

Evidence attached

↓

visible

---

Duplicate URLs

↓

deduped

---

Conflict

↓

confidence lowered

---

Refresh

↓

new evidence

---

Cache hit

↓

reuse evidence

---

# NON GOALS

Do NOT implement:

RAG

embeddings

vector search

memory

evaluation

queues

workers

provider abstraction

provider swapping

multi-provider search

agent collaboration

---

# DONE CONDITION

Feature complete only if:

Decision generated

Evidence attached

Consensus visible

Refresh works

Cache works

Feature 1 works

Feature 2 works
