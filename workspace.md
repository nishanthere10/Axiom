# F-010 — WORKSPACE SYSTEM

# EXECUTION SPEC

# TARGET: CODING AGENT

Status: READY FOR IMPLEMENTATION

Priority: P0

Depends On:

* F-001 Research Engine
* F-005 Memory System
* F-007 Memory Dashboard
* F-008 Corrective RAG
* F-009 GitHub Context Provider
* P-001B Observability

---

# FEATURE GOAL

Atlas currently organizes everything around:

User

---

Current ownership model:

User

↓

Research Sessions

Memories

Comparisons

Exports

GitHub Repositories

---

Problem:

As Atlas grows:

GitHub

Notion

Jira

Slack

Comparisons

Memory

Research

all become mixed together.

---

Atlas cannot determine:

Which project?

Which repository?

Which decision context?

Which engineering environment?

---

Result:

Context pollution.

Memory pollution.

Repository pollution.

Decision pollution.

---

# OBJECTIVE

Introduce Workspaces as the primary organizational entity.

Everything belongs to a workspace.

---

Future hierarchy:

User

↓

Global Memory

↓

Workspace

↓

Research

↓

Comparisons

↓

Memory

↓

GitHub

↓

Notion

↓

Jira

↓

Slack

↓

Exports

---

Workspace becomes the primary context boundary.

---

# PRODUCT PRINCIPLE

Atlas is not organized around users.

Atlas is organized around engineering initiatives.

---

Examples:

Atlas

Startup

Open Source

College Project

Client Project

---

Each becomes its own workspace.

---

# SUCCESS CRITERIA

Atlas can:

✓ Create workspaces

✓ Select active workspace

✓ Isolate memories

✓ Isolate repositories

✓ Isolate research

✓ Isolate exports

✓ Isolate MCP connections

✓ Support multiple workspaces

✓ Maintain global user preferences

---

# DATABASE CHANGES

## TABLE

workspaces

Columns:

id

user_id

name

description

icon

created_at

updated_at

---

Example:

Atlas

Startup

College

Open Source

---

# DEFAULT WORKSPACE

Every user receives:

My Workspace

automatically.

---

Existing users:

Migration creates:

My Workspace

automatically.

---

No manual setup required.

---

# GLOBAL MEMORY VS WORKSPACE MEMORY

Atlas introduces two memory scopes.

---

Scope 1

Global Memory

User-level.

---

Examples:

Prefers Open Source

Prefers Cost Optimization

Prefers TypeScript

---

Applies everywhere.

---

Scope 2

Workspace Memory

Workspace-level.

---

Examples:

Atlas uses Pinecone

Atlas uses Railway

Atlas prefers LangGraph

---

Only applies inside workspace.

---

# MEMORY ARCHITECTURE

Current:

memory.user_id

---

Future:

memory.workspace_id

memory.scope

---

Scopes:

GLOBAL

WORKSPACE

---

Retrieval:

Global Memory

*

Workspace Memory

↓

Corrective RAG

↓

Research

---

# RESEARCH CHANGES

Current:

Research

↓

User

---

Future:

Research

↓

Workspace

---

Add:

workspace_id

to:

research_sessions

---

Every research belongs to a workspace.

---

# COMPARISON CHANGES

Current:

comparison.user_id

---

Future:

comparison.workspace_id

---

All comparisons become workspace-specific.

---

# EXPORT CHANGES

Current:

export.user_id

---

Future:

export.workspace_id

---

Exports retain workspace metadata.

---

Example:

Workspace

Atlas

Decision

Should we migrate to Kubernetes?

---

# GITHUB MCP CHANGES

Current:

github_repositories.user_id

---

Future:

github_repositories.workspace_id

---

Repository belongs to:

One Workspace Only.

---

Rule:

A repository may not belong to multiple workspaces.

---

# MCP ARCHITECTURE

All future MCPs attach to workspace.

---

Future:

Workspace

↓

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

Never attach integrations directly to user.

---

# PINECONE ARCHITECTURE

Current:

Namespace

user_id

---

Future:

Namespace

workspace_id

---

Examples:

workspace_atlas

