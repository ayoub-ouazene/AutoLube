"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useAdminAuth } from "@/components/admin/AdminAuthProvider";
import { useConfirm } from "@/components/admin/ConfirmProvider";
import {
  type AdminOrderDetail,
  cancelOrder,
  confirmOrder,
  formatDate,
  formatPrice,
  getOrder,
  statusLabel,
  whatsappUrl,
} from "@/lib/adminOrders";
import { OrderStatusBadge } from "@/components/admin/OrderStatusBadge";

export default function OrderDetailPage() {
  const params = useParams<{ id: string }>();
  const { handleApiError } = useAdminAuth();
  const confirm = useConfirm();
  const orderId = parseInt(params.id, 10);

  const [order, setOrder] = useState<AdminOrderDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [acting, setActing] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (isNaN(orderId)) {
      setLoadError("Identifiant de commande invalide.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setLoadError(null);
    try {
      const result = await getOrder(orderId);
      setOrder(result);
    } catch (err) {
      const message = handleApiError(err);
      if (message) setLoadError(message);
      setOrder(null);
    } finally {
      setLoading(false);
    }
  }, [orderId, handleApiError]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- load route-driven data
    load();
  }, [load]);

  const handleConfirm = async () => {
    if (!order) return;
    const confirmed = await confirm(
      `Confirmer la commande #${order.id} ? Le stock des produits sera décrémenté. Si le stock est insuffisant, la confirmation échouera.`,
      {
        title: "Confirmer cette commande ?",
        confirmLabel: "Confirmer",
        cancelLabel: "Annuler",
      }
    );
    if (!confirmed) return;

    setActing(true);
    setActionError(null);
    try {
      await confirmOrder(order.id);
      await load();
    } catch (err) {
      const message = handleApiError(err);
      if (message) setActionError(message);
    } finally {
      setActing(false);
    }
  };

  const handleCancel = async () => {
    if (!order) return;
    const confirmed = await confirm(
      `Annuler la commande #${order.id} ? Cette action est irréversible.`,
      {
        title: "Annuler cette commande ?",
        confirmLabel: "Annuler la commande",
        cancelLabel: "Retour",
        danger: true,
      }
    );
    if (!confirmed) return;

    setActing(true);
    setActionError(null);
    try {
      await cancelOrder(order.id);
      await load();
    } catch (err) {
      const message = handleApiError(err);
      if (message) setActionError(message);
    } finally {
      setActing(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <p className="text-sm text-neutral-500">Chargement…</p>
      </div>
    );
  }

  if (loadError || !order) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <p className="text-sm text-red-600">
          {loadError ?? "Commande introuvable."}
        </p>
        <Link
          href="/admin/orders"
          className="mt-4 inline-block text-sm underline text-neutral-700"
        >
          ← Retour aux commandes
        </Link>
      </div>
    );
  }

  const canConfirm = order.status === "pending";
  const canCancel = order.status === "pending";

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <Link
        href="/admin/orders"
        className="text-sm text-neutral-600 hover:text-neutral-900 underline mb-4 inline-block"
      >
        ← Retour aux commandes
      </Link>

      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-neutral-900">
            Commande #{order.id}
          </h1>
          <p className="text-sm text-neutral-500 mt-1">
            {formatDate(order.created_at)}
          </p>
        </div>
        <OrderStatusBadge status={order.status} />
      </div>

      {actionError && (
        <div className="bg-red-50 border border-red-200 text-red-800 text-sm rounded-md p-3 mb-4">
          {actionError}
        </div>
      )}

      {canConfirm || canCancel ? (
        <div className="bg-white border border-neutral-200 rounded-md p-4 mb-6 flex items-center gap-3">
          {canConfirm && (
            <button
              type="button"
              onClick={handleConfirm}
              disabled={acting}
              className="bg-neutral-900 text-white text-sm font-medium px-4 py-2 rounded hover:bg-neutral-800 disabled:bg-neutral-400"
            >
              {acting ? "Traitement…" : "Confirmer la commande"}
            </button>
          )}
          {canCancel && (
            <button
              type="button"
              onClick={handleCancel}
              disabled={acting}
              className="text-sm border border-red-200 text-red-700 px-4 py-2 rounded hover:bg-red-50 disabled:opacity-40"
            >
              Annuler la commande
            </button>
          )}
        </div>
      ) : (
        <div className="bg-neutral-50 border border-neutral-200 rounded-md p-3 mb-6 text-sm text-neutral-600">
          {order.status === "confirmed" &&
            "Cette commande est confirmée. Elle ne peut plus être annulée."}
          {order.status === "cancelled" && "Cette commande est annulée."}
          {order.status === "delivered" &&
            "Cette commande est marquée comme livrée."}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="md:col-span-2 bg-white border border-neutral-200 rounded-md p-4">
          <h2 className="text-sm font-medium text-neutral-900 mb-3">Client</h2>
          <dl className="grid grid-cols-1 gap-2 text-sm">
            <div className="flex gap-2">
              <dt className="text-neutral-500 w-28 shrink-0">Nom</dt>
              <dd className="text-neutral-900">{order.customer_name}</dd>
            </div>
            <div className="flex gap-2">
              <dt className="text-neutral-500 w-28 shrink-0">Téléphone</dt>
              <dd>
                <a
                  href={whatsappUrl(order.customer_phone)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-neutral-900 underline hover:text-green-700"
                >
                  {order.customer_phone}
                </a>
              </dd>
            </div>
            {order.customer_email && (
              <div className="flex gap-2">
                <dt className="text-neutral-500 w-28 shrink-0">Email</dt>
                <dd>
                  <a
                    href={`mailto:${order.customer_email}`}
                    className="text-neutral-900 underline"
                  >
                    {order.customer_email}
                  </a>
                </dd>
              </div>
            )}
            <div className="flex gap-2">
              <dt className="text-neutral-500 w-28 shrink-0">Localisation</dt>
              <dd className="text-neutral-900">
                {order.wilaya} · {order.city}
              </dd>
            </div>
            {order.notes && (
              <div className="flex gap-2">
                <dt className="text-neutral-500 w-28 shrink-0">Notes</dt>
                <dd className="text-neutral-900 whitespace-pre-wrap">
                  {order.notes}
                </dd>
              </div>
            )}
          </dl>
        </div>

        <div className="bg-white border border-neutral-200 rounded-md p-4">
          <h2 className="text-sm font-medium text-neutral-900 mb-3">Total</h2>
          <p className="text-2xl font-semibold text-neutral-900">
            {formatPrice(order.total)}
          </p>
          <p className="text-xs text-neutral-500 mt-1">
            {order.items.reduce((sum, item) => sum + item.quantity, 0)} article(s)
          </p>
        </div>
      </div>

      <div className="bg-white border border-neutral-200 rounded-md overflow-x-auto">
        <table className="w-full min-w-[700px] text-sm">
          <thead className="bg-neutral-50 text-neutral-600 text-xs uppercase">
            <tr>
              <th className="px-3 py-2 text-left">Article</th>
              <th className="px-3 py-2 text-left">Spécification</th>
              <th className="px-3 py-2 text-left">Taille</th>
              <th className="px-3 py-2 text-right">P.U.</th>
              <th className="px-3 py-2 text-right">Qté</th>
              <th className="px-3 py-2 text-right">Total ligne</th>
            </tr>
          </thead>
          <tbody>
            {order.items.map((item) => (
              <tr key={item.id} className="border-t border-neutral-100">
                <td className="px-3 py-2">
                  <div className="font-medium text-neutral-900">
                    {item.brand}
                  </div>
                  <div className="text-xs text-neutral-500">{item.name}</div>
                </td>
                <td className="px-3 py-2 text-neutral-600">
                  {item.specification}
                </td>
                <td className="px-3 py-2 text-neutral-600">
                  {item.size ?? "—"}
                </td>
                <td className="px-3 py-2 text-right">
                  {formatPrice(item.unit_price)}
                </td>
                <td className="px-3 py-2 text-right">{item.quantity}</td>
                <td className="px-3 py-2 text-right font-medium">
                  {formatPrice(item.line_total)}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot className="bg-neutral-50 border-t border-neutral-200">
            <tr>
              <td
                colSpan={5}
                className="px-3 py-2 text-right text-sm font-medium text-neutral-700"
              >
                Total
              </td>
              <td className="px-3 py-2 text-right font-semibold text-neutral-900">
                {formatPrice(order.total)}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      <p className="text-xs text-neutral-500 mt-4">
        Statut actuel : {statusLabel(order.status)}.
      </p>
    </div>
  );
}
