"use client";

import {
  type ChangeEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { useAdminAuth } from "./AdminAuthProvider";
import { useConfirm } from "./ConfirmProvider";
import {
  type AdminStockItem,
  type ImagePosition,
  type StockCategory,
  deleteStockImage,
  uploadStockImage,
} from "@/lib/adminStock";

const MAX_BYTES = 5 * 1024 * 1024;
const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const ACCEPT_ATTR = "image/jpeg,image/png,image/webp";

function validateFile(file: File): string | null {
  if (!ALLOWED_TYPES.includes(file.type)) {
    return "Format non supporté. Utilisez JPG, PNG ou WEBP.";
  }
  if (file.size > MAX_BYTES) {
    return "Fichier trop volumineux (max 5 MB).";
  }
  return null;
}

type SectionProps = {
  position: ImagePosition;
  label: string;
  currentUrl: string | null;
  category: StockCategory;
  productId: number;
  onUpdated: (item: AdminStockItem) => void;
};

function ImageSection({
  position,
  label,
  currentUrl,
  category,
  productId,
  onUpdated,
}: SectionProps) {
  const { handleApiError } = useAdminAuth();
  const confirm = useConfirm();
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const clearSelection = useCallback(() => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setFile(null);
    setPreviewUrl(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  }, [previewUrl]);

  const handleSelect = (event: ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0];
    if (!selected) return;
    const validationError = validateFile(selected);
    if (validationError) {
      setError(validationError);
      if (inputRef.current) inputRef.current.value = "";
      return;
    }
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setFile(selected);
    setPreviewUrl(URL.createObjectURL(selected));
    setError(null);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const updated = await uploadStockImage(
        category,
        productId,
        position,
        file
      );
      onUpdated(updated);
      clearSelection();
    } catch (err) {
      const message = handleApiError(err);
      if (message) setError(message);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async () => {
    const confirmed = await confirm(
      `L'image « ${label.toLowerCase()} » sera définitivement supprimée.`,
      {
        title: `Supprimer l'image ${label.toLowerCase()} ?`,
        confirmLabel: "Supprimer",
        cancelLabel: "Annuler",
        danger: true,
      }
    );
    if (!confirmed) return;

    setDeleting(true);
    setError(null);
    try {
      const updated = await deleteStockImage(
        category,
        productId,
        position
      );
      onUpdated(updated);
    } catch (err) {
      const message = handleApiError(err);
      if (message) setError(message);
    } finally {
      setDeleting(false);
    }
  };

  const displayUrl = previewUrl ?? currentUrl;
  const hasExistingImage = !!currentUrl;
  const isBusy = uploading || deleting;

  return (
    <div className="border border-neutral-200 rounded-md p-4">
      <h3 className="text-sm font-medium text-neutral-900 mb-3">{label}</h3>
      <div className="flex items-start gap-4">
        <div className="w-32 h-32 border border-neutral-200 rounded bg-neutral-50 flex items-center justify-center overflow-hidden shrink-0">
          {displayUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={displayUrl}
              alt={label}
              className="w-full h-full object-cover"
            />
          ) : (
            <span className="text-xs text-neutral-400">Aucune image</span>
          )}
        </div>
        <div className="flex-1 min-w-0 space-y-2">
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPT_ATTR}
            className="hidden"
            onChange={handleSelect}
            disabled={isBusy}
          />
          {previewUrl ? (
            <>
              <p className="text-xs text-neutral-600">
                Aperçu local — cliquez sur Uploader pour enregistrer.
              </p>
              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={handleUpload}
                  disabled={isBusy}
                  className="text-sm bg-neutral-900 text-white px-3 py-1.5 rounded hover:bg-neutral-800 disabled:bg-neutral-400"
                >
                  {uploading ? "Envoi…" : "Uploader"}
                </button>
                <button
                  type="button"
                  onClick={clearSelection}
                  disabled={isBusy}
                  className="text-sm border border-neutral-300 px-3 py-1.5 rounded hover:bg-neutral-100 disabled:opacity-40"
                >
                  Annuler
                </button>
              </div>
            </>
          ) : (
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={() => inputRef.current?.click()}
                disabled={isBusy}
                className="text-sm border border-neutral-300 px-3 py-1.5 rounded hover:bg-neutral-100 disabled:opacity-40"
              >
                {hasExistingImage ? "Remplacer" : "Choisir une image"}
              </button>
              {hasExistingImage && (
                <button
                  type="button"
                  onClick={handleDelete}
                  disabled={isBusy}
                  className="text-sm border border-red-200 text-red-700 px-3 py-1.5 rounded hover:bg-red-50 disabled:opacity-40"
                >
                  {deleting ? "Suppression…" : "Supprimer"}
                </button>
              )}
            </div>
          )}
          {error && (
            <p className="text-xs text-red-600" role="alert">
              {error}
            </p>
          )}
          <p className="text-xs text-neutral-500">
            JPG, PNG ou WEBP — max 5 MB.
          </p>
        </div>
      </div>
    </div>
  );
}

export function ImageManager({
  item,
  onUpdated,
}: {
  item: AdminStockItem;
  onUpdated: (item: AdminStockItem) => void;
}) {
  return (
    <div className="bg-white border border-neutral-200 rounded-md p-6">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-neutral-900">
          Images du produit
        </h2>
        <p className="text-xs text-neutral-500 mt-1">
          Face avant affichée par défaut. Face arrière affichée au survol sur
          ordinateur.
        </p>
      </div>
      <div className="space-y-4">
        <ImageSection
          position="front"
          label="Face avant"
          currentUrl={item.image_front_url}
          category={item.category}
          productId={item.id}
          onUpdated={onUpdated}
        />
        <ImageSection
          position="back"
          label="Face arrière"
          currentUrl={item.image_back_url}
          category={item.category}
          productId={item.id}
          onUpdated={onUpdated}
        />
      </div>
    </div>
  );
}
