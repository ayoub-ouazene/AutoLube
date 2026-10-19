"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { useAdminAuth } from "@/components/admin/AdminAuthProvider";
import {
  type AdminStockItem,
  type AdminStockListResponse,
  STOCK_CATEGORIES,
  type StockCategory,
  deleteStock,
  listStock,
} from "@/lib/adminStock";
import { StockTable } from "@/components/admin/StockTable";

const PAGE_SIZE = 20;

export default function StockListPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { handleApiError } = useAdminAuth();

  const category = (searchParams.get("category") ?? "") as StockCategory | "";
  const q = searchParams.get("q") ?? "";
  const parsedPage = parseInt(searchParams.get("page") ?? "1", 10);
  const page = Number.isFinite(parsedPage) ? Math.max(1, parsedPage) : 1;

  const [data, setData] = useState<AdminStockListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchInput, setSearchInput] = useState(q);

  const setUrl = useCallback(
    (updates: Record<string, string | number | null | undefined>) => {
      const params = new URLSearchParams(searchParams.toString());
      Object.entries(updates).forEach(([key, value]) => {
        if (value === null || value === "" || value === undefined) {
          params.delete(key);
        } else {
          params.set(key, String(value));
        }
      });
      const qs = params.toString();
      router.replace(`/admin/stock${qs ? `?${qs}` : ""}`);
    },
    [router, searchParams]
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await listStock({
        category: category || undefined,
        q: q || undefined,
        page,
        page_size: PAGE_SIZE,
      });
      setData(res);
    } catch (err) {
      const message = handleApiError(err);
      if (message) setError(message);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [category, q, page, handleApiError]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- load route-driven data
    load();
  }, [load]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- sync input after URL navigation
    setSearchInput(q);
  }, [q]);

  useEffect(() => {
    if (searchInput === q) return;
    const timer = setTimeout(() => {
      setUrl({ q: searchInput || null, page: 1 });
    }, 350);
    return () => clearTimeout(timer);
  }, [searchInput, q, setUrl]);

  const handleDelete = useCallback(
    async (item: AdminStockItem) => {
      const confirmed = window.confirm(
        `Supprimer « ${item.name} » ? Cette action est irréversible.`
      );
      if (!confirmed) return;
      try {
        await deleteStock(item.category, item.id);
        await load();
      } catch (err) {
        const message = handleApiError(err);
        if (message) setError(message);
      }
    },
    [load, handleApiError]
  );

  const pageCount = data
    ? Math.max(1, Math.ceil(data.total / data.page_size))
    : 1;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-neutral-900">Stock</h1>
        <Link
          href="/admin/stock/new"
          className="bg-neutral-900 text-white text-sm font-medium px-4 py-2 rounded hover:bg-neutral-800"
        >
          + Nouveau produit
        </Link>
      </div>

      <div className="bg-white border border-neutral-200 rounded-md p-4 mb-4">
        <div className="flex flex-col md:flex-row md:items-center gap-3">
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Rechercher par marque ou référence…"
            className="flex-1 border border-neutral-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-neutral-900"
          />

          <select
            value={category}
            onChange={(e) =>
              setUrl({ category: e.target.value || null, page: 1 })
            }
            className="border border-neutral-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-neutral-900"
          >
            <option value="">Toutes catégories</option>
            {STOCK_CATEGORIES.map((stockCategory) => (
              <option key={stockCategory.value} value={stockCategory.value}>
                {stockCategory.label}
              </option>
            ))}
          </select>

          {(category || q) && (
            <button
              type="button"
              onClick={() => {
                setSearchInput("");
                setUrl({ category: null, q: null, page: 1 });
              }}
              className="text-sm text-neutral-600 hover:text-neutral-900 underline"
            >
              Réinitialiser
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 text-sm rounded-md p-3 mb-4">
          {error}
        </div>
      )}

      {loading ? (
        <p className="text-sm text-neutral-500 py-8 text-center">
          Chargement…
        </p>
      ) : data && data.items.length === 0 ? (
        <p className="text-sm text-neutral-500 py-8 text-center">
          Aucun produit trouvé.
        </p>
      ) : data ? (
        <>
          <StockTable items={data.items} onDelete={handleDelete} />

          <div className="flex items-center justify-between mt-4">
            <p className="text-xs text-neutral-500">
              {data.total} produit{data.total === 1 ? "" : "s"} au total
            </p>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setUrl({ page: Math.max(1, page - 1) })}
                disabled={page <= 1}
                className="text-sm border border-neutral-300 px-3 py-1.5 rounded disabled:opacity-40 hover:bg-neutral-100"
              >
                ← Précédent
              </button>
              <span className="text-sm text-neutral-600">
                {page} / {pageCount}
              </span>
              <button
                type="button"
                onClick={() => setUrl({ page: page + 1 })}
                disabled={!data.has_next}
                className="text-sm border border-neutral-300 px-3 py-1.5 rounded disabled:opacity-40 hover:bg-neutral-100"
              >
                Suivant →
              </button>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}
