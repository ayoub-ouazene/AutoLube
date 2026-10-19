"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAdminAuth } from "@/components/admin/AdminAuthProvider";
import { StockForm } from "@/components/admin/StockForm";
import { createStock, type StockCreatePayload } from "@/lib/adminStock";

export default function NewStockPage() {
  const router = useRouter();
  const { handleApiError } = useAdminAuth();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (
    payload: StockCreatePayload | Record<string, unknown>
  ) => {
    setSubmitting(true);
    setError(null);
    try {
      await createStock(payload as StockCreatePayload);
      router.replace("/admin/stock");
    } catch (err) {
      const message = handleApiError(err);
      if (message) setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-semibold text-neutral-900 mb-6">
        Nouveau produit
      </h1>
      <StockForm
        mode="create"
        onSubmit={handleSubmit}
        onCancel={() => router.replace("/admin/stock")}
        submitting={submitting}
        errorMessage={error}
      />
    </div>
  );
}
