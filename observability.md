# P-001B — OBSERVABILITY & PRODUCT INTELLIGENCE

# EXECUTION SPEC

# TARGET: CODING AGENT

Status: READY FOR IMPLEMENTATION

Priority: P1

Depends On:

* F-001 Research Engine
* F-002 Comparison Engine
* F-003 Evidence Grounding
* F-004 Visual Intelligence
* F-005 Memory System
* P-001A Launch Protection
* F-006 Decision Export

---

# OBJECTIVE

Atlas is becoming a real product.

We need visibility into:

* System Health
* User Behavior
* Feature Usage
* Performance
* Memory Effectiveness
* Provider Reliability

This feature introduces the observability layer.

This is NOT a user-facing feature.

This is an operator-facing feature.

---

# SUCCESS CRITERIA

Atlas operators can answer:

* How many researches were performed?
* How many comparisons were performed?
* How often is memory retrieved?
* How often is memory useful?
* What is average research latency?
* Which providers fail most?
* How often do fallbacks occur?
* Which features are used most?
* Which topics are researched most?

without manually inspecting logs.

---

# PRODUCT PRINCIPLE

Every major Atlas action must be measurable.

If it cannot be measured, it cannot be improved.

---

# ARCHITECTURE OVERVIEW

Current:

Research

↓

Decision

↓

Response

---

Future:

Research

↓

Metrics Collection

↓

Decision

↓

Analytics Storage

↓

Response

---

Observability must be passive.

It must never alter business logic.

---

# NEW BACKEND MODULE

Create:

services/metrics/

metrics_service.py

analytics_service.py

provider_metrics_service.py

latency_service.py

---

Responsibilities:

* collect metrics
* aggregate metrics
* query metrics
* calculate health indicators

---

# DATABASE CHANGES

## TABLE 1

analytics_daily

Purpose:

Daily aggregated product metrics.

Columns:

id

metric_date

research_count

comparison_count

memory_retrieval_count

memory_hit_count

memory_hit_rate

export_count

avg_research_latency_ms

avg_comparison_latency_ms

avg_memory_latency_ms

provider_fallback_count

failed_memory_jobs

created_at

updated_at

---

One row per day.

---

## TABLE 2

analytics_provider_metrics

Purpose:

Provider health tracking.

Columns:

id

metric_date

provider_name

request_count

success_count

failure_count

avg_latency_ms

fallback_count

created_at

updated_at

---

Example Providers:

Groq

Gemini

Tavily

Pinecone

---

## TABLE 3

analytics_topic_metrics

Purpose:

Track popular research themes.

Columns:

id

metric_date

topic_label

research_count

created_at

---

IMPORTANT

Store topic labels only.

Never store raw user queries.

---

Example:

AI Agents

Vector Databases

System Design

LangGraph

Open Source

---

# METRICS TO TRACK

## Research Metrics

research_count

avg_research_latency_ms

avg_confidence_score

avg_evidence_count

avg_sources_used

---

## Comparison Metrics

comparison_count

avg_comparison_latency_ms

avg_comparison_confidence

---

## Memory Metrics

memory_retrieval_count

memory_hit_count

memory_hit_rate

avg_memories_retrieved

memory_search_latency_ms

retrieved_memory_count

used_memory_count

---

IMPORTANT

Store both:

retrieved_memory_count

used_memory_count

for future Corrective RAG adoption.

---

## Export Metrics

export_count

pdf_export_count

markdown_export_count

adr_export_count

avg_export_latency_ms

---

## Provider Metrics

provider_used

provider_latency

provider_failure

fallback_triggered

---

Track:

Groq

Gemini

Tavily

Pinecone

Future providers automatically supported.

---

# INSTRUMENTATION

## Research Flow

Current:

POST /research

↓

LangGraph

↓

Response

---

Add:

research_started

research_completed

research_duration

confidence_score

evidence_count

sources_used

---

Metrics must be emitted automatically.

---

## Comparison Flow

Track:

comparison_started

