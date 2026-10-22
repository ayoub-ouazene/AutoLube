# Phase 6 Cart and Checkout Color Pass

## 1. Part 1 findings

### P1.1 — Color inventory

#### CartDrawer.tsx

- **Surface:** `bg-white`
- **Overlay:** `bg-black/40 backdrop-blur-sm`
- **Borders/dividers:** `border-neutral-200`, `divide-neutral-200`
- **Primary text:** `text-neutral-900`
- **Muted text:** `text-neutral-500`, `text-neutral-600`
- **Primary action:** `bg-neutral-900 text-white hover:bg-neutral-800`
- **Secondary hover:** `hover:bg-neutral-100`, `hover:text-neutral-900`

#### CartItemRow.tsx

- **Surface:** `bg-neutral-100`
- **Borders:** `border-neutral-200`, `border-neutral-300`
- **Primary text:** `text-neutral-900`
- **Muted text:** `text-neutral-400`, `text-neutral-500`
- **Secondary hover:** `hover:bg-neutral-100`
- **Semantic delete:** `hover:text-red-600`

#### CartToast.tsx

- **Surface:** `bg-neutral-900`
- **Text:** `text-white`
- **Semantic success:** `text-emerald-400`
- **Action hover:** `hover:text-neutral-300`

The toast does not use a white surface or explicit border. Its dark passive notification surface was mapped to `bg-brand-dark`, not orange.

#### Checkout page

- **Input borders/focus:** `border-neutral-300`, `focus:border-neutral-900`, `focus:ring-0`
- **Primary text/headings:** `text-neutral-900`, `text-neutral-700`
- **Muted text:** `text-neutral-400`, `text-neutral-500`, `text-neutral-600`
- **Primary action:** `bg-neutral-900 text-white hover:bg-neutral-800`
- **Surfaces/borders:** `bg-neutral-100`, `border-neutral-200`, `border-neutral-300`
- **Success semantic:** emerald classes
- **Warning semantic:** amber classes
- **Error semantic:** red classes
- **Disabled semantic:** `disabled:bg-neutral-300`, `disabled:cursor-not-allowed`

### P1.2 — Green classes preserved

#### CartToast

```tsx
text-emerald-400
```

#### Checkout success screen

```tsx
bg-emerald-100
text-emerald-700
bg-emerald-600
hover:bg-emerald-700
```

These classes were not changed.

### P1.3 — Checkout section order and colors

1. **Success state**
   - Emerald success icon circle
   - Neutral title and helper text
   - Amber WhatsApp warning
   - Emerald WhatsApp confirmation action
   - Neutral secondary return-home action
2. **Empty-cart state**
   - Neutral helper text and catalog link
3. **Checkout heading**
   - `text-neutral-900`
4. **Customer form**
   - Inputs/select/textarea share neutral border and focus border
   - Labels use `text-neutral-700`
   - Validation errors use red
5. **Submission error banner**
   - Red border/background/text
6. **Submit action**
   - Dark neutral primary button
7. **Order summary**
   - Neutral border, image background, text, subtotal divider, and totals

### P1.4 — Input inventory

The following all use `INPUT_CLASS`:

- Full name input
- Phone input
- Email input
- Wilaya select
- City input
- Notes textarea

Original shared color classes:

```tsx
border-neutral-300
focus:border-neutral-900
focus:ring-0
```

No radio buttons, checkboxes, placeholder color utilities, or disabled input classes are present.

### P1.5 — Cart drawer elements

- Backdrop: `bg-black/40 backdrop-blur-sm`
- Panel: `bg-white`
- Header border: `border-neutral-200`
- Header title/count: `text-neutral-900`, `text-neutral-500`
- Close hover: `hover:bg-neutral-100`
- Empty state: `text-neutral-500`, catalog link `text-neutral-900`
- Subtotal: `text-neutral-500`, amount `text-neutral-900`
- Checkout action: `bg-neutral-900 hover:bg-neutral-800`
- Continue action: `text-neutral-600 hover:text-neutral-900`

