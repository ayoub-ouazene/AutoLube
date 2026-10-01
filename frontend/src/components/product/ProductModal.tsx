"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import type { Product } from "@/lib/types";
import { ProductGallery } from "./ProductGallery";
import { useCart } from "@/components/cart/CartProvider";

function formatDA(n: number): string {
  return `${n.toLocaleString("fr-DZ")} DA`;
}

export function ProductModal({
  product,
  onClose,
  openDrawerOnAdd = true,
}: {
  product: Product;
  onClose: () => void;
  openDrawerOnAdd?: boolean;
}) {
  const { addItem } = useCart();
  const [qty, setQty] = useState(1);

  // Lock body scroll
  useEffect(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, []);

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="relative bg-white max-w-4xl w-full max-h-[92vh] rounded-md overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          type="button"
          onClick={onClose}
          aria-label="Fermer"
          className="absolute top-3 right-3 w-8 h-8 flex items-center justify-center rounded-full hover:bg-neutral-100 z-10"
        >
          <X size={18} strokeWidth={2} />
        </button>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6 p-4 md:p-5">
          {/* LEFT: gallery */}
          <div>
            <ProductGallery product={product} />
          </div>

          {/* RIGHT: info */}
          <div>
            <p className="text-xs uppercase tracking-wide text-neutral-500">
              {product.brand}
            </p>
            <h2 className="text-xl font-semibold text-neutral-900 mt-1">
              {product.name}
            </h2>

            {product.in_stock ? (
              <span className="inline-block mt-3 text-xs px-2 py-0.5 border border-emerald-300 text-emerald-700 rounded">
                Disponible
              </span>
            ) : (
              <span className="inline-block mt-3 text-xs px-2 py-0.5 border border-neutral-300 text-neutral-500 rounded">
                Rupture de stock
              </span>
            )}

            <p className="text-2xl font-semibold text-neutral-900 mt-3">
              {formatDA(product.price)}
            </p>

            <dl className="mt-4 border-t border-neutral-200 pt-3 grid grid-cols-2 gap-y-2 text-sm">
              <dt className="text-neutral-500">Viscosité</dt>
              <dd className="text-neutral-900">{product.viscosity ?? "—"}</dd>
              <dt className="text-neutral-500">Conditionnement</dt>
              <dd className="text-neutral-900">{product.size ?? "—"}</dd>
              <dt className="text-neutral-500">Spécification</dt>
              <dd className="text-neutral-900">{product.specification || "—"}</dd>
            </dl>

            {/* Quantity selector */}
            <div className="mt-4 flex items-center gap-3">
              <span className="text-sm text-neutral-700">Quantité</span>
              <div className="flex items-center border border-neutral-300 rounded-md">
                <button
                  type="button"
                  onClick={() => setQty((q) => Math.max(1, q - 1))}
                  className="w-8 h-8 flex items-center justify-center hover:bg-neutral-100 disabled:opacity-50"
                  disabled={qty <= 1 || !product.in_stock}
                  aria-label="Diminuer la quantité"
                >
                  −
                </button>
                <span className="w-10 text-center text-sm font-medium">{qty}</span>
                <button
                  type="button"
                  onClick={() => setQty((q) => q + 1)}
                  className="w-8 h-8 flex items-center justify-center hover:bg-neutral-100 disabled:opacity-50"
                  disabled={!product.in_stock}
                  aria-label="Augmenter la quantité"
                >
                  +
                </button>
              </div>
            </div>

            {/* Add to cart */}
            <button
              type="button"
              disabled={!product.in_stock}
              onClick={() => {
                addItem(product, qty, { openDrawer: openDrawerOnAdd });
                onClose();
              }}
              className="mt-4 w-full px-6 py-2.5 bg-neutral-900 text-white text-sm font-medium rounded-md hover:bg-neutral-800 transition-colors disabled:bg-neutral-300 disabled:cursor-not-allowed"
            >
              {product.in_stock ? "Ajouter au panier" : "Indisponible"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
