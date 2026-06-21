# F-009 — GITHUB CONTEXT PROVIDER (GITHUB MCP)

# EXECUTION SPEC

# TARGET: CODING AGENT

Status: READY FOR IMPLEMENTATION

Priority: P1

Depends On:

* F-001 Research Engine
* F-005 Memory System
* F-007 Memory Dashboard
* F-008 Corrective Memory Retrieval
* P-001A Launch Protection
* P-001B Observability

---

# FEATURE GOAL

Atlas currently makes decisions using:

* User Query
* Research Evidence
* Historical Memory

Atlas lacks:

Repository Context

As a result:

Atlas understands technology.

Atlas does NOT understand the user's actual engineering environment.

---

Example:

Question:

Should we migrate from Railway to Kubernetes?

Current Atlas:

Generic recommendation.

---

Future Atlas:

Knows:

Current Deployment: Railway

Current Users: Small Scale

Current Architecture: Monolith

Current Infrastructure Complexity: Low

Recommendation:

Do NOT migrate yet.

---

This is the goal.

Atlas becomes:

Repository-Aware Decision Intelligence.

---

# PRODUCT PRINCIPLE

Atlas is NOT a GitHub Chat Tool.

Atlas is NOT a Code Search Tool.

Atlas is NOT a Repository Q&A Tool.

---

Atlas uses GitHub context to improve engineering decisions.

---

# SUCCESS CRITERIA

Atlas can:

✓ Connect GitHub

✓ Access public repositories

✓ Access private repositories

✓ Sync repository context

✓ Generate repository summaries

✓ Embed repository knowledge

✓ Retrieve repository context

✓ Use repository context during research

✓ Explain repository context used

✓ Support multiple repositories

---

# ARCHITECTURAL PRINCIPLE

GitHub must never be a runtime dependency.

---

Bad:

Research

↓

GitHub API

↓

Decision

---

Good:

GitHub

↓

Sync

↓

Summarize

↓

Embed

↓

Store

↓

Research Retrieval

↓

Decision

---

Research flow never directly calls GitHub.

---

# AUTHENTICATION

Use:

Clerk GitHub OAuth

---

Do NOT implement standalone GitHub OAuth.

---

Leverage Clerk.

---

Flow:

User

↓

Connect GitHub

↓

Clerk OAuth

↓

GitHub Access Granted

↓

Store Connection

---

# PERMISSIONS

Read-only access only.

---

Required Scopes:

Repository Metadata

Repository Contents

Issues

Pull Requests

---

Forbidden:

Write Access

PR Creation

Commit Access

Repository Modification

Repository Deletion

---

# DATABASE CHANGES

## TABLE

github_connections

Columns:

id

user_id

github_user_id

github_username

encrypted_access_token

created_at

updated_at

---

## TABLE

github_repositories

Columns:

id

user_id

repository_id

repository_name

repository_owner

repository_url

is_private

is_active

last_synced_at

created_at

updated_at

---

## TABLE

github_sync_jobs

Columns:

id

user_id

repository_id

status

error_message

started_at

completed_at

created_at

---

Statuses:

queued

running

completed

failed

---

# CONTEXT PROVIDER ARCHITECTURE

Create generic provider architecture.

---

Create:

services/context_providers/

base_provider.py

github_provider.py

---

Interface:

class ContextProvider:

```
sync()

retrieve()

summarize()
```

---

Future Providers:

NotionProvider

JiraProvider

SlackProvider

LinearProvider

---

Atlas should be designed for provider expansion.

---

# REPOSITORY SELECTION

Users explicitly choose repositories.

---

Never auto-index all repositories.

---

Flow:

Connect GitHub

↓

List Repositories

↓

User Selects

↓

Repositories Activated

↓

Sync Starts

---

# MULTI-REPOSITORY SUPPORT

Supported.

---

Users may connect:

atlas-backend

atlas-frontend

atlas-infra

atlas-docs

---

All supported.

---

Repository metadata stored.

---

# INITIAL REPOSITORY INGESTION

DO NOT INDEX SOURCE CODE.

---

V1 indexes:

README

Repository Description

Repository Metadata

Documentation Files

Issue Summaries

Pull Request Summaries

---

Not Indexed:

Source Code

Controllers

Services

Functions

Tests

Generated Files

---

Reason:

Repository understanding.

Not code understanding.

---

# REPOSITORY PROFILING

Create:

services/github/repository_profile_service.py

---

Generate:

RepositoryProfile

---

Schema:

{
"repository_name": "",
"language": "",
"framework": "",
"database": "",
"vector_database": "",
"deployment_platform": "",
"architecture_style": "",
"summary": ""
}

---

Example:

FastAPI

Postgres

Pinecone

Railway

Monolith

---

Store profile in Postgres.

---

# REPOSITORY SUMMARIZATION

Create:

services/github/repository_summary_service.py

---

Input:

README

