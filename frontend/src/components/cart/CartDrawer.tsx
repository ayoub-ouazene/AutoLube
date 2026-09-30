"use client";

import { useEffect } from "react";
import Link from "next/link";
import { X } from "lucide-react";
import { useCart } from "./CartProvider";
import { CartItemRow } from "./CartItemRow";

function formatDA(n: number): string {
  return `${n.toLocaleString("fr-DZ")} DA`;
}

export function CartDrawer() {
  const { isOpen, closeCart, items, totalPrice, totalItems } = useCart();

  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeCart();
    };
    window.addEventListener("keydown", handler);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", handler);
      document.body.style.overflow = prev;
    };
  }, [isOpen, closeCart]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex justify-end"
      onClick={closeCart}
      aria-modal="true"
      role="dialog"
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />

      {/* Panel */}
      <div
        className="relative bg-white w-full max-w-md h-full flex flex-col shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-200">
          <h2 className="text-base font-semibold text-neutral-900">
            Panier {totalItems > 0 && <span className="text-neutral-500 font-normal">({totalItems})</span>}
          </h2>
          <button
            type="button"
            onClick={closeCart}
            aria-label="Fermer"
            className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-neutral-100"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto">
          {items.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full px-6 text-center">
              <p className="text-sm text-neutral-500">Votre panier est vide.</p>
              <Link
                href="/products"
                onClick={closeCart}
                className="mt-4 text-sm text-neutral-900 underline underline-offset-4"
              >
                Parcourir le catalogue
              </Link>
            </div>
          ) : (
            <ul className="divide-y divide-neutral-200">
              {items.map((it) => (
                <CartItemRow key={`${it.category}-${it.id}`} item={it} />
              ))}
            </ul>
          )}
        </div>

        {/* Footer */}
        {items.length > 0 && (
          <div className="border-t border-neutral-200 px-4 py-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-neutral-500">Sous-total</span>
              <span className="text-lg font-semibold text-neutral-900">
                {formatDA(totalPrice)}
              </span>
            </div>
            <Link
              href="/checkout"
              onClick={closeCart}
              className="block w-full text-center px-6 py-3 bg-neutral-900 text-white text-sm font-medium rounded-md hover:bg-neutral-800 transition-colors"
            >
              Passer la commande
            </Link>
            <button
              type="button"
              onClick={closeCart}
              className="block w-full text-center mt-2 px-6 py-2 text-sm text-neutral-600 hover:text-neutral-900"
            >
              Continuer mes achats
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