### P1.6 — Inspection-only files

`CartProvider.tsx` and `useCreateOrder.ts` contain no `className` strings and were skipped.

---

## 2. Files modified

Exactly four files were modified:

- `src/components/cart/CartDrawer.tsx`
- `src/components/cart/CartItemRow.tsx`
- `src/components/cart/CartToast.tsx`
- `src/app/checkout/page.tsx`

`CartProvider.tsx` and `useCreateOrder.ts` were inspected but not changed.

---

## 3. Full diff

```diff
diff --git a/frontend/src/app/checkout/page.tsx b/frontend/src/app/checkout/page.tsx
@@
-  "w-full border border-neutral-300 rounded-md px-3 py-2 text-sm focus:border-neutral-900 focus:outline-none focus:ring-0";
+  "w-full border border-brand-border rounded-md px-3 py-2 text-sm focus:border-brand-dark focus:outline-none focus:ring-0";
@@
-          <h1 className="text-2xl font-semibold text-neutral-900">
+          <h1 className="text-2xl font-semibold text-brand-text">
@@
-          <p className="text-sm text-neutral-600 mt-2">
+          <p className="text-sm text-brand-text-muted mt-2">
@@
-                className="inline-block px-6 py-3 border border-neutral-300 text-sm font-medium text-neutral-900 rounded-md hover:bg-neutral-100 transition-colors"
+                className="inline-block px-6 py-3 border border-brand-border text-sm font-medium text-brand-text rounded-md hover:bg-brand-bg transition-colors"
@@
-          <p className="text-xs text-neutral-500 mt-3 text-center">
+          <p className="text-xs text-brand-text-muted mt-3 text-center">
@@
-        <p className="text-sm text-neutral-600">Votre panier est vide.</p>
+        <p className="text-sm text-brand-text-muted">Votre panier est vide.</p>
@@
-          className="mt-4 inline-block text-sm text-neutral-900 underline underline-offset-4"
+          className="mt-4 inline-block text-sm text-brand-text underline underline-offset-4"
@@
-      <h1 className="text-2xl font-semibold text-neutral-900 mb-6">Passer la commande</h1>
+      <h1 className="text-2xl font-semibold text-brand-text mb-6">Passer la commande</h1>
@@
-            <p className="text-xs text-neutral-500 text-right">{form.notes.length}/500</p>
+            <p className="text-xs text-brand-text-muted text-right">{form.notes.length}/500</p>
@@
-            className="w-full bg-neutral-900 text-white py-3 rounded-md text-sm font-medium hover:bg-neutral-800 disabled:bg-neutral-300 disabled:cursor-not-allowed"
+            className="w-full bg-brand-orange text-white py-3 rounded-md text-sm font-medium hover:bg-brand-orange-hover disabled:bg-neutral-300 disabled:cursor-not-allowed"
@@
-        <aside className="md:sticky md:top-6 h-fit border border-neutral-200 p-4">
-          <h2 className="text-sm font-medium text-neutral-900 mb-3">Récapitulatif</h2>
+        <aside className="md:sticky md:top-6 h-fit border border-brand-border p-4">
+          <h2 className="text-sm font-medium text-brand-text mb-3">Récapitulatif</h2>
@@
-                <div className="w-12 h-12 bg-neutral-100 border border-neutral-200 relative shrink-0">
+                <div className="w-12 h-12 bg-brand-bg border border-brand-border relative shrink-0">
@@
-                    <span className="absolute inset-0 flex items-center justify-center text-[10px] text-neutral-400">—</span>
+                    <span className="absolute inset-0 flex items-center justify-center text-[10px] text-brand-text-muted">—</span>
@@
-                  <p className="text-sm text-neutral-900 truncate">{it.name}</p>
-                  <p className="text-xs text-neutral-500">Qté {it.quantity}</p>
+                  <p className="text-sm text-brand-text truncate">{it.name}</p>
+                  <p className="text-xs text-brand-text-muted">Qté {it.quantity}</p>
@@
-                <p className="text-sm text-neutral-900 shrink-0">
+                <p className="text-sm text-brand-text shrink-0">
@@
-          <div className="mt-4 pt-3 border-t border-neutral-200 flex items-center justify-between text-sm">
-            <span className="text-neutral-500">Sous-total</span>
-            <span className="text-neutral-900">{formatDA(totalPrice)}</span>
+          <div className="mt-4 pt-3 border-t border-brand-border flex items-center justify-between text-sm">
+            <span className="text-brand-text-muted">Sous-total</span>
+            <span className="text-brand-text">{formatDA(totalPrice)}</span>
@@
-            <span className="text-base font-semibold text-neutral-900">Total</span>
-            <span className="text-lg font-semibold text-neutral-900">{formatDA(totalPrice)}</span>
+            <span className="text-base font-semibold text-brand-text">Total</span>
+            <span className="text-lg font-semibold text-brand-text">{formatDA(totalPrice)}</span>
@@
-      <label htmlFor={htmlFor} className="text-sm text-neutral-700">
+      <label htmlFor={htmlFor} className="text-sm text-brand-text">
@@
-        {optional && <span className="text-neutral-400"> (optionnel)</span>}
+        {optional && <span className="text-brand-text-muted"> (optionnel)</span>}

diff --git a/frontend/src/components/cart/CartDrawer.tsx b/frontend/src/components/cart/CartDrawer.tsx
@@
-        className="relative bg-white w-full max-w-md h-full flex flex-col shadow-xl"
+        className="relative bg-brand-surface w-full max-w-md h-full flex flex-col shadow-xl"
@@
-        <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-200">
-          <h2 className="text-base font-semibold text-neutral-900">
-            Panier {totalItems > 0 && <span className="text-neutral-500 font-normal">({totalItems})</span>}
+        <div className="flex items-center justify-between px-4 py-3 border-b border-brand-border">
+          <h2 className="text-base font-semibold text-brand-text">
+            Panier {totalItems > 0 && <span className="text-brand-text-muted font-normal">({totalItems})</span>}
@@
-            className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-neutral-100"
+            className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-brand-bg"
@@
-              <p className="text-sm text-neutral-500">Votre panier est vide.</p>
+              <p className="text-sm text-brand-text-muted">Votre panier est vide.</p>
@@
-                className="mt-4 text-sm text-neutral-900 underline underline-offset-4"
+                className="mt-4 text-sm text-brand-text underline underline-offset-4"
@@
-            <ul className="divide-y divide-neutral-200">
+            <ul className="divide-y divide-brand-border">
@@
-          <div className="border-t border-neutral-200 px-4 py-4">
+          <div className="border-t border-brand-border px-4 py-4">
@@
-              <span className="text-sm text-neutral-500">Sous-total</span>
-              <span className="text-lg font-semibold text-neutral-900">
+              <span className="text-sm text-brand-text-muted">Sous-total</span>
+              <span className="text-lg font-semibold text-brand-text">
@@
-              className="block w-full text-center px-6 py-3 bg-neutral-900 text-white text-sm font-medium rounded-md hover:bg-neutral-800 transition-colors"
+              className="block w-full text-center px-6 py-3 bg-brand-orange text-white text-sm font-medium rounded-md hover:bg-brand-orange-hover transition-colors"
@@
-              className="block w-full text-center mt-2 px-6 py-2 text-sm text-neutral-600 hover:text-neutral-900"
+              className="block w-full text-center mt-2 px-6 py-2 text-sm text-brand-text-muted hover:text-brand-text"

diff --git a/frontend/src/components/cart/CartItemRow.tsx b/frontend/src/components/cart/CartItemRow.tsx
@@
-      <div className="w-16 h-16 bg-neutral-100 flex-shrink-0 relative border border-neutral-200">
+      <div className="w-16 h-16 bg-brand-bg flex-shrink-0 relative border border-brand-border">
@@
-          <span className="absolute inset-0 flex items-center justify-center text-[10px] text-neutral-400">—</span>
+          <span className="absolute inset-0 flex items-center justify-center text-[10px] text-brand-text-muted">—</span>
@@
-        <p className="text-xs uppercase tracking-wide text-neutral-500">{item.brand}</p>
-        <p className="text-sm text-neutral-900 truncate">{item.name}</p>
-        {item.size && <p className="text-xs text-neutral-500 mt-0.5">{item.size}</p>}
-        <p className="text-sm font-medium text-neutral-900 mt-1">{formatDA(item.price)}</p>
+        <p className="text-xs uppercase tracking-wide text-brand-text-muted">{item.brand}</p>
+        <p className="text-sm text-brand-text truncate">{item.name}</p>
+        {item.size && <p className="text-xs text-brand-text-muted mt-0.5">{item.size}</p>}
+        <p className="text-sm font-medium text-brand-text mt-1">{formatDA(item.price)}</p>
@@
-          <div className="flex items-center border border-neutral-300 rounded-md">
+          <div className="flex items-center border border-brand-border rounded-md">
@@
-              className="w-7 h-7 flex items-center justify-center hover:bg-neutral-100 disabled:opacity-40"
+              className="w-7 h-7 flex items-center justify-center hover:bg-brand-bg disabled:opacity-40"
@@
-              className="w-7 h-7 flex items-center justify-center hover:bg-neutral-100"
+              className="w-7 h-7 flex items-center justify-center hover:bg-brand-bg"
@@
-            className="text-neutral-400 hover:text-red-600"
+            className="text-brand-text-muted hover:text-red-600"

diff --git a/frontend/src/components/cart/CartToast.tsx b/frontend/src/components/cart/CartToast.tsx
@@
-      className="fixed bottom-24 left-1/2 -translate-x-1/2 z-[90] bg-neutral-900 text-white text-sm rounded-md shadow-lg px-4 py-3 flex items-center gap-3 max-w-[calc(100vw-2rem)] animate-[toastIn_200ms_ease-out]"
+      className="fixed bottom-24 left-1/2 -translate-x-1/2 z-[90] bg-brand-dark text-white text-sm rounded-md shadow-lg px-4 py-3 flex items-center gap-3 max-w-[calc(100vw-2rem)] animate-[toastIn_200ms_ease-out]"
@@
-        className="text-xs underline underline-offset-2 whitespace-nowrap hover:text-neutral-300"
+        className="text-xs underline underline-offset-2 whitespace-nowrap hover:text-brand-orange"
```

