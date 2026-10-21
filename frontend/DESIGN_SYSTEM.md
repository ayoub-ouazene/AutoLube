# LubriStock Design System

## Colors

| Token | Hex | Usage |
|---|---|---|
| brand-orange | #FF5500 | CTAs, active states, badges, price highlights |
| brand-orange-hover | #E04B00 | Orange button hover |
| brand-dark | #121315 | Headers, footers, hero bg, primary text |
| brand-dark-light | #1E2024 | Dark panels |
| brand-bg | #F7F8FA | Page background |
| brand-surface | #FFFFFF | Cards, modals, forms |
| brand-border | #E2E8F0 | Dividers, borders |
| brand-text | #121315 | Body text |
| brand-text-muted | #5A5E66 | Secondary text |
| brand-text-inverse | #FFFFFF | Text on dark/orange |

Tailwind: `bg-brand-orange`, `text-brand-dark`, `border-brand-border`.

## Typography

- Body: system stack (Segoe UI / SF Pro / Roboto).
- Headings: same family, normal weight. `.heading-brand` opt-in only
  (hero + logo wordmark).
- Sizes: Tailwind defaults.

## Spacing

Tailwind defaults. Page padding `px-4` mobile / `px-6` desktop.
Container `max-w-7xl`.

## Radius

`rounded` (buttons), `rounded-md` (cards, inputs), `rounded-lg` (modals).

## Shadows

`shadow-sm` cards, `shadow-xl` modals/drawers. Not every element.

## Blur

`backdrop-blur-sm` on modal/drawer backdrops only.

## Buttons

- Primary: `bg-brand-orange text-white hover:bg-brand-orange-hover`
- Secondary: `border border-brand-border text-brand-text hover:bg-brand-bg`
- Danger: `border border-red-300 text-red-700 hover:bg-red-50`

## Inputs

`border border-brand-border rounded px-3 py-2 text-sm
focus:outline-none focus:border-brand-dark`

## Cards

`bg-brand-surface border border-brand-border rounded-md p-4` or `p-6`.

## Header / Footer

`bg-brand-dark text-brand-text-inverse`, links `hover:text-brand-orange`.

## Icons

`lucide-react`, 16-20 inline, 20-24 standalone.

## What NOT to do

- No web fonts.
- No italic/uppercase on section headings.
- No neon colors outside palette.
- No gradients beyond hero.
- No animations > 200ms.
- No `rounded-full` on cards (pills/badges only).

## Brand

- Logo: `public/LubriStock.jpg`
- Instagram: @lubristock
- Delivery: 58 wilayas (Algeria)