# UI Context

## 1. Theme & Design Philosophy

Atlas Research is a dark-mode-first technical workspace tailored for software engineers. The UI should feel like a premium IDE or developer tool—dense but legible, heavily structured, and utilizing near-black backgrounds with subtle layered surfaces to establish hierarchy. Avoid overly playful or consumer-focused aesthetics.

## 2. Color System (Tailwind CSS Variables)

All components must use these CSS custom properties. **Do not use hardcoded hex values in component code.**

| Role | CSS Variable | Value | Usage Context |
|---|---|---|---|
| Page Background | `--background` | `0 0% 3.9%` (`#0a0a0a`) | Main app background |
| Surface | `--surface` | `0 0% 9%` (`#171717`) | Cards, sidebars, panels |
| Surface Hover | `--surface-hover` | `0 0% 14.9%` (`#262626`) | Interactive row/card hover |
| Primary Text | `--foreground` | `0 0% 98%` (`#fafafa`) | Headings, primary body text |
| Muted Text | `--muted-foreground` | `0 0% 63.9%` (`#a3a3a3`) | Secondary text, placeholders |
| Primary Accent | `--primary` | `217.2 91.2% 59.8%` (`#3b82f6`) | Primary buttons, active states, focus rings |
| Border | `--border` | `0 0% 14.9%` (`#262626`) | Dividers, card borders, inputs |
| Error State | `--destructive` | `0 62.8% 30.6%` (`#7f1d1d`) | Delete actions, error messages |
| Success State | `--success` | `142.1 76.2% 36.3%` (`#16a34a`) | Success indicators, high confidence scores |

*(Note: Values are in HSL format for Tailwind's native variable support).*

## 3. Typography

- **Primary UI Font**: Geist Sans (configured via `next/font/google`). Used for standard body text, buttons, and UI controls.
- **Display Headings Font**: Plus Jakarta Sans (configured via `next/font/google`). Used for high-impact page headings and hero titles.
- **Monospace Font**: Geist Mono. Used strictly for code snippets, IDs, technical terms, and structured matrix keys.

## 4. Spacing & Border Radius

- **Spacing**: Strictly adhere to Tailwind's default spacing scale (e.g., `p-4`, `gap-2`). Do not use arbitrary values like `p-[15px]`.
- **Border Radius**:
  - `rounded-sm` (2px): Interactive inline elements (checkboxes, tags).
  - `rounded-md` (6px): Buttons, inputs, small cards.
  - `rounded-lg` (8px): Main panels, modals, major layout boundaries.

## 5. Component Library & State

- **Library**: `shadcn/ui` built on top of Tailwind CSS and Radix UI primitives.
- **Installation**: Always use the CLI (`npx shadcn@latest add [component]`) to add components. Do not copy-paste or write standard UI components from scratch.
- **State Management**:
  - **Server State**: Managed by Next.js Server Components and Server Actions.
  - **Form State**: Managed via `react-hook-form` + `@hookform/resolvers/zod`.
  - **Global Client State**: Use Zustand *only if* prop drilling becomes unmanageable. Otherwise, rely on React Context for simple theme/auth state.

## 6. Layout Patterns & Interactions

- **Workspace Layout**: A fixed, full-viewport layout (`h-screen w-screen overflow-hidden`).
  - **Left Sidebar**: Collapsible. Contains session history and settings (`w-64`).
  - **Center Canvas**: Scrollable. The active research query interface and chat/generation logs.
  - **Right Panel**: Collapsible. Displays the Evidence Breakdown, Confidence Score, and Source citations (`w-80`).
- **Loading States**: Use animated skeletons (`animate-pulse`) that mimic the shape of the expected content. Avoid generic spinners for major layout shifts.
- **Feedback**: Use Toast notifications (`sonner` or `shadcn/ui` toast) for async action results (e.g., "Research session started", "Error fetching data").

## 7. Iconography

- **Library**: Lucide React.
- **Style**: Stroke-based icons only (stroke-width: 2).
- **Sizing**: `h-4 w-4` alongside text, `h-5 w-5` for standalone icon buttons.