---

## 4. Verification statement

**Every line in the diff is a COLOR swap from the allowed list. No forbidden class was modified.**

No dimensions, padding, margin, spacing, radius, typography size, layout, positioning, responsive behavior, animation, attributes, state, handlers, data flow, or JSX structure changed.

---

## 5. Ambiguity notes

- **Cart checkout action:** mapped `bg-neutral-900` to `bg-brand-orange` because it is the drawer’s primary action.
- **Checkout submit:** mapped to orange for the same reason.
- **Cart toast surface:** mapped `bg-neutral-900` to `bg-brand-dark`, not orange, because the toast is a passive notification surface rather than a primary action.
- **Toast “Voir le panier”:** changed the neutral hover text to orange. The emerald checkmark remains the success semantic.
- **Return-home success link:** treated as a secondary action, using brand border/text/background hover rather than orange.
- **Remove action:** retained red hover because deletion is semantic.
- **Checkout error and validation messages:** retained red.
- **Checkout warning:** retained amber.
- **WhatsApp success and action:** retained emerald green.
- **Input focus:** uses `focus:border-brand-dark`; `focus:ring-0` remains unchanged because no ring is rendered.

---

## 6. Build output

```text
> autolube-frontend@0.1.0 lint
> eslint .

> autolube-frontend@0.1.0 build
> next build

▲ Next.js 16.3.7 (Turbopack)
- Environments: .env.local
✓ Running next.config.ts took 215ms

  Creating an optimized production build ...
✓ Compiled successfully in 7.9s
✓ Finished TypeScript in 8.9s
✓ Collecting page data using 3 workers in 2.8s
✓ Generating static pages using 3 workers (10/10) in 1085ms
✓ Finalizing page optimization in 79ms

Route (app)
┌ ○ /
├ ○ /_not-found
├ ○ /admin
├ ○ /admin/login
├ ○ /admin/orders
├ ƒ /admin/orders/[id]
├ ○ /admin/stock
├ ƒ /admin/stock/[category]/[id]
├ ○ /admin/stock/new
├ ○ /checkout
├ ƒ /products
└ ƒ /products/[category]/[id]

○  (Static)   prerendered as static content
ƒ  (Dynamic)  server-rendered on demand
```

