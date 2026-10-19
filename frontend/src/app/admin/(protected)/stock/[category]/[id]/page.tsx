"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAdminAuth } from "@/components/admin/AdminAuthProvider";
import { useConfirm } from "@/components/admin/ConfirmProvider";
import { StockForm } from "@/components/admin/StockForm";
import {
  type AdminStockItem,
  type StockCategory,
  type StockCreatePayload,
  type StockUpdatePayload,
  deleteStock,
  findStockItem,
  updateStock,
} from "@/lib/adminStock";

const VALID_CATEGORIES: StockCategory[] = [
  "engine_oil",
  "gearbox_oil",
  "oil_filter",
  "additional",
];

export default function EditStockPage() {
  const params = useParams<{ category: string; id: string }>();
  const router = useRouter();
  const { handleApiError } = useAdminAuth();
  const confirm = useConfirm();

  const category = params.category as StockCategory;
  const id = parseInt(params.id, 10);

  const [item, setItem] = useState<AdminStockItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const loadItem = useCallback(async () => {
    if (!VALID_CATEGORIES.includes(category) || isNaN(id)) {
      setLoadError("URL invalide.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setLoadError(null);
    try {
      const found = await findStockItem(category, id);
      if (!found) {
        setLoadError("Produit introuvable.");
        setItem(null);
      } else {
        setItem(found);
      }
    } catch (err) {
      const message = handleApiError(err);
      if (message) setLoadError(message);
    } finally {
      setLoading(false);
    }
  }, [category, id, handleApiError]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- load route-driven item
    loadItem();
  }, [loadItem]);

  const handleSubmit = async (
    payload: StockCreatePayload | Record<string, unknown>
  ) => {
    if (!item) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const raw = payload as Record<string, unknown>;
      const updatePayload: StockUpdatePayload = {};
      if (raw.brand !== undefined) updatePayload.brand = String(raw.brand);
      if (raw.specification !== undefined) {
        updatePayload.specification = String(raw.specification);
      }
      if (raw.viscosity !== undefined) {
        updatePayload.viscosity = String(raw.viscosity);
      }
      if (raw.size !== undefined) updatePayload.size = String(raw.size);
      if (raw.price !== undefined) updatePayload.price = Number(raw.price);
      if (raw.quantity !== undefined) {
        updatePayload.quantity = Number(raw.quantity);
      }
      if (raw.category_type !== undefined) {
        updatePayload.category_type = String(raw.category_type);
      }

      if (category === "oil_filter" || category === "additional") {
        updatePayload.viscosity = "";
        updatePayload.size = "";
      }

      await updateStock(category, id, updatePayload);
      router.replace("/admin/stock");
    } catch (err) {
      const message = handleApiError(err);
      if (message) setSubmitError(message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!item) return;
    const confirmed = await confirm(
      `Le produit « ${item.name} » sera définitivement supprimé. Cette action est irréversible.`,
      {
        title: "Supprimer ce produit ?",
        confirmLabel: "Supprimer",
        cancelLabel: "Annuler",
        danger: true,
      }
    );
    if (!confirmed) return;
    try {
      await deleteStock(category, id);
      router.replace("/admin/stock");
    } catch (err) {
      const message = handleApiError(err);
      if (message) setSubmitError(message);
    }
  };

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8">
        <p className="text-sm text-neutral-500">Chargement…</p>
      </div>
    );
  }

  if (loadError || !item) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8">
        <p className="text-sm text-red-600">
          {loadError ?? "Produit introuvable."}
        </p>
        <button
          type="button"
          onClick={() => router.replace("/admin/stock")}
          className="mt-4 text-sm underline text-neutral-700"
        >
          Retour au stock
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-neutral-900">
          Modifier le produit
        </h1>
        <button
          type="button"
          onClick={handleDelete}
          className="text-sm border border-red-200 text-red-700 px-3 py-1.5 rounded hover:bg-red-50"
        >
          Supprimer
        </button>
      </div>
      <StockForm
        mode="edit"
        initial={item}
        onSubmit={handleSubmit}
        onCancel={() => router.replace("/admin/stock")}
        submitting={submitting}
        errorMessage={submitError}
      />
    </div>
  );
}
