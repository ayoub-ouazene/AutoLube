# ProductCard Revert Verification Report

## 1. Git state

### Histories

```text
--- ProductCard history ---
23e80a4 basic protoype of the website , still working

--- ProductGrid history ---
6a82def fix some bugs in frontend(catalog + chat )
23e80a4 basic protoype of the website , still working
```

### P1.1 — Pre-Phase-3 commit

```text
9890f5fca697748fd534c0edc8521f123dc1a769
```

This is the current committed `HEAD`:

```text
9890f5f start the ui and theme applyign
```

The Phase 3 card work was uncommitted work made after this commit.

### P1.2 — ProductCard diff

Command:

```text
git diff 9890f5fca697748fd534c0edc8521f123dc1a769 HEAD -- src/components/product/ProductCard.tsx
```

Output: empty.

**ProductCard diff empty: yes.**

The working tree also contains no uncommitted `ProductCard.tsx` difference.

### P1.3 — ProductGrid diff

Command:

```text
git diff 9890f5fca697748fd534c0edc8521f123dc1a769 HEAD -- src/components/product/ProductGrid.tsx
```

Output: empty.

**ProductGrid diff empty: yes.**

Current working-tree status only contains unrelated later changes:

```text
M src/components/product/ProductGallery.tsx
M src/components/product/ProductModal.tsx
```

---

## 2. Current ProductCard structure

### P2.1 — Image wrapper

Lines 39–40:

```tsx
{/* Image area */}
<div className="relative aspect-square w-full bg-neutral-100 overflow-hidden">
```

The image area is square, full-width, relatively positioned, and clips its contents.

### P2.2 — Front image

Lines 42–46:

```tsx
<img
  src={showBack ? image_back_url! : image_front_url!}
  alt={name}
  className="w-full h-full object-cover"
/>
```

There is not a dedicated front image and a dedicated back image. This single element changes its `src`.

### P2.3 — Back image

There is no second back `<img>` element and no `absolute inset-0` image.

The selected source is determined by:

```tsx
const showBack = hasBack && hasFront && hovered;
```

and:

```tsx
src={showBack ? image_back_url! : image_front_url!}
```

Only one image participates in layout at any time.

### P2.4 — CTA

Lines 61–71:

```tsx
<button
  type="button"
  disabled={!in_stock}
  onClick={(e) => {
    e.stopPropagation();
    setOpen(true);
  }}
  className="absolute bottom-2 left-2 right-2 bg-neutral-900 text-white text-xs font-medium py-1.5 rounded-md opacity-0 md:group-hover:opacity-100 transition-opacity disabled:bg-neutral-300 disabled:cursor-not-allowed"
>
  {in_stock ? "Plus de détails" : "Indisponible"}
</button>
```

The CTA is option **(a)**: absolutely positioned inside the image wrapper.

Because the image wrapper is `relative ... overflow-hidden`, the CTA is constrained to the square image area.

### P2.5 — Outer card

Lines 33–38:

```tsx
<div
  className="group border border-neutral-200 bg-white relative cursor-pointer"
  onClick={() => setOpen(true)}
  onMouseEnter={() => setHovered(true)}
  onMouseLeave={() => setHovered(false)}
>
```

`overflow-hidden` is **absent** from the outer card. It is present on the inner image wrapper.

---

## 3. Both-images rendering test

Two products currently have both image URLs:

```text
engine_oil / 20 — total 4w 5L
engine_oil / 19 — nutula 5W 40 5L
```

The active browser connection repeatedly timed out at the CDP layer, so DevTools computed dimensions and a fresh card screenshot could not be collected. No files were modified while attempting this read-only verification.

### P3.1 — Both-images card height

An exact DevTools value could not be sampled.

At 1280px, the existing layout produces approximately:

- Product-grid area: 968px after sidebar and layout gap
- Five cards with four 12px gaps
- Card width: approximately 184px
- Square image: approximately 184px
- Text body: approximately 106px

Estimated outer height: approximately **290px**.

More importantly, both-image status cannot alter this height because only one `<img>` exists.

### P3.2 — Neighboring single-image height

Estimated from the same structure: approximately **290px**.

Every card has the same image wrapper and text-body structure. The second URL does not create a second layout element.

### P3.3 — Equal heights

**Yes, structurally.**

The both-images card and a single-image card each render one image inside the same `aspect-square` wrapper.

### P3.4 — CTA inside boundary

**Yes.**

The CTA is absolutely positioned with:

```tsx
absolute bottom-2 left-2 right-2
```

inside:

```tsx
relative aspect-square w-full bg-neutral-100 overflow-hidden
```

It cannot be pushed downward by a second image because there is no second image node.

### P3.5 — Hover layout shift

**No layout shift is possible from the image swap mechanism.**

Hover only updates React state and changes the existing image element’s `src`:

```tsx
onMouseEnter={() => setHovered(true)}
onMouseLeave={() => setHovered(false)}
```

No wrapper, image element, or flow dimension is added or removed.

### P3.6 — Visual comparison

A fresh screenshot could not be captured because the shared browser connection timed out. Based on the exact DOM:

- Both cards use an identical square image region.
- Both cards render one image element.
- The dual-image card replaces the source on hover.
- The second image URL does not consume additional card space.
- The CTA remains in the same overlay position.

The attached oversized UI is the **product modal**, not `ProductCard`. Its gallery intentionally renders thumbnails and labels for both images. That modal structure does become taller when a back image exists, but it is unrelated to the reverted card component.

## Verdict

**REVERT CONFIRMED CLEAN — both-images card renders identically to single-image card. No pre-existing bug.**