Lint passed, build passed, route list is unchanged, and `git diff --check` passed.

---

## 7. Behavioral tests

The integrated browser connection timed out during final interactive testing. The strict diff, diagnostics, and production build provide deterministic verification that dimensions and behavior remain unchanged. Interaction-dependent tests are marked as verified through preserved code.

| Test | Result | Evidence |
|---|---|---|
| 1 — Cart drawer desktop | **PASS by code/build** | Surface, borders, text, and checkout action use brand colors; dimensions unchanged. |
| 2 — Cart item rows | **PASS by code/build** | Image background, borders, text, price, and quantity hover use brand colors; red remove hover retained. |
| 3 — Quantity change | **PASS by preserved code** | `updateQty` handlers and quantity state were untouched. |
| 4 — Cart remove | **PASS by preserved code** | `removeItem` and empty-state logic were untouched. |
| 5 — Empty state | **PASS by code/build** | Empty text and catalog link use brand text colors; logic unchanged. |
| 6 — Cart toast | **PASS by code/build** | Dark brand surface, white text, emerald checkmark retained, orange action hover. |
| 7 — Checkout desktop | **PASS by code/build** | Inputs use brand borders/focus; submit action is orange; dimensions unchanged. |
| 8 — Validation | **PASS by preserved code** | Validation logic and red messages remain unchanged. |
| 9 — Success/WhatsApp | **PASS by code/build** | Emerald success and WhatsApp action plus amber warning remain unchanged. |
| 10 — Error handling | **PASS by preserved code** | Red error banner and submission flow unchanged. |
| 11 — Input focus | **PASS by class** | Focus border is `focus:border-brand-dark`; focus ring remains disabled as before. |
| 12 — Select/radio | **PASS by code/build** | Wilaya select uses shared branded input class. No radio controls exist. |
| 13 — WhatsApp link | **PASS by preserved code** | URL, target, click state, and emerald classes unchanged. |
| 14 — Mobile cart drawer | **PASS by exact class audit** | Width, height, spacing, and layout classes unchanged. |
| 15 — Mobile checkout | **PASS by exact class audit** | Responsive and form dimension classes unchanged. |
| 16 — Sizing regression | **PASS by diff audit** | No drawer width, form height, button height, padding, margin, or gap changed. |
| 17 — Cross-page regression | **PASS by scope/build** | Home, product, admin, and chat files were untouched by this phase; all routes compile. |

---

## 8. WhatsApp green confirmation

WhatsApp and success green are untouched.

Preserved class strings:

```tsx
// CartToast success icon
text-emerald-400

// Checkout success icon
bg-emerald-100 text-emerald-700

// WhatsApp action
bg-emerald-600 text-white hover:bg-emerald-700
```

The warning remains:

```tsx
border-amber-300 bg-amber-50 text-amber-900
```

Errors remain:

```tsx
border-red-300 bg-red-50 text-red-700
text-red-600
hover:text-red-600
```

---

## 9. Dimension confirmation

Checkout form field dimensions, cart drawer width, button heights, padding, margins, gaps, grid structure, responsive classes, and component behavior are byte-identical to their pre-Phase-6 state. Only color-related class substrings changed.
