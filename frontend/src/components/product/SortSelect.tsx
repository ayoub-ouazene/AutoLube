"use client";

import { useCatalog } from "./CatalogProvider";

const SORT_OPTIONS = [
  { value: "random", label: "Recommandés" },
  { value: "price_asc", label: "Prix croissant" },
  { value: "price_desc", label: "Prix décroissant" },
] as const;

export function SortSelect({ className = "" }: { className?: string }) {
  const { filters, setFilters } = useCatalog();

  return (
    <select
      value={filters.sort}
      onChange={(event) =>
        setFilters({ sort: event.target.value as typeof filters.sort })
      }
      aria-label="Trier les produits"
      className={
        "border border-neutral-300 rounded px-3 py-1.5 text-sm " +
        "focus:outline-none focus:border-neutral-900 bg-white " +
        className
      }
    >
      {SORT_OPTIONS.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}