# F-008 — CORRECTIVE MEMORY RETRIEVAL (CORRECTIVE RAG)

# EXECUTION SPEC

# TARGET: CODING AGENT

Status: READY FOR IMPLEMENTATION

Priority: P1

Depends On:

* F-001 Research Engine
* F-005 Research Memory System
* F-007 Memory Dashboard
* P-001B Observability

---

# FEATURE GOAL

Current Atlas memory retrieval works as:

Query

↓

Pinecone Retrieval

↓

Top K Memories

↓

Inject Into Context

↓

Research

↓

Decision

---

Problem:

Similarity does not guarantee relevance.

Example:

User Query:

"Should I use Rust for a high-frequency trading system?"

Retrieved Memory:

"User preferred LangGraph over CrewAI."

Similarity may be acceptable.

Actual usefulness is near zero.

---

Current Atlas may inject irrelevant memories.

This creates:

Context Pollution

↓

Reduced Decision Quality

↓

Lower Confidence

---

Corrective RAG solves this.

---

# OBJECTIVE

Introduce a memory relevance evaluation layer.

Atlas must:

Retrieve Memories

↓

Evaluate Relevance

↓

Rank Memories

↓

Inject Best Memories

↓

Generate Research

---

Only memory retrieval changes.

Research pipeline remains unchanged.

---

# PRODUCT PRINCIPLE

Atlas should use:

Relevant Memory

not

Available Memory

---

# SUCCESS CRITERIA

Atlas:

✓ Retrieves memories

✓ Evaluates relevance

✓ Filters low-value memories

✓ Prioritizes high-value memories

✓ Preserves pinned memories

✓ Improves context quality

✓ Falls back safely if evaluator fails

---

# ARCHITECTURE OVERVIEW

CURRENT

Query

↓

Retrieve Memories

↓

Inject

↓

Research

---

NEW

Query

↓

Retrieve Memories

↓

Memory Relevance Evaluator

↓

Weighted Memory Selection

↓

Inject

↓

Research

---

# LANGGRAPH CHANGES

Add new node:

memory_relevance_evaluator

---

Updated flow:

retrieve_memories

↓

memory_relevance_evaluator

↓

memory_analysis

↓

research

---

Only one new node.

No graph redesign.

---

# MEMORY RETRIEVAL STRATEGY

Current:

Top K retrieval.

Keep existing Pinecone retrieval.

---

Retrieve:

Top 5 Memories

Only.

---

Reason:

Balances:

Quality

Latency

Cost

---

# MEMORY PRIORITY ORDER

When retrieved:

Priority Ranking:

1. Pinned Memories

2. Preference Memories

3. Decision Memories

4. Comparison Memories

5. Evidence Memories

---

Priority influences ranking.

Priority does not override relevance evaluation.

Except for pinned memories.

---

# PINNED MEMORY RULE

Pinned memories always survive.

Never filtered.

Never rejected.

Always included.

Reason:

User explicitly promoted them.

User intent must override algorithmic filtering.

---

# MEMORY RELEVANCE EVALUATION

New service:

services/memory_relevance_service.py

---

Input:

User Query

Memory

Memory Metadata

---

Output:

MemoryRelevanceResult

---

Schema:

class MemoryRelevanceResult(BaseModel):
memory_id: str
relevance_score: float
reasoning: str

---

Range:

0.0 → 1.0

---

# EVALUATION STRATEGY

Hybrid Evaluation

---

Stage 1

Rule-Based Filter

Use:

Pinecone Similarity

Memory Type

Pinned Status

---

Discard obviously weak memories.

---

Stage 2

LLM Evaluation

Evaluate:

Query

*

Memory

↓

Relevance Score

↓

Reasoning

---

Only Top 5 memories reach evaluation.

---

# EVALUATOR MODEL

Use dedicated evaluator.

Do NOT use primary research model.

---

Purpose:

Relevance Classification

not

Decision Generation

---

Evaluator responsibilities:

Determine:

Does this memory meaningfully help answer the query?

---

Return:

Relevance Score

Reasoning

---

# EVALUATION PROMPT

Goal:

Determine whether memory is useful.

---

Evaluator considers:

Topical Relevance

Decision Relevance

User Preference Relevance

Contextual Importance

---

Ignore:

Superficial keyword overlap.

---

Output:

Score

Reasoning

Only.

---

# WEIGHTED CONTEXT STRATEGY

Selected Approach:

Weighted Context

---

Do NOT hard reject memories.

Except extremely low-value memories.

---

Final Context:

Ordered by relevance.

Highest first.

---

Example:

Memory A

Score: 0.93

---

Memory B

Score: 0.81

---

Memory C

Score: 0.42

---

Injection order:

A

↓

B

↓

C

---

# MEMORY CONTEXT FORMAT

Inject:

Memory Summary

Memory Type

Relevance Score

Reasoning

---

Example:

Memory:
User strongly prefers open-source solutions.

Type:
Preference

Relevance:
0.92

Reason:
Directly influences technology selection decisions.

---

This gives the research model richer context.

---

# FAILURE STRATEGY

Critical Requirement.

---

If evaluator fails:

Atlas must continue.

---

Fallback:

Current Retrieval Logic

↓

Inject Retrieved Memories

↓

Research

---

Corrective RAG must improve reliability.

Never reduce reliability.

---

# MEMORY DASHBOARD INTEGRATION

Memory Dashboard already exists.

---

Add:

Relevance Score Display

---

Research Results

Comparison Results

Display:

Memories Used

↓

Relevance Score

↓

Reasoning

---

Example:

Memories Used

Preference:
Open-source preference

Relevance: 0.91

Reason:
Directly impacts technology recommendation.

---

# DATABASE CHANGES

No new tables.

No schema changes.

No persistence.

---

Reason:

Relevance is query-dependent.

Relevance should not be stored.

---

# API CHANGES

No new endpoints.

No API contract changes.

All behavior remains internal.

---

# FRONTEND CHANGES

Research Results Page

Update:

Memory Influence Panel

---

Display:

Memory Name

Memory Type

Relevance Score

Reasoning

---

Comparison Page

Same behavior.

---

# OBSERVABILITY

No new analytics tables.

No new metrics.

No dashboard changes.

---

Structured logs only.

Log:

memory_evaluated

memory_relevance_score

memory_evaluator_failure

---

No aggregation required.

---

# PERFORMANCE REQUIREMENTS

Maximum Additional Latency:

< 1.5 seconds

Target:

< 1 second

---

Evaluation must remain lightweight.

---

# TESTING

Memory Retrieval

Top 5 Retrieval

Pinned Memory Survival

Priority Ordering

LLM Evaluation

Weighted Ranking

Failure Fallback

Research Integration

Comparison Integration

Memory Dashboard Display

---

# NON-GOALS

Do NOT implement:

Self-RAG

Recursive Retrieval

Reflection Loops

GraphRAG

Knowledge Graph

Agent Debate

Multi-Agent Retrieval

Evidence Evaluation

Visual Evaluation

Outcome Tracking

GitHub MCP

---

# DONE CONDITION

Feature complete only when:

✓ Memory relevance evaluation exists

✓ Top 5 memories evaluated

✓ Pinned memories always survive

✓ Weighted ranking implemented

✓ Dedicated evaluator model used

✓ Relevance reasoning generated

✓ Dashboard shows relevance information

✓ Research quality improves

✓ Failure fallback works

✓ Existing APIs unchanged

✓ Existing Atlas features remain functional

Success Metric:

Atlas uses fewer irrelevant memories, produces cleaner context, and generates more focused decisions without increasing user-facing complexity.
