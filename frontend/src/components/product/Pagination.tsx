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
        className="px-3 py-1.5 text-sm border border-brand-orange rounded-md bg-brand-orange text-white cursor-pointer hover:bg-brand-orange-hover hover:border-brand-orange-hover disabled:bg-brand-bg disabled:text-brand-text-muted disabled:border-brand-border disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        Précédent
      </button>

      <span className="text-sm text-brand-text-muted">
        Page {page} sur {pageCount}
      </span>

      <button
        onClick={() => setFilters({ page: page + 1 })}
        disabled={isLast}
        className="px-3 py-1.5 text-sm border border-brand-orange rounded-md bg-brand-orange text-white cursor-pointer hover:bg-brand-orange-hover hover:border-brand-orange-hover disabled:bg-brand-bg disabled:text-brand-text-muted disabled:border-brand-border disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        Suivant
      </button>
    </div>
  );
}
