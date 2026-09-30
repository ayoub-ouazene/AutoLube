"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useState } from "react";
import Link from "next/link";

function formatDA(n: number): string {
  return `${n.toLocaleString("fr-DZ")} DA`;
}

const CATEGORIES = [
  { id: "engine_oil", label: "Huile moteur" },
  { id: "gearbox_oil", label: "Huile de boîte" },
  { id: "oil_filter", label: "Filtres" },
  { id: "additional", label: "Autres" },
] as const;

export function CatalogSidebar({
  maxPrice,
  brands,
  sizes,
}: {
  maxPrice: number;
  brands: string[];
  sizes: string[];
}) {
  const router = useRouter();
  const searchParams = useSearchParams();

  // ── Current URL state ──────────────────────────────────────────────────────
  const selectedCategories = searchParams.getAll("category");
  const selectedBrands = searchParams.getAll("brand");
  const selectedSizes = searchParams.getAll("size");
  const urlMinPrice = searchParams.get("min_price") ?? "";
  const urlMaxPrice = searchParams.get("max_price") ?? "";

  // ── Local input state (for price slider) ───────────────────────────────
  const [minPriceInput, setMinPriceInput] = useState(
    Number(urlMinPrice) || 0
  );
  const [maxPriceInput, setMaxPriceInput] = useState(
    Number(urlMaxPrice) || maxPrice
  );

  // Reset local state when URL params change (e.g. "Réinitialiser" link)
  const [prevSearch, setPrevSearch] = useState(searchParams.toString());
  if (prevSearch !== searchParams.toString()) {
    setPrevSearch(searchParams.toString());
    setMinPriceInput(Number(searchParams.get("min_price")) || 0);
    setMaxPriceInput(Number(searchParams.get("max_price")) || maxPrice);
  }

  // ── Helpers ────────────────────────────────────────────────────────────────
  const pushParams = useCallback(
    (mutate: (p: URLSearchParams) => void) => {
      const p = new URLSearchParams(searchParams.toString());
      p.delete("page");
      mutate(p);
      router.replace(`?${p.toString()}`);
    },
    [router, searchParams],
  );

  // ── Category toggle (immediate) ───────────────────────────────────────────
  const toggleCategory = useCallback(
    (cat: string) => {
      pushParams((p) => {
        const cats = p.getAll("category");
        p.delete("category");
        if (cats.includes(cat)) {
          cats.filter((c) => c !== cat).forEach((c) => p.append("category", c));
        } else {
          cats.forEach((c) => p.append("category", c));
          p.append("category", cat);
        }
      });
    },
    [pushParams],
  );

  // ── Size toggle ──────────────────────────────────────────────────────────
  const toggleSize = useCallback(
    (s: string) => {
      pushParams((p) => {
        p.delete("size");
        const next = selectedSizes.includes(s)
          ? selectedSizes.filter((x) => x !== s)
          : [...selectedSizes, s];
        next.forEach((s2) => p.append("size", s2));
      });
    },
    [pushParams, selectedSizes],
  );
  // ── Brand toggle ─────────────────────────────────────────────────────────
  const toggleBrand = useCallback(
    (b: string) => {
      pushParams((p) => {
        p.delete("brand");
        const next = selectedBrands.includes(b)
          ? selectedBrands.filter((x) => x !== b)
          : [...selectedBrands, b];
        next.forEach((b2) => p.append("brand", b2));
      });
    },
    [pushParams, selectedBrands],
  );

  // ── Price apply ──────────────────────────────────────────────────────────
  const applyPrice = () => {
    pushParams((p) => {
      if (minPriceInput > 0) p.set("min_price", String(minPriceInput));
      else p.delete("min_price");
      if (maxPriceInput < maxPrice) p.set("max_price", String(maxPriceInput));
      else p.delete("max_price");
    });
  };

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="w-full md:w-60 shrink-0 flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-neutral-200">
        <h2 className="text-base font-semibold text-neutral-900">Filtres</h2>
        <Link
          href="/products"
          className="text-xs text-neutral-500 hover:text-neutral-900 underline underline-offset-2"
        >
          Réinitialiser
        </Link>
      </div>

      {/* Categories */}
      <div className="border border-neutral-200 p-4">
        <h3 className="text-sm font-medium text-neutral-900 mb-3">
          Catégories
        </h3>
        <div className="space-y-2">
          {CATEGORIES.map((cat) => (
            <label
              key={cat.id}
              className="flex items-center gap-2 cursor-pointer"
            >
              <input
                type="checkbox"
                checked={selectedCategories.includes(cat.id)}
                onChange={() => toggleCategory(cat.id)}
                className="w-4 h-4 accent-neutral-900"
              />
              <span className="text-sm text-neutral-600">{cat.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Price */}
      <div className="border border-neutral-200 p-4">
        <h3 className="text-sm font-medium text-neutral-900 mb-3">
          Prix (DA)
        </h3>

        <p className="text-xs text-neutral-500 mb-3">
          De {formatDA(minPriceInput)} à {formatDA(maxPriceInput)}
        </p>

        <div className="price-slider relative h-1 bg-neutral-200 rounded-full my-4">
          <input
            type="range"
            min={0}
            max={maxPrice}
            step={100}
            value={minPriceInput}
            onChange={(e) => {
              const v = Math.min(Number(e.target.value), maxPriceInput);
              setMinPriceInput(v);
            }}
            onMouseUp={applyPrice}
            onTouchEnd={applyPrice}
            className="absolute top-1/2 -translate-y-1/2 w-full appearance-none bg-transparent pointer-events-none"
            aria-label="Prix minimum"
          />
          <input
            type="range"
            min={0}
            max={maxPrice}
            step={100}
            value={maxPriceInput}
            onChange={(e) => {
              const v = Math.max(Number(e.target.value), minPriceInput);
              setMaxPriceInput(v);
            }}
            onMouseUp={applyPrice}
            onTouchEnd={applyPrice}
            className="absolute top-1/2 -translate-y-1/2 w-full appearance-none bg-transparent pointer-events-none"
            aria-label="Prix maximum"
          />
        </div>
      </div>

      {/* Brand */}
      <div className="border border-neutral-200 p-3 mb-3">
        <h3 className="text-xs uppercase tracking-wide text-neutral-500 mb-2">
          Marque
        </h3>
        <div className="max-h-56 overflow-y-auto space-y-1.5">
          {brands.length === 0 ? (
            <p className="text-xs text-neutral-500">Aucune marque disponible.</p>
          ) : (
            brands.map((b) => (
              <label key={b} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={selectedBrands.includes(b)}
                  onChange={() => toggleBrand(b)}
                  className="accent-neutral-900"
                />
                <span>{b}</span>
              </label>
            ))
          )}
        </div>
      </div>

      {/* Size / Conditionnement */}
      <div className="border border-neutral-200 p-3 mb-3">
        <h3 className="text-xs uppercase tracking-wide text-neutral-500 mb-2">
          Conditionnement
        </h3>
        <div className="max-h-56 overflow-y-auto space-y-1.5">
          {sizes.length === 0 ? (
            <p className="text-xs text-neutral-500">Aucun format disponible.</p>
          ) : (
            sizes.map((s) => (
              <label key={s} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={selectedSizes.includes(s)}
                  onChange={() => toggleSize(s)}
                  className="accent-neutral-900"
                />
                <span>{s}</span>
              </label>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
