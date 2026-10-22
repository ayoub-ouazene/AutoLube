"use client";

import { useEffect, useState } from "react";
import { useCatalog } from "./CatalogProvider";

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
  const { filters, setFilters } = useCatalog();
  const selectedCategories = filters.categories;
  const selectedBrands = filters.brands;
  const selectedSizes = filters.sizes;

  // ── Local input state (for price slider) ───────────────────────────────
  const [minPriceInput, setMinPriceInput] = useState(
    filters.minPrice ?? 0
  );
  const [maxPriceInput, setMaxPriceInput] = useState(
    filters.maxPrice ?? maxPrice
  );

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- sync after external reset
    setMinPriceInput(filters.minPrice ?? 0);
    setMaxPriceInput(filters.maxPrice ?? maxPrice);
  }, [filters.minPrice, filters.maxPrice, maxPrice]);

  // ── Category toggle (immediate) ───────────────────────────────────────────
  const toggleCategory = (cat: string) => {
    const next = selectedCategories.includes(cat)
      ? selectedCategories.filter((c) => c !== cat)
      : [...selectedCategories, cat];
    setFilters({ categories: next });
  };

  // ── Size toggle ──────────────────────────────────────────────────────────
  const toggleSize = (s: string) => {
    const next = selectedSizes.includes(s)
      ? selectedSizes.filter((x) => x !== s)
      : [...selectedSizes, s];
    setFilters({ sizes: next });
  };
  // ── Brand toggle ─────────────────────────────────────────────────────────
  const toggleBrand = (b: string) => {
    const next = selectedBrands.includes(b)
      ? selectedBrands.filter((x) => x !== b)
      : [...selectedBrands, b];
    setFilters({ brands: next });
  };

  // ── Price apply ──────────────────────────────────────────────────────────
  const applyPrice = () => {
    setFilters({
      minPrice: minPriceInput > 0 ? minPriceInput : null,
      maxPrice: maxPriceInput < maxPrice ? maxPriceInput : null,
    });
  };

  const resetFilters = () => {
    setFilters({
      categories: [],
      brands: [],
      sizes: [],
      minPrice: null,
      maxPrice: null,
      q: "",
      page: 1,
    });
  };

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="w-full md:w-60 shrink-0 flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-brand-border">
        <h2 className="text-base font-semibold text-brand-text">Filtres</h2>
        <button
          type="button"
          onClick={resetFilters}
          className="text-xs text-brand-text-muted hover:text-brand-text underline underline-offset-2"
        >
          Réinitialiser
        </button>
      </div>

      {/* Categories */}
      <div className="border border-brand-border p-4">
        <h3 className="text-sm font-medium text-brand-text mb-3">
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
                className="w-4 h-4 accent-brand-orange"
              />
              <span className="text-sm text-brand-text-muted">{cat.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Price */}
      <div className="border border-brand-border p-4">
        <h3 className="text-sm font-medium text-brand-text mb-3">
          Prix (DA)
        </h3>

        <p className="text-xs text-brand-text-muted mb-3">
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
      <div className="border border-brand-border p-3 mb-3">
        <h3 className="text-xs uppercase tracking-wide text-brand-text-muted mb-2">
          Marque
        </h3>
        <div className="max-h-56 overflow-y-auto space-y-1.5">
          {brands.length === 0 ? (
            <p className="text-xs text-brand-text-muted">Aucune marque disponible.</p>
          ) : (
            brands.map((b) => (
              <label key={b} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={selectedBrands.includes(b)}
                  onChange={() => toggleBrand(b)}
                  className="accent-brand-orange"
                />
                <span>{b}</span>
              </label>
            ))
          )}
        </div>
      </div>

      {/* Size / Conditionnement */}
      <div className="border border-brand-border p-3 mb-3">
        <h3 className="text-xs uppercase tracking-wide text-brand-text-muted mb-2">
          Conditionnement
        </h3>
        <div className="max-h-56 overflow-y-auto space-y-1.5">
          {sizes.length === 0 ? (
            <p className="text-xs text-brand-text-muted">Aucun format disponible.</p>
          ) : (
            sizes.map((s) => (
              <label key={s} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={selectedSizes.includes(s)}
                  onChange={() => toggleSize(s)}
                  className="accent-brand-orange"
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
