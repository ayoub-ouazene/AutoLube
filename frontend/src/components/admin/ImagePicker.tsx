"use client";

import {
  type ChangeEvent,
  useEffect,
  useRef,
  useState,
} from "react";

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

export function ImagePicker({
  label,
  file,
  onSelect,
  disabled,
}: {
  label: string;
  file: File | null;
  onSelect: (file: File | null) => void;
  disabled?: boolean;
}) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!file) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- clear derived preview
      setPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const handleSelect = (event: ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0];
    if (!selected) return;
    const validationError = validateFile(selected);
    if (validationError) {
      setError(validationError);
      if (inputRef.current) inputRef.current.value = "";
      return;
    }
    setError(null);
    onSelect(selected);
  };

  const handleClear = () => {
    onSelect(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div className="border border-neutral-200 rounded-md p-4">
      <h3 className="text-sm font-medium text-neutral-900 mb-3">{label}</h3>
      <div className="flex items-start gap-4">
        <div className="w-32 h-32 border border-neutral-200 rounded bg-neutral-50 flex items-center justify-center overflow-hidden shrink-0">
          {previewUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={previewUrl}
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
            disabled={disabled}
          />
          {file ? (
            <>
              <p className="text-xs text-neutral-600 truncate">{file.name}</p>
              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={() => inputRef.current?.click()}
                  disabled={disabled}
                  className="text-sm border border-neutral-300 px-3 py-1.5 rounded hover:bg-neutral-100 disabled:opacity-40"
                >
                  Changer
                </button>
                <button
                  type="button"
                  onClick={handleClear}
                  disabled={disabled}
                  className="text-sm border border-neutral-300 px-3 py-1.5 rounded hover:bg-neutral-100 disabled:opacity-40"
                >
                  Retirer
                </button>
              </div>
            </>
          ) : (
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              disabled={disabled}
              className="text-sm border border-neutral-300 px-3 py-1.5 rounded hover:bg-neutral-100 disabled:opacity-40"
            >
              Choisir une image
            </button>
          )}
          {error && (
            <p className="text-xs text-red-600" role="alert">
              {error}
            </p>
          )}
          <p className="text-xs text-neutral-500">
            JPG, PNG ou WEBP — max 5 MB. Optionnel.
          </p>
        </div>
      </div>
    </div>
  );
}
