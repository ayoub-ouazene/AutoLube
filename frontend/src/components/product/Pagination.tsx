"use client";

import { useCatalog } from "./CatalogProvider";

export function Pagination() {
  const { filters, pageCount, setFilters } = useCatalog();
  const page = Math.min(filters.page, pageCount);

  if (pageCount <= 1) return null;

  const isFirst = page <= 1;
  const isLast = page >= pageCount;

  return (
    <div className="flex items-center gap-3 mt-6">
      <button
        onClick={() => setFilters({ page: page - 1 })}
        disabled={isFirst}
        className="px-3 py-1.5 text-sm border border-neutral-200 rounded-md text-neutral-700 hover:bg-neutral-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        Précédent
      </button>

      <span className="text-sm text-neutral-600">
        Page {page} sur {pageCount}
      </span>

      <button
        onClick={() => setFilters({ page: page + 1 })}
        disabled={isLast}
        className="px-3 py-1.5 text-sm border border-neutral-200 rounded-md text-neutral-700 hover:bg-neutral-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        Suivant
      </button>
    </div>
  );
}
