"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { useAdminAuth } from "@/components/admin/AdminAuthProvider";
import {
  type AdminOrderListResponse,
  ORDER_STATUSES,
  type OrderStatus,
  formatDate,
  formatPrice,
  listOrders,
} from "@/lib/adminOrders";
import { OrderStatusBadge } from "@/components/admin/OrderStatusBadge";

const PAGE_SIZE = 20;

export default function OrdersListPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { handleApiError } = useAdminAuth();

  const status = (searchParams.get("status") ?? "") as OrderStatus | "";
  const parsedPage = parseInt(searchParams.get("page") ?? "1", 10);
  const page = Number.isFinite(parsedPage) ? Math.max(1, parsedPage) : 1;

  const [data, setData] = useState<AdminOrderListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
      const query = params.toString();
      router.replace(`/admin/orders${query ? `?${query}` : ""}`);
    },
    [router, searchParams]
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await listOrders({
        status: status || undefined,
        page,
        page_size: PAGE_SIZE,
      });
      setData(result);
    } catch (err) {
      const message = handleApiError(err);
      if (message) setError(message);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [status, page, handleApiError]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- load route-driven data
    load();
  }, [load]);

  const pageCount = data
    ? Math.max(1, Math.ceil(data.total / data.page_size))
    : 1;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-brand-text">Commandes</h1>
        <p className="text-xs text-brand-text-muted">
          {data
            ? `${data.total} commande${data.total === 1 ? "" : "s"}`
            : "…"}
        </p>
      </div>

      <div className="bg-brand-surface border border-brand-border rounded-md p-4 mb-4">
        <div className="flex items-center gap-3">
          <label className="text-sm text-brand-text">Statut</label>
          <select
            value={status}
            onChange={(event) =>
              setUrl({ status: event.target.value || null, page: 1 })
            }
            className="border border-brand-border rounded px-3 py-2 text-sm focus:outline-none focus:border-brand-dark"
          >
            <option value="">Tous</option>
            {ORDER_STATUSES.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
          {status && (
            <button
              type="button"
              onClick={() => setUrl({ status: null, page: 1 })}
              className="text-sm text-brand-text-muted hover:text-brand-text underline"
            >
              Réinitialiser
            </button>
          )}
        </div>
        {status === "delivered" && (
          <p className="text-xs text-brand-text-muted mt-2">
            Aucune commande ne peut avoir ce statut pour le moment — le
            système n&apos;expose pas encore d&apos;action « marquer comme livrée ».
          </p>
        )}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 text-sm rounded-md p-3 mb-4">
          {error}
        </div>
      )}

      {loading ? (
        <p className="text-sm text-brand-text-muted py-8 text-center">
          Chargement…
        </p>
      ) : data && data.items.length === 0 ? (
        <p className="text-sm text-brand-text-muted py-8 text-center">
          Aucune commande trouvée.
        </p>
      ) : data ? (
        <>
          <div className="bg-brand-surface border border-brand-border rounded-md overflow-x-auto">
            <table className="w-full min-w-[900px] text-sm">
              <thead className="bg-brand-bg text-brand-text-muted text-xs uppercase">
                <tr>
                  <th className="px-3 py-2 text-left">#</th>
                  <th className="px-3 py-2 text-left">Date</th>
                  <th className="px-3 py-2 text-left">Client</th>
                  <th className="px-3 py-2 text-left">Localisation</th>
                  <th className="px-3 py-2 text-right">Articles</th>
                  <th className="px-3 py-2 text-right">Total</th>
                  <th className="px-3 py-2 text-left">Statut</th>
                  <th className="px-3 py-2 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((order) => (
                  <tr
                    key={order.id}
                    className="border-t border-brand-border hover:bg-brand-bg"
                  >
                    <td className="px-3 py-2 font-mono text-xs text-brand-text-muted">
                      #{order.id}
                    </td>
                    <td className="px-3 py-2 text-brand-text">
                      {formatDate(order.created_at)}
                    </td>
                    <td className="px-3 py-2">
                      <div className="font-medium text-brand-text">
                        {order.customer_name}
                      </div>
                      <div className="text-xs text-brand-text-muted">
                        {order.customer_phone}
                      </div>
                    </td>
                    <td className="px-3 py-2 text-brand-text-muted">
                      {order.wilaya} · {order.city}
                    </td>
                    <td className="px-3 py-2 text-right text-brand-text">
                      {order.item_count}
                    </td>
                    <td className="px-3 py-2 text-right font-medium">
                      {formatPrice(order.total)}
                    </td>
                    <td className="px-3 py-2">
                      <OrderStatusBadge status={order.status} />
                    </td>
                    <td className="px-3 py-2 text-right">
                      <Link
                        href={`/admin/orders/${order.id}`}
                        className="text-xs border border-brand-border px-2 py-1 rounded hover:bg-brand-bg"
                      >
                        Voir
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between mt-4">
            <div className="text-xs text-brand-text-muted">
              Page {page} sur {pageCount}
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setUrl({ page: Math.max(1, page - 1) })}
                disabled={page <= 1}
                className="text-sm border border-brand-border px-3 py-1.5 rounded disabled:opacity-40 hover:bg-brand-bg"
              >
                ← Précédent
              </button>
              <span className="text-sm text-brand-text-muted">
                {page} / {pageCount}
              </span>
              <button
                type="button"
                onClick={() => setUrl({ page: page + 1 })}
                disabled={!data.has_next}
                className="text-sm border border-brand-border px-3 py-1.5 rounded disabled:opacity-40 hover:bg-brand-bg"
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
