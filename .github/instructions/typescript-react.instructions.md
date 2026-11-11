---
applyTo: "**/*.{ts,tsx}"
description: "Guidelines for TypeScript and React frontend development"
---

# TypeScript and React Instructions

You are an experienced TypeScript and React developer focused on maintainable, production-quality frontend code.

## General rules
- Prefer simple, explicit, strongly typed solutions.
- Keep changes minimal and consistent with the existing frontend architecture.
- Do not introduce new libraries, frameworks, or architectural patterns unless clearly justified.
- Preserve the existing project structure, naming, and conventions unless explicitly asked to change them.
- If the project is based on a template, follow the template conventions consistently.

## Project structure
When working on a React frontend, follow the existing project structure:

- `src/api` – API communication, API clients, shared API types, and error mapping
- `src/assets` – static assets
- `src/components` – reusable UI components
  - `src/components/common` – shared/common reusable components
  - `src/components/data` – data-related presentation components
- `src/context` – React context providers and related types
- `src/hooks` – custom React hooks
- `src/layout` – application layout components
- `src/pages` – page-level components and route targets
- `src/utils` – utility/helper functions
- `src/App.tsx` – root application component
- `src/main.tsx` – application entry point
- `src/index.css` – global styles

Do not move files between layers unless explicitly requested.

## API layer conventions
- Keep all API communication inside `src/api`.
- API clients, API-specific types, and error mapping should stay in the `api` layer.
- Reuse existing API helpers and error mapping patterns before introducing new ones.
- Keep request/response transformation logic close to the API layer when appropriate.

## Component conventions
- Prefer functional React components.
- Keep components focused on one responsibility.
- Put shared reusable UI into `src/components/common`.
- Put domain/data-oriented UI components into `src/components/data` when consistent with the project structure.
- Avoid overly large components; extract smaller components when it improves clarity.

## Context and hooks conventions
- Keep React context definitions and related types in `src/context`.
- Keep reusable logic in custom hooks under `src/hooks`.
- Prefer hooks for reusable stateful logic instead of duplicating logic across components.
- Follow existing project conventions for auth, API error handling, and shared state.

## Page conventions
- Put route-level views in `src/pages`.
- Pages should orchestrate layout and feature composition, not contain excessive low-level UI logic.
- Keep business/UI flow clear and predictable.

## TypeScript conventions
- Prefer strong typing over `any`.
- Use explicit types when inference is not clear enough.
- Keep interfaces and types focused and readable.
- Reuse existing shared types before creating new duplicates.
- Avoid unsafe casts unless there is no better option.

## React conventions
- Prefer clear props and predictable data flow.
- Move non-UI logic out of components when it improves readability.
- Avoid deeply nested JSX when it can be simplified.
- Follow existing patterns for hooks, context, forms, and data fetching.
- Handle loading, empty, and error states explicitly.
- Avoid unnecessary re-renders and unnecessary derived state.

## Styling conventions
- Follow the existing styling approach used in the project.
- If Tailwind CSS is already used, stay consistent with that approach.
- Prefer reusable styling patterns over duplicated class lists when appropriate.
- Do not introduce a new styling solution unless explicitly requested.

## Error handling
- Use the existing API error mapping approach.
- Do not silently swallow frontend errors.
- Display user-facing errors consistently with the project style.
- Keep internal details out of user-facing messages.

## Testing
- Follow the project’s existing testing approach if tests are present.
- Add or update tests when behavior changes and when it is reasonable.
- Prefer testing user-visible behavior over implementation details.

## Output
- Return compilable TypeScript/TSX when generating full code.
- Include imports when generating full files.
- Prefer the smallest safe change that solves the problem.
- Respect the existing structure, naming, and template conventions.