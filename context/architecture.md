# Architecture Context

## 1. System Stack

| Layer          | Technology          | Specific Version/Config                        | Role                                           |
| -------------- | ------------------- | ---------------------------------------------- | ---------------------------------------------- |
| **Frontend**   | Next.js             | App Router, React 19 (Server Components)       | User interface, routing, and client-side logic |
| **Backend**    | FastAPI             | Async Python 3.12+                             | Core REST API and system orchestration         |
| **Agent Core** | LangGraph           | Python SDK                                     | Workflow orchestration and agentic execution   |
| **LLM Layer**  | Groq                | Groq Python SDK (e.g., Llama 3)                | Fast LLM inference layer for reasoning         |
| **Auth**       | Clerk               | Next.js App Router Integration                 | User authentication and session management     |
| **Relational DB**| Supabase          | PostgreSQL + Prisma ORM                        | Relational data (users, sessions, artifacts)   |
| **Task Queue** | Celery + Redis      | Celery 5+, Redis 7                             | Background task processing and message broker  |
| **Vector DB**  | Pinecone            | Serverless Index                               | Semantic search and evidence retrieval         |
| **Hosting**    | Vercel + Railway    | Serverless (Vercel) + Containers (Railway)     | Deployment environments                        |

## 2. High-Level Data Flow

1. **Client Request**: User submits a research query via the Next.js UI.
2. **Frontend to Backend**: Next.js Server Action authenticates the user via Clerk, then calls the FastAPI endpoint (`POST /api/v1/research`).
3. **Task Orchestration**: FastAPI validates the request, creates a "pending" session in Supabase, queues a Celery task, and returns a `task_id` to the client.
4. **Agent Execution**: Celery worker picks up the task and initializes a LangGraph state machine.
5. **Research Cycle**:
   - **Decompose**: LangGraph uses Groq to break down the query.
   - **Retrieve**: LangGraph queries Pinecone for context and evidence.
   - **Evaluate**: Contradictions are analyzed.
   - **Generate**: A structured decision matrix is generated via Groq.
6. **Persistence**: The Celery worker updates the session in Supabase with the final research artifact and confidence score.
7. **Client Update**: Next.js polls (or uses Server-Sent Events/WebSockets) FastAPI for task status and fetches the completed artifact from Supabase.

## 3. Storage Model

### 3.1 Relational Database (Supabase + Prisma)
- **`users`**: User metadata (syncs with Clerk webhooks).
- **`sessions`**: `id`, `user_id`, `status` (pending/completed/failed), `created_at`.
- **`queries`**: Original natural language input.
- **`research_artifacts`**: The final structured JSON or Markdown document containing context, tradeoffs, alternatives, evidence, and rationale.

### 3.2 Vector Database (Pinecone)
- **Index**: `atlas-research-v1`
- **Namespaces**: Partitioned by source type or public/private (if applicable).
- **Metadata**: Every vector must include `source_url`, `timestamp`, and `confidence_score`.

### 3.3 Message Broker & Cache (Redis)
- **Celery Broker**: Routes tasks to workers.
- **Celery Backend**: Stores task execution status (pending, started, success, failure) and temporary results.

## 4. Authentication & Access Model

- **Identity Provider**: Clerk handles all authentication via JWTs.
- **Backend Auth**: FastAPI must verify the Clerk JWT on every protected route using `clerk-backend-api` or a custom JWT verifier.
- **Authorization**: Row-Level Security (RLS) is enabled in Supabase. A user can *only* read, update, or delete records where `user_id == auth.uid()`.
- **System Constraints**: Multi-user collaboration is strictly out of scope for V1. There are no "teams" or "organizations" tables.

## 5. Architectural Invariants

1. **No Synchronous LLM Calls in API**: The FastAPI event loop must NEVER be blocked by LLM inference. All Groq/LangGraph execution must occur within Celery workers.
2. **Evidence over Authority**: The system must never claim absolute certainty (FR-5). All claims must be linked to retrieved evidence.
3. **Stateless API**: FastAPI routes must remain stateless. All state is in Supabase or Redis.
4. **Secure by Default**: All DB queries must be scoped to the authenticated user. No exposed endpoints without JWT verification.
