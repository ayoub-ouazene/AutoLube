"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAdminAuth } from "@/components/admin/AdminAuthProvider";
import { StockForm } from "@/components/admin/StockForm";
import { ImagePicker } from "@/components/admin/ImagePicker";
import {
  createStock,
  type StockCreatePayload,
  uploadStockImage,
} from "@/lib/adminStock";

export default function NewStockPage() {
  const router = useRouter();
  const { handleApiError } = useAdminAuth();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [frontFile, setFrontFile] = useState<File | null>(null);
  const [backFile, setBackFile] = useState<File | null>(null);

  const handleSubmit = async (
    payload: StockCreatePayload | Record<string, unknown>
  ) => {
    setSubmitting(true);
    setError(null);
    try {
      const created = await createStock(payload as StockCreatePayload);

      try {
        if (frontFile) {
          await uploadStockImage(
            created.category,
            created.id,
            "front",
            frontFile
          );
        }
        if (backFile) {
          await uploadStockImage(
            created.category,
            created.id,
            "back",
            backFile
          );
        }
      } catch (uploadError) {
        console.error("[create] image upload failed", uploadError);
      }

      router.replace(`/admin/stock/${created.category}/${created.id}`);
    } catch (err) {
      const message = handleApiError(err);
      if (message) setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="w-full max-w-none px-4 py-8 md:px-6 lg:px-8">
      <h1 className="text-2xl font-semibold text-brand-text mb-6">
        Nouveau produit
      </h1>
      <div className="grid grid-cols-1 items-start gap-6 md:grid-cols-2">
        <StockForm
          mode="create"
          onSubmit={handleSubmit}
          onCancel={() => router.replace("/admin/stock")}
          submitting={submitting}
          errorMessage={error}
        />

        <div className="bg-brand-surface border border-brand-border rounded-md p-6 md:sticky md:top-6">
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-brand-text">
              Images du produit (optionnel)
            </h2>
            <p className="text-xs text-brand-text-muted mt-1">
              Vous pouvez ajouter les images maintenant, ou les téléverser
              plus tard depuis la page d&apos;édition.
            </p>
          </div>
          <div className="space-y-4">
            <ImagePicker
              label="Face avant"
              file={frontFile}
              onSelect={setFrontFile}
              disabled={submitting}
            />
            <ImagePicker
              label="Face arrière"
              file={backFile}
              onSelect={setBackFile}
              disabled={submitting}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
