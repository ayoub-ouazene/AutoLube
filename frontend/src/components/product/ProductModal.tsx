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
  const hasTwoImages = Boolean(product.image_front_url && product.image_back_url);

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
        className="relative bg-brand-surface max-w-4xl w-full max-h-[92vh] rounded-md overflow-y-auto md:overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          type="button"
          onClick={onClose}
          aria-label="Fermer"
          className="absolute top-3 right-3 w-8 h-8 flex items-center justify-center rounded-full hover:bg-brand-bg z-10"
        >
          <X size={18} strokeWidth={2} />
        </button>

        <div className="grid grid-cols-[minmax(0,0.8fr)_minmax(0,1fr)] md:grid-cols-2 gap-x-3 gap-y-3 md:gap-6 p-3 md:p-5">
          {/* LEFT: gallery */}
          <div className="contents md:block md:min-w-0">
            <ProductGallery product={product} compact modalLayout />
          </div>

          {/* RIGHT: info */}
          <div className={`flex min-w-0 flex-col md:h-full ${hasTwoImages ? "" : "max-md:col-span-2"}`}>
            <p className="text-xs uppercase tracking-wide text-brand-text-muted">
              {product.brand}
            </p>
            <h2 className="text-base md:text-xl font-semibold text-brand-text mt-1">
              {product.name}
            </h2>

            {product.in_stock ? (
              <span className="inline-block self-start mt-3 text-xs px-2 py-0.5 border border-emerald-300 text-emerald-700 rounded">
                Disponible
              </span>
            ) : (
              <span className="inline-block self-start mt-3 text-xs px-2 py-0.5 border border-brand-border text-brand-text-muted rounded">
                Rupture de stock
              </span>
            )}

            <p className="text-lg md:text-2xl font-semibold text-brand-text mt-3">
              {formatDA(product.price)}
            </p>

            <dl className="hidden md:grid mt-4 border-t border-brand-border pt-3 grid-cols-2 gap-y-2 text-sm">
              <dt className="text-brand-text-muted">Viscosité</dt>
              <dd className="text-brand-text">{product.viscosity ?? "—"}</dd>
              <dt className="text-brand-text-muted">Conditionnement</dt>
              <dd className="text-brand-text">{product.size ?? "—"}</dd>
              <dt className="text-brand-text-muted">Spécification</dt>
              <dd className="text-brand-text">{product.specification || "—"}</dd>
            </dl>

            <div className="hidden md:block mt-auto pt-6">
              {/* Quantity selector */}
              <div className="flex items-center gap-3">
                <span className="text-sm text-brand-text">Quantité</span>
                <div className="flex items-center border border-brand-border rounded-md">
                  <button
                    type="button"
                    onClick={() => setQty((q) => Math.max(1, q - 1))}
                    className="w-8 h-8 flex items-center justify-center hover:bg-brand-bg disabled:opacity-50"
                    disabled={qty <= 1 || !product.in_stock}
                    aria-label="Diminuer la quantité"
                  >
                    −
                  </button>
                  <span className="w-10 text-center text-sm font-medium">{qty}</span>
                  <button
                    type="button"
                    onClick={() => setQty((q) => q + 1)}
                    className="w-8 h-8 flex items-center justify-center hover:bg-brand-bg disabled:opacity-50"
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
                className="mt-4 w-full px-6 py-2.5 bg-brand-orange text-white text-sm font-medium rounded-md hover:bg-brand-orange-hover transition-colors disabled:bg-neutral-300 disabled:cursor-not-allowed"
              >
                {product.in_stock ? "Ajouter au panier" : "Indisponible"}
              </button>
            </div>
          </div>

          <dl className="col-span-2 grid grid-cols-[auto_minmax(0,1fr)] gap-x-4 gap-y-1 border-t border-brand-border pt-2 text-xs break-words md:hidden">
            <dt className="text-brand-text-muted">Viscosité</dt>
            <dd className="text-brand-text">{product.viscosity ?? "—"}</dd>
            <dt className="text-brand-text-muted">Conditionnement</dt>
            <dd className="text-brand-text">{product.size ?? "—"}</dd>
            <dt className="text-brand-text-muted">Spécification</dt>
            <dd className="min-w-0 text-brand-text">{product.specification || "—"}</dd>
          </dl>

          <div className="col-span-2 border-t border-brand-border pt-2 md:hidden">
            <div className="flex items-center gap-2">
              <span className="text-xs text-brand-text">Quantité</span>
              <div className="flex items-center border border-brand-border rounded-md">
                <button
                  type="button"
                  onClick={() => setQty((q) => Math.max(1, q - 1))}
                  className="w-8 h-8 flex items-center justify-center hover:bg-brand-bg disabled:opacity-50"
                  disabled={qty <= 1 || !product.in_stock}
                  aria-label="Diminuer la quantité"
                >
                  −
                </button>
                <span className="w-10 text-center text-sm font-medium">{qty}</span>
                <button
                  type="button"
                  onClick={() => setQty((q) => q + 1)}
                  className="w-8 h-8 flex items-center justify-center hover:bg-brand-bg disabled:opacity-50"
                  disabled={!product.in_stock}
                  aria-label="Augmenter la quantité"
                >
                  +
                </button>
              </div>
            </div>
            <button
              type="button"
              disabled={!product.in_stock}
              onClick={() => {
                addItem(product, qty, { openDrawer: openDrawerOnAdd });
                onClose();
              }}
              className="mt-2 w-full px-2 py-2 bg-brand-orange text-white text-sm font-medium rounded-md hover:bg-brand-orange-hover transition-colors disabled:bg-neutral-300 disabled:cursor-not-allowed"
            >
              {product.in_stock ? "Ajouter au panier" : "Indisponible"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