comparison_completed

comparison_duration

comparison_confidence

---

## Memory Flow

Track:

memory_retrieval_started

memory_retrieval_completed

memory_search_latency

retrieved_memory_count

used_memory_count

---

This prepares Atlas for Corrective RAG.

---

## Export Flow

Track:

export_requested

export_completed

export_type

export_duration

---

# STRUCTURED LOGGING

Upgrade all logs.

Current:

logger.info("research completed")

---

Future:

logger.info(
"research_completed",
extra={
"user_id": user_id,
"latency_ms": latency,
"confidence": confidence,
"evidence_count": evidence_count
}
)

---

Required Log Events:

research_started

research_completed

comparison_started

comparison_completed

memory_retrieved

memory_search

memory_hit

memory_miss

provider_fallback

provider_failure

export_requested

export_completed

health_check_failed

---

Do NOT log:

User research content

Raw prompts

Memory content

API keys

Tokens

PII

---

# ADMIN METRICS API

Create:

routes/admin_metrics.py

Admin only.

Authentication required.

---

## Endpoint

GET /admin/metrics/overview

Returns:

{
"research_count": 0,
"comparison_count": 0,
"memory_hit_rate": 0.0,
"avg_latency_ms": 0,
"fallback_count": 0
}

---

## Endpoint

GET /admin/metrics/research

Returns research analytics.

---

## Endpoint

GET /admin/metrics/memory

Returns memory analytics.

---

## Endpoint

GET /admin/metrics/providers

Returns provider analytics.

---

## Endpoint

GET /admin/metrics/topics

Returns top research categories.

---

# TOPIC CLASSIFICATION

Purpose:

Track what users research.

---

Implementation:

Simple lightweight classifier.

Input:

Research query

↓

LLM Classification

↓

Topic Label

↓

Store Metric

---

Store:

AI Agents

Vector Databases

Cloud

Backend

Frontend

System Design

Architecture

Open Source

Other

---

Never store raw queries.

---

# FRONTEND ADMIN DASHBOARD

Create:

app/admin/metrics/page.tsx

---

Sections:

Overview

Research Analytics

Memory Analytics

Provider Analytics

Topic Analytics

---

No advanced charts required.

Simple cards and tables.

---

# OVERVIEW PANEL

Display:

Research Count

Comparison Count

Memory Hit Rate

Average Latency

Fallback Count

Exports Generated

---

# MEMORY PANEL

Display:

Memory Retrieval Count

Memory Hit Rate

Average Memories Retrieved

Memory Search Latency

Retrieved vs Used Ratio

---

This panel becomes extremely valuable after Corrective RAG.

---

# PROVIDER PANEL

Display:

Provider

Requests

Failures

Fallbacks

Average Latency

---

# TOPIC PANEL

Display:

Top 10 Topics

Research Count

Percentage Usage

---

# TESTING

Research Metrics Tracking

Comparison Metrics Tracking

Memory Metrics Tracking

Provider Metrics Tracking

Export Metrics Tracking

Admin Metrics Authorization

Topic Classification

Analytics Aggregation

Dashboard APIs

---

# NON-GOALS

Do NOT implement:

Datadog

Prometheus

Grafana

OpenTelemetry

Distributed Tracing

Real-Time Monitoring

Alerting Systems

User Analytics Dashboard

Event-Level Analytics

A/B Testing

Corrective RAG

Self-RAG

GitHub MCP

---

# DONE CONDITION

Feature complete only when:

✓ Daily metrics aggregate correctly

✓ Provider metrics aggregate correctly

✓ Topic metrics aggregate correctly

✓ Research metrics tracked

✓ Comparison metrics tracked

✓ Memory metrics tracked

✓ Export metrics tracked

✓ Structured logging implemented

✓ Admin dashboard functional

✓ Metrics APIs secured

✓ Existing features remain unchanged

Success Metric:

Atlas operators can understand product usage, performance, memory effectiveness, provider reliability, and emerging user interests without inspecting raw logs.
