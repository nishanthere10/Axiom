# ROADMAP.md — Atlas Implementation Roadmap

**Status:** Ready for Execution

**Purpose**

This document translates the Atlas RFCs into an executable engineering roadmap.

The planning phase is complete.

From this point onward, Atlas evolves through incremental implementation.

This roadmap defines the execution order, implementation strategy, milestones, and Definition of Done for every phase.

---

# 1. Guiding Principles

Every implementation must follow these principles.

* Preserve existing engineering investment.
* Refactor instead of rewrite.
* Workspace First.
* Context Before Intelligence.
* Decisions over Conversations.
* Knowledge compounds automatically.
* Maintain backwards compatibility.
* Ship incrementally.
* Never build features without a product reason.

---

# 2. Execution Philosophy

Atlas will not be rebuilt.

Atlas will evolve.

The majority of the current backend remains.

Our objective is to reorganize engineering capabilities into a coherent Engineering Workspace.

Success is measured by product coherence, not lines of code changed.

---

# Phase 1 — Foundation

## Goal

Stabilize the platform before introducing the new product model.

### Backend

* Clerk JWT validation
* Authorization middleware
* Workspace ownership
* Role validation
* API security
* Rate limiting
* CORS cleanup

### Database

* Workspace validation
* Missing indexes
* Foreign key cleanup

### Frontend

* Authentication cleanup
* Session handling
* Error states

### Deliverable

A secure production-ready foundation.

---

# Phase 2 — Workspace Evolution

## Goal

Make Workspace the primary product object.

### Backend

Introduce:

WorkspaceService

Workspace APIs

Workspace summaries

Workspace statistics

### Frontend

Workspace Dashboard

Workspace Overview

Workspace Navigation

Workspace Search

### Deliverable

Workspace becomes the engineering home.

---

# Phase 3 — Initiative Domain

## Goal

Replace isolated Research Sessions with engineering Initiatives.

### Backend

Initiative model

Initiative APIs

Initiative lifecycle

Workspace ownership

Migration

### Frontend

Initiative List

Initiative Overview

Initiative Dashboard

### Migration

Automatically migrate existing research into:

General Initiative

No data loss.

### Deliverable

Engineering work becomes initiative-centric.

---

# Phase 4 — Exploration Engine

## Goal

Capture engineering thinking before research.

### Backend

Exploration model

Exploration service

Context storage

Question generation

### Frontend

Exploration editor

Problem statement

Constraints

Assumptions

Goals

### Deliverable

Every research begins with context.

---

# Phase 5 — Research Refactor

## Goal

Move Research inside the Initiative workflow.

### Backend

Refactor:

Research Service

Research APIs

Research ownership

Context Assembly

### Intelligence

Repository Intelligence

Knowledge Layer

Corrective RAG

Web Search

LLM

become one pipeline.

### Deliverable

Research becomes context-aware.

---

# Phase 6 — Decision System

## Goal

Transform decisions into first-class engineering assets.

### Backend

Decision lifecycle

Decision ownership

Decision retrieval

Decision summaries

### Frontend

Decision Timeline

Decision Detail

Decision Search

Decision Status

### Deliverable

Engineering decisions become reusable knowledge.

---

# Phase 7 — Knowledge Layer

## Goal

Expose accumulated engineering knowledge.

### Backend

Knowledge Service

Knowledge synthesis

Workspace summaries

Knowledge retrieval

### Frontend

Knowledge dashboard

Knowledge search

Workspace Intelligence

### Deliverable

Knowledge becomes visible.

---

# Phase 8 — Repository Intelligence

## Goal

Upgrade GitHub Context Provider into Repository Intelligence.

### Backend

Architecture summaries

Technology detection

Dependency analysis

Repository health

Repository profile

### Frontend

Repository Overview

Architecture View

Technology Stack

Repository Insights

### Deliverable

Repository becomes engineering context.

---

# Phase 9 — Product Polish

## Goal

Prepare Atlas for production.

### Tasks

Performance

Caching

Loading states

Error handling

Accessibility

Animations

Documentation

Developer Experience

### Deliverable

Production-quality experience.

---

# 3. Backend Checklist

Every phase should answer:

✓ Services updated

✓ APIs updated

✓ LangGraph updated

✓ Tests written

✓ Logging added

✓ Metrics validated

---

# 4. Frontend Checklist

Every phase should include:

✓ Responsive UI

✓ Loading states

✓ Empty states

✓ Error handling

✓ Accessibility

✓ Component reuse

✓ Design consistency

---

# 5. Database Checklist

Every migration must:

Preserve data.

Support rollback.

Maintain compatibility.

Avoid downtime.

---

# 6. AI Checklist

Every AI capability must:

Use Repository Intelligence.

Use Workspace Knowledge.

Use Corrective RAG.

Use previous Decisions.

Use current Exploration.

Never rely solely on the LLM.

---

# 7. Definition of Done

A sprint is complete only when:

Backend complete.

Frontend complete.

Tests passing.

Documentation updated.

Migration verified.

Performance acceptable.

No breaking changes.

---

# 8. Milestones

Milestone 1

Engineering Workspace

---

Milestone 2

Initiative-Centric Workflow

---

Milestone 3

Engineering Intelligence Platform

---

Milestone 4

Knowledge Workspace

---

Milestone 5

Production Launch

---

# 9. Success Criteria

Atlas succeeds when engineers naturally think:

Workspace

↓

Initiative

↓

Exploration

↓

Research

↓

Decision

↓

Knowledge

without needing to understand the underlying AI architecture.

The technology should disappear behind the workflow.

---

# 10. Future Roadmap

Future integrations:

GitHub

↓

Notion

↓

Linear

↓

Jira

↓

Slack

These systems provide additional engineering context.

They should never become the center of the product.

The Engineering Workspace remains the primary abstraction.

---

# Closing Statement

The planning phase of Atlas ends with this document.

RFC-001 defines the philosophy.

RFC-002 defines the evolution.

P-001 defines the user experience.

P-002 defines the intelligence platform.

ROADMAP.md defines execution.

From this point onward, every pull request, feature, migration, and architectural decision should move Atlas closer to becoming the Engineering Workspace where software teams think, research, decide, and preserve engineering knowledge.

Planning is complete.

The next phase is execution.