Docs

Issues

PR Summaries

---

Output:

Repository Summary

---

Purpose:

Condense repository knowledge.

Reduce retrieval cost.

Control context window size.

---

# EMBEDDING STRATEGY

Embed:

Repository Summary

Documentation

Issue Summaries

PR Summaries

---

Use existing embedding pipeline.

---

Store:

Pinecone

---

Namespace:

user_id

---

Metadata:

{
"provider": "github",
"repository": "atlas-backend",
"document_type": "readme"
}

---

Do NOT create repository-specific Pinecone indexes.

---

# REFRESH STRATEGY

Manual Sync

Only.

---

No webhooks.

No automatic refresh.

No background polling.

---

User clicks:

Sync Repository

↓

Refresh

↓

Re-embed changed content

---

# CHANGE DETECTION

Use:

Repository SHA

or

Document Hash

---

Only changed content reprocessed.

---

Avoid full re-indexing.

---

# LANGGRAPH CHANGES

Add node:

retrieve_github_context

---

Current:

memory

↓

evidence

↓

research

---

Future:

memory

↓

github_context

↓

evidence

↓

research

---

One new node only.

---

# GITHUB CONTEXT RETRIEVAL

Input:

User Query

Repository Scope

---

Retrieve:

Top Relevant GitHub Chunks

---

Maximum:

5 chunks

---

Never inject entire summaries.

---

Context window must remain controlled.

---

# RESEARCH INTEGRATION

Example:

Question:

Should we move to Kubernetes?

---

GitHub Retrieval:

Current Platform: Railway

Current Architecture: Monolith

Infrastructure Documentation

---

Research receives:

Memory

*

GitHub Context

*

Evidence

---

Decision becomes repository-aware.

---

# CONTEXT TRANSPARENCY

Research results must show:

Repository Context Used

---

Example:

Repository Context Used

atlas-backend README

Infrastructure Documentation

PR #142 Summary

Issue #88 Summary

---

Transparency required.

---

# REPOSITORY MEMORY

Repository profiles become long-term memory.

---

Example:

Atlas Backend

↓

FastAPI

↓

Postgres

↓

Railway

---

Stored as:

Repository Memory

---

Retrievable by Corrective RAG.

---

Purpose:

Prevent rediscovery.

---

# FRONTEND

Create:

/settings/integrations/github

---

Components:

GitHubConnectionCard

RepositorySelector

RepositorySyncButton

RepositoryStatusPanel

---

Research Results:

Add:

Repository Context Used

---

# API CONTRACTS

POST

/github/connect

---

GET

/github/repositories

---

POST

/github/repositories/select

---

POST

/github/repositories/{id}/sync

---

DELETE

/github/disconnect

---

GET

/github/status

---

# ERROR HANDLING

GitHub Connection Failure

↓

Graceful Error

---

Repository Sync Failure

↓

Sync Job Failed

↓

Retry Allowed

---

GitHub Downtime

↓

No Effect On Research

---

Research uses stored context only.

---

# SECURITY

Access Tokens:

Encrypted At Rest

---

Repository Isolation:

Strict User Isolation

---

Users may only access:

Their Repositories

Their Context

Their Embeddings

---

No Cross-Tenant Access.

---

# OBSERVABILITY

Track:

github_connections

repository_count

repository_sync_count

sync_failures

context_retrieval_count

---

Add to Admin Dashboard.

---

# TESTING

GitHub OAuth Flow

Repository Selection

Repository Sync

Repository Summarization

Embedding Pipeline

Pinecone Storage

Context Retrieval

LangGraph Integration

Repository Transparency

Permission Isolation

Token Encryption

Failure Recovery

---

# NON-GOALS

Do NOT Implement:

Code Indexing

Code Search

Code Generation

Repository Chat

Pull Request Creation

Issue Creation

GitHub Actions

Webhook Infrastructure

Automatic Sync

Repository Editing

Multi-Agent Review

---

# FUTURE EXTENSIBILITY

This architecture must support:

GitHub

↓

Notion

↓

Jira

↓

Slack

↓

Linear

---

Without LangGraph redesign.

---

Future:

retrieve_context

↓

GitHub

↓

Notion

↓

Jira

↓

Memory

↓

Research

---

Provider architecture must remain generic.

---

# DONE CONDITION

Feature complete only when:

✓ GitHub OAuth works through Clerk

✓ Public repositories supported

✓ Private repositories supported

✓ Multiple repositories supported

✓ Repository summaries generated

✓ Repository context embedded

✓ Pinecone storage operational

✓ GitHub retrieval node operational

✓ Research uses repository context

✓ Repository context transparency displayed

✓ Repository memory created

✓ User isolation enforced

✓ Existing Atlas functionality preserved

Success Metric:

Atlas recommendations become aware of the user's actual repository architecture, technology stack, infrastructure, and engineering context without requiring runtime GitHub access.
