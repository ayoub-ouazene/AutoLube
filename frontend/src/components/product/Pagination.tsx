"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback } from "react";

interface Props {
  page: number;
  pageSize: number;
  total: number;
}

export function Pagination({ page, pageSize, total }: Props) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const goToPage = useCallback(
    (newPage: number) => {
      const params = new URLSearchParams(searchParams.toString());
      params.set("page", String(newPage));
      router.push(`?${params.toString()}`);
    },
    [router, searchParams],
  );

  if (totalPages <= 1) return null;

  const isFirst = page <= 1;
  const isLast = page >= totalPages;

  return (
    <div className="flex items-center gap-3 mt-6">
      <button
        onClick={() => goToPage(page - 1)}
        disabled={isFirst}
        className="px-3 py-1.5 text-sm border border-neutral-200 rounded-md text-neutral-700 hover:bg-neutral-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        Précédent
      </button>

      <span className="text-sm text-neutral-600">
        Page {page} sur {totalPages}
      </span>

      <button
        onClick={() => goToPage(page + 1)}
        disabled={isLast}
        className="px-3 py-1.5 text-sm border border-neutral-200 rounded-md text-neutral-700 hover:bg-neutral-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        Suivant
      </button>
    </div>
  );
}
