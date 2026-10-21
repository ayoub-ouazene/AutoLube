# LubriStock Frontend — Project Context

This file is the pinned context for every prompt. Read it before doing anything.
Do not modify it unless the human explicitly asks.

## What we are building

LubriStock is a **retailer** of automotive oils and lubricants in Algeria.
The frontend is a customer-facing e-commerce site plus a small admin dasboard section.

We are a retailer, not a manufacturer. We sell many brands (Castrol, Total,
Elf, Motul, Febi, etc.), not one. Think of the model of AutoDoc, Oscaro, or
Jumia — a product catalog with filters and search — not a single-brand
manufacturer site like Motul or Liqui-Moly.

## Tech stack

- Next.js 16 (App Router) with TypeScript
- React 19
- Tailwind CSS v4 (imported via `@import "tailwindcss"` in globals.css)
- No component libraries (no shadcn, no MUI, no Chakra)
- No state management libraries (no Redux, no Zustand) unless we explicitly ask later
- Lucide React for icons is allowed

## Language

The UI is **French**. All user-visible strings are in French, including
buttons, labels, error messages, and headings. Code identifiers, comments, and
file names stay in English.

## Backend

Base URL read from `process.env.NEXT_PUBLIC_API_URL`.
In development: `http://127.0.0.1:8000/api/v1`

Endpoints already available:

- `GET /products` — list with filters, pagination
  Query params: `category` (multi), `brand` (multi), `min_price`, `max_price`,
  `size_min`, `size_max`, `q`, `sort` (random | price_asc | price_desc),
  `page`, `page_size`
- `GET /products/{category}/{id}` — single product
- `POST /chat/session` — create chat session
- `POST /chat/session/{id}/message` — send message, returns { reply, products }
- `POST /orders` — create order, returns { order_id, total, items, whatsapp_url }
- `POST /admin/login` — returns { access_token, token_type, expires_in }
- Admin endpoints under `/admin/*` require `Authorization: Bearer <token>`

## Product shape (returned by /products and inside chat replies)

```ts
{
  category: "engine_oil" | "gearbox_oil" | "oil_filter" | "additional";
  id: number;
  brand: string;
  name: string;                 // e.g. "Castrol 5w-30 5L"
  specification: string;        // OEM / API spec codes, comma-separated
  viscosity: string | null;     // e.g. "5w-30"
  size: string | null;          // e.g. "5L", "1L", "1 pc"
  price: number;                // in DA
  in_stock: boolean;
  image_front_url: string | null;
  image_back_url: string | null;
}
```

There is no `quantity` field exposed to the customer. That is admin-only.

## Design system

See DESIGN_SYSTEM.md for the full reference. Summary:

- **Brand color**: orange `#FF5500` (hover `#E04B00`) — CTAs, active
  states, badges. Use sparingly.
- **Dark carbon**: `#121315` — headers, footers, hero backgrounds,
  primary text.
- **Page background**: `#F7F8FA`.
- **Surfaces**: `#FFFFFF` — cards, modals, inputs.
- **Borders**: `#E2E8F0`.
- **Text**: `#121315` main, `#5A5E66` muted, `#FFFFFF` inverse.
- **Typography**: system stack (no web fonts). Tailwind default sizes.
- **`.heading-brand` utility**: italic + 800 + uppercase + tracking
  -0.02em. Hero + logo-adjacent branding ONLY. Do NOT apply to all
  h1/h2/h3 — reading becomes fatiguing.
- **Radius**: Tailwind defaults (`rounded`, `rounded-md`, `rounded-lg`).
- **Shadows**: `shadow-sm` cards, `shadow-xl` modals/drawers. Not every
  element.
- **Blur**: allowed on modal/drawer backdrops.

Brand name: **LubriStock** (exact spelling). Instagram: @lubristock.

Logo: `public/LubriStock.jpg`. Navbar uses it with `alt='LubriStock'`.

Never display the old name 'AutoLube' in customer-facing UI.

## File conventions

- Path alias `@/*` maps to `src/*` (already configured in tsconfig)
- API client lives in `src/lib/api.ts`
- Shared types live in `src/lib/types.ts`
- Layout components live in `src/components/layout/`
- Feature components live in `src/components/<feature>/`
- Pages live in `src/app/<route>/page.tsx`
- Server Components by default. Add `"use client"` only when the file uses
  state, effects, or browser APIs.

## What not to touch unless explicitly asked

- `next.config.ts`
- `tsconfig.json`
- `postcss.config.mjs`
- `eslint.config.mjs`
- `package.json` (do not add dependencies without asking)
- `.env.local` (the human manages this)
- Any file outside the ones listed in the current step prompt

## Working style

Each task is a numbered step. Do only what the step says. Do not refactor
previous steps. Do not add features that weren't asked for. When in doubt,
leave a `// TODO:` comment rather than inventing.

<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->