workspace_startup

workspace_college

---

Reason:

Workspace isolation.

---

# VECTOR STORAGE MIGRATION

Existing vectors:

user namespace

↓

workspace namespace

---

Migration required.

---

All future embeddings stored under workspace namespace.

---

# RESEARCH EXECUTION FLOW

Current:

User Query

↓

Memory

↓

GitHub

↓

Research

---

Future:

Workspace

↓

Global Memory

↓

Workspace Memory

↓

GitHub Context

↓

Evidence

↓

Research

↓

Decision

---

Workspace becomes retrieval root.

---

# ACTIVE WORKSPACE

User always has:

active_workspace_id

---

Research executes against active workspace.

---

Workspace switching supported.

---

# FRONTEND

Create:

/workspaces

---

Components:

WorkspaceSelector

WorkspaceCard

WorkspaceCreateModal

WorkspaceSettings

WorkspaceDeleteDialog

---

# WORKSPACE SWITCHER

Visible globally.

---

Example:

Atlas ▼

Startup

College

Open Source

---

Switching workspace updates:

Research

Memory

Comparisons

Repositories

Exports

---

# WORKSPACE CREATION

Fields:

Name

Description

Icon

---

Workspace created instantly.

---

# WORKSPACE SETTINGS

Editable:

Name

Description

Icon

---

Display:

Repository Count

Memory Count

Research Count

Comparison Count

---

# WORKSPACE DASHBOARD

Display:

Recent Research

Recent Decisions

Connected Repositories

Connected Integrations

Memory Statistics

---

# DELETION RULES

Workspace deletion allowed.

---

Requirements:

Confirmation Required

Repository Detachment

Memory Removal

Research Removal

Comparison Removal

Export Removal

Vector Cleanup

---

Hard delete.

---

# AUTHORIZATION

Users only access:

Their workspaces.

---

Validate:

workspace.user_id

==

authenticated_user_id

---

Every request validated.

---

# API CHANGES

POST

/workspaces

---

GET

/workspaces

---

GET

/workspaces/{id}

---

PATCH

/workspaces/{id}

---

DELETE

/workspaces/{id}

---

POST

/workspaces/select

---

# OBSERVABILITY

Track:

workspace_created

workspace_deleted

workspace_switched

workspace_research_count

workspace_memory_count

workspace_repository_count

---

Add to Admin Dashboard.

---

# MIGRATION STRATEGY

Critical.

---

For existing users:

Create:

My Workspace

---

Move:

Research

Memory

Comparisons

Repositories

Exports

↓

My Workspace

---

No user action required.

---

# FUTURE MCP COMPATIBILITY

Required.

---

Future providers:

GitHub

Notion

Jira

Slack

Linear

Google Drive

Confluence

---

Must attach to workspace.

---

No redesign permitted.

---

# TEAM WORKSPACE READINESS

Do NOT implement team workspaces.

---

However:

Workspace model must support future:

workspace_members

workspace_roles

workspace_permissions

---

without redesign.

---

# TESTING

Workspace Creation

Workspace Selection

Workspace Switching

Workspace Isolation

Global Memory Retrieval

Workspace Memory Retrieval

GitHub Isolation

Research Isolation

Comparison Isolation

Export Isolation

Pinecone Namespace Isolation

Authorization

Migration

Workspace Deletion

---

# NON-GOALS

Do NOT implement:

Team Workspaces

Invitations

Workspace Roles

Workspace Permissions

Workspace Sharing

Organization Accounts

Billing

Multi-Tenant Teams

Workspace Templates

---

# DONE CONDITION

Feature complete only when:

✓ Workspace entity exists

✓ Default workspace created

✓ Global memory supported

✓ Workspace memory supported

✓ Research isolated

✓ Comparisons isolated

✓ Exports isolated

✓ GitHub isolated

✓ Pinecone isolated

✓ Workspace switching works

✓ Migration completed

✓ Future MCPs supported

✓ Existing functionality preserved

Success Metric:

Atlas evolves from a user-centric research tool into a workspace-centric engineering decision operating system capable of supporting repositories, memory, MCPs, research, and future team collaboration without architectural redesign.
