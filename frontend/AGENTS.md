# AutoLube Frontend — Project Context

This file is the pinned context for every prompt. Read it before doing anything.
Do not modify it unless the human explicitly asks.

## What we are building

AutoLube is a **retailer** of automotive oils and lubricants in Algeria.
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

### Tone

Neutral, commercial, dense. A real shop's website, not a marketing landing page.

### Color

- Background: `white` (light mode only for now)
- Primary text: `neutral-900`
- Secondary text: `neutral-600`, `neutral-500`
- Borders: `neutral-200` (1px solid)
- Muted backgrounds: `neutral-50`, `neutral-100`
- No accent color yet. When we add one, it will be used only on primary
  buttons and important badges. Until then, buttons are `neutral-900` bg
  with white text.

### Typography

- System stack via Tailwind defaults (Inter-like). No custom font files.
- Hierarchy through size and weight, not color:
  - Page titles: `text-2xl font-semibold`
  - Section headings: `text-lg font-medium`
  - Body: `text-sm` or `text-base`
  - Small labels: `text-xs uppercase tracking-wide text-neutral-500`

### Layout

- Horizontal container: `max-w-7xl mx-auto px-4` (or `px-6` on wider screens)
- Real content density — tight spacing, information-rich cards
- Product grids: 2 cols mobile, 3–4 cols tablet, 4–5 cols desktop
- Whitespace is used to separate sections, not to pad everything

### Components

- Product card: bordered box, image on top, brand + name + spec + price below,
  small "Rupture" badge when `in_stock` is false
- Buttons: rectangular, small radius (`rounded-md`), no shadows
- Inputs: `border border-neutral-300 rounded-md`, focus ring in `neutral-900`
- Badges: `text-xs px-2 py-0.5 border border-neutral-200 rounded`

### Anti-generic rules (hard constraints)

Do NOT produce any of the following:

- Purple/blue/pink gradients anywhere, on any element
- Glassmorphism (`backdrop-blur` on cards)
- Large drop shadows (`shadow-2xl`, colored shadows)
- Rounded-3xl corners on cards or containers
- Decorative SVG blobs, floating orbs, glowing shapes
- Full-viewport centered heroes with one headline and one button
- Emoji used as icons or in headings
- Placeholder copy like "Empower your journey", "Unlock efficiency"
- Everything centered — use grids, sidebars, two-column layouts
- Testimonial sections with circular avatars and star ratings
- Scroll-triggered animations on every element
- Any layout that could be swapped with a SaaS landing page without anyone noticing

If you're unsure, favor a layout where **the products or the content are the
visual interest**, not the design chrome around them.

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