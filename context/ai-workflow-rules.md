# AI Workflow Rules

## 1. Absolute Directives

This is a spec-driven workflow. As an AI assistant, you must adhere to the following rules absolutely. These context files (`architecture.md`, `code-standards.md`, `ui-context.md`, `prd.md`) form the ground truth. **You must follow them every time you write even a single line of code.**

- **Do not infer architecture**: If a technology or pattern is not listed in `architecture.md`, do not use it.
- **Do not invent features**: If a behavior is not in `prd.md`, ask the user before implementing it.
- **Do not guess dependencies**: Ask for permission before running `npm install` or `pip install` for major new dependencies not established in the stack.

## 2. Implementation Loop

For every coding task, follow this rigorous loop:

1. **Understand Context**: Read the relevant sections of `architecture.md`, `code-standards.md`, and `ui-context.md` before making a plan.
2. **Narrow Scope**: Work on exactly one feature unit at a time. If the user asks for a full end-to-end feature, break it down (e.g., "First, let's create the DB schema. Next, the FastAPI route. Finally, the Next.js UI.").
3. **Write Code**: Implement following `code-standards.md`.
4. **Verify**: Ensure the code builds (`npm run build` or `pytest`), type checks (`tsc` or `mypy`), and lints correctly.
5. **Update Context**: If you made a structural decision, an API schema decision, or added a new standard, you MUST document it in the context files immediately.

## 3. When to Stop and Ask

You must stop execution and explicitly ask the user for direction if:
- An instruction contradicts the PRD (e.g., user asks for a real-time collaboration feature when it is out of scope).
- You are about to make a significant schema change to the database.
- You encounter an ambiguous technical requirement that impacts the system boundaries.
- You realize a task is too large to complete in one step and needs to be split.

## 4. Documentation Sync

The context files are living documents. Every time you write code that changes how the system works conceptually, you update the docs.
- Added a new Prisma model? Update the Storage Model in `architecture.md`.
- Added a new UI pattern (like a specific type of modal)? Update `ui-context.md`.
- Changed the way errors are handled? Update `code-standards.md`.
