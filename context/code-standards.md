# Code Standards

## 1. General Principles

- **Small, Verifiable Increments**: Never write more than one logical component or route before verifying it works.
- **Single Responsibility**: A function does one thing. A component renders one thing. A module handles one domain.
- **Fail Fast**: Validate early, throw specific errors, and do not swallow exceptions without logging them.

## 2. TypeScript & Next.js (Frontend)

- **Framework**: Next.js App Router (`app/` directory).
- **Server vs Client**: Default to React Server Components (RSC). Use `'use client'` *only* at the leaf nodes of the component tree when interactivity (hooks, event listeners) is strictly required.
- **Typing**: Strict mode is enforced. `any` is strictly forbidden. Use `unknown` and type narrowing if necessary.
- **Validation**: Use **Zod** for all external data validation (API responses, form inputs).
- **Imports**: Use absolute imports with the `@/` alias (e.g., `import { Button } from "@/components/ui/button"`).
- **Data Fetching**: Prefer Server Actions for mutations and Server Components for data fetching. Do not use `useEffect` for data fetching unless absolutely necessary.

## 3. Python & FastAPI (Backend)

- **Typing**: Use strict type hints for all function arguments and return types. Run `mypy` or `pyright` to verify.
- **Validation**: Use **Pydantic v2** models for all incoming request bodies and outgoing responses.
- **Formatting & Linting**: Use **Ruff** for linting and formatting. Line length is 88 characters.
- **Async Execution**: Use `async def` for all FastAPI endpoints. Use `await` for I/O bound operations (DB, Redis, external APIs).
- **Celery Tasks**: Keep task functions small. The task should initialize the LangGraph execution, handle exceptions, and save the result to the DB.

## 4. API Design Standards

- **RESTful Patterns**: Use standard HTTP methods (`GET`, `POST`, `PATCH`, `DELETE`).
- **Standardized Error Responses**: All API errors must return a consistent JSON shape:
  ```json
  {
    "error": {
      "code": "RESOURCE_NOT_FOUND",
      "message": "The requested research session does not exist.",
      "details": {}
    }
  }
  ```
- **Authentication Header**: Pass the Clerk JWT in the `Authorization: Bearer <token>` header to the FastAPI backend.

## 5. File & Directory Organization

### Next.js (`my-app/`)
- `app/` — Route handlers, layouts, and pages.
- `components/ui/` — Generic, reusable `shadcn/ui` components.
- `components/features/` — Domain-specific components (e.g., `ResearchForm.tsx`, `DecisionMatrix.tsx`).
- `lib/` — Utility functions, Zod schemas, and API clients.
- `types/` — Shared TypeScript interfaces.

### FastAPI (`backend/`)
- `api/routes/` — FastAPI endpoint definitions.
- `core/` — Configuration, security, and global dependencies.
- `models/` — Pydantic schemas and database models.
- `services/` — Business logic (DB interactions).
- `agents/` — LangGraph definitions, Groq prompts, and vector store integrations.
- `workers/` — Celery task definitions.
