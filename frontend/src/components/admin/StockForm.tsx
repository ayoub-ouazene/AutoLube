"use client";

import { useState, type FormEvent } from "react";
import {
  type AdminStockItem,
  STOCK_CATEGORIES,
  type StockCategory,
  type StockCreatePayload,
} from "@/lib/adminStock";

type FormValues = {
  category: StockCategory;
  brand: string;
  specification: string;
  viscosity: string;
  size: string;
  price: string;
  quantity: string;
  category_type: string;
};

function itemToForm(item: AdminStockItem): FormValues {
  return {
    category: item.category,
    brand: item.brand,
    specification: item.specification,
    viscosity: item.viscosity ?? "",
    size: item.size ?? "",
    price: String(item.price),
    quantity: String(item.quantity),
    category_type: "",
  };
}

export function StockForm({
  mode,
  initial,
  onSubmit,
  onCancel,
  submitting,
  errorMessage,
}: {
  mode: "create" | "edit";
  initial?: AdminStockItem;
  onSubmit: (payload: StockCreatePayload | Record<string, unknown>) => void;
  onCancel: () => void;
  submitting: boolean;
  errorMessage: string | null;
}) {
  const [values, setValues] = useState<FormValues>(
    initial
      ? itemToForm(initial)
      : {
          category: "engine_oil",
          brand: "",
          specification: "",
          viscosity: "",
          size: "",
          price: "",
          quantity: "0",
          category_type: "",
        }
  );
  const [validationError, setValidationError] = useState<string | null>(null);

  const showsOilFields =
    values.category === "engine_oil" || values.category === "gearbox_oil";
  const isAdditional = values.category === "additional";

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    if (!values.brand.trim()) {
      setValidationError("La marque est requise.");
      return;
    }
    if (!values.specification.trim()) {
      setValidationError("La spécification est requise.");
      return;
    }
    const priceNum = parseFloat(values.price);
    if (isNaN(priceNum) || priceNum < 0) {
      setValidationError("Prix invalide.");
      return;
    }
    const qtyNum = parseInt(values.quantity, 10);
    if (isNaN(qtyNum) || qtyNum < 0) {
      setValidationError("Quantité invalide.");
      return;
    }
    if (showsOilFields) {
      if (!values.viscosity.trim()) {
        setValidationError("La viscosité est requise pour cette catégorie.");
        return;
      }
      if (!values.size.trim()) {
        setValidationError("La taille est requise pour cette catégorie.");
        return;
      }
    }
    if (isAdditional && !values.category_type.trim()) {
      setValidationError(
        "Le type de produit est requis pour un produit additionnel."
      );
      return;
    }

    const payload: StockCreatePayload = {
      category: values.category,
      brand: values.brand.trim(),
      specification: values.specification.trim(),
      price: priceNum,
      quantity: qtyNum,
    };
    if (showsOilFields) {
      payload.viscosity = values.viscosity.trim();
      payload.size = values.size.trim();
    }
    if (isAdditional) {
      payload.category_type = values.category_type.trim();
    }

    onSubmit(payload);
  };

  const set = <K extends keyof FormValues>(key: K, value: FormValues[K]) =>
    setValues((prev) => ({ ...prev, [key]: value }));

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white border border-neutral-200 rounded-md p-6 space-y-4"
    >
      <div>
        <label className="block text-sm font-medium text-neutral-700 mb-1">
          Catégorie *
        </label>
        <select
          value={values.category}
          onChange={(e) => set("category", e.target.value as StockCategory)}
          disabled={mode === "edit"}
          className="w-full border border-neutral-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-neutral-900 disabled:bg-neutral-100"
        >
          {STOCK_CATEGORIES.map((category) => (
            <option key={category.value} value={category.value}>
              {category.label}
            </option>
          ))}
        </select>
        {mode === "edit" && (
          <p className="text-xs text-neutral-500 mt-1">
            La catégorie ne peut pas être modifiée.
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">
            Marque *
          </label>
          <input
            type="text"
            value={values.brand}
            onChange={(e) => set("brand", e.target.value)}
            maxLength={64}
            className="w-full border border-neutral-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-neutral-900"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">
            Spécification *
          </label>
          <input
            type="text"
            value={values.specification}
            onChange={(e) => set("specification", e.target.value)}
            maxLength={500}
            placeholder="ex: VW 504.00, PSA B71 2290"
            className="w-full border border-neutral-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-neutral-900"
          />
        </div>

        {showsOilFields && (
          <>
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Viscosité *
              </label>
              <input
                type="text"
                value={values.viscosity}
                onChange={(e) => set("viscosity", e.target.value)}
                maxLength={16}
                placeholder="ex: 5W-30"
                className="w-full border border-neutral-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-neutral-900"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Taille *
              </label>
              <input
                type="text"
                value={values.size}
                onChange={(e) => set("size", e.target.value)}
                maxLength={16}
                placeholder="ex: 5L"
                className="w-full border border-neutral-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-neutral-900"
              />
            </div>
          </>
        )}

        {isAdditional && (
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-neutral-700 mb-1">
              Type de produit *
            </label>
            <input
              type="text"
              value={values.category_type}
              onChange={(e) => set("category_type", e.target.value)}
              maxLength={64}
              placeholder="ex: liquide de frein, additif"
              className="w-full border border-neutral-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-neutral-900"
            />
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">
            Prix (DA) *
          </label>
          <input
            type="number"
            step="1"
            min="0"
            value={values.price}
            onChange={(e) => set("price", e.target.value)}
            className="w-full border border-neutral-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-neutral-900"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">
            Quantité *
          </label>
          <div className="flex items-stretch rounded border border-neutral-300 focus-within:border-neutral-900">
            <button
              type="button"
              onClick={() =>
                set(
                  "quantity",
                  String(Math.max(0, (parseInt(values.quantity, 10) || 0) - 1))
                )
              }
              disabled={submitting || (parseInt(values.quantity, 10) || 0) <= 0}
              aria-label="Diminuer la quantité"
              className="w-10 border-r border-neutral-300 text-lg text-neutral-700 hover:bg-neutral-100 disabled:cursor-not-allowed disabled:opacity-40"
            >
              −
            </button>
            <input
              type="number"
              step="1"
              min="0"
              value={values.quantity}
              onChange={(e) => set("quantity", e.target.value)}
              className="min-w-0 flex-1 px-3 py-2 text-center text-sm focus:outline-none"
            />
            <button
              type="button"
              onClick={() =>
                set("quantity", String((parseInt(values.quantity, 10) || 0) + 1))
              }
              disabled={submitting}
              aria-label="Augmenter la quantité"
              className="w-10 border-l border-neutral-300 text-lg text-neutral-700 hover:bg-neutral-100 disabled:cursor-not-allowed disabled:opacity-40"
            >
              +
            </button>
          </div>
        </div>
      </div>

      {(validationError || errorMessage) && (
        <p className="text-sm text-red-600">
          {validationError ?? errorMessage}
        </p>
      )}

      <div className="flex items-center gap-3 pt-2">
        <button
          type="submit"
          disabled={submitting}
          className="bg-neutral-900 text-white text-sm font-medium px-4 py-2 rounded hover:bg-neutral-800 disabled:bg-neutral-400"
        >
          {submitting
            ? "Enregistrement…"
            : mode === "create"
              ? "Créer le produit"
              : "Enregistrer"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={submitting}
          className="text-sm text-neutral-700 px-4 py-2 rounded hover:bg-neutral-100 disabled:opacity-40"
        >
          Annuler
        </button>
      </div>
    </form>
  );
}
