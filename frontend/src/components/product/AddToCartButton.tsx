"use client";

import { useState } from "react";
import type { Product } from "@/lib/types";
import { useCart } from "@/components/cart/CartProvider";

export function AddToCartButton({ product }: { product: Product }) {
  const { addItem } = useCart();
  const [qty, setQty] = useState(1);

  return (
    <div className="mt-6 flex flex-col sm:flex-row gap-3">
      <div className="flex items-center border border-neutral-300 rounded-md w-fit">
        <button
          type="button"
          onClick={() => setQty((q) => Math.max(1, q - 1))}
          disabled={qty <= 1}
          className="w-9 h-9 flex items-center justify-center hover:bg-neutral-100 disabled:opacity-40"
          aria-label="Diminuer"
        >
          −
        </button>
        <span className="w-10 text-center text-sm">{qty}</span>
        <button
          type="button"
          onClick={() => setQty((q) => q + 1)}
          className="w-9 h-9 flex items-center justify-center hover:bg-neutral-100"
          aria-label="Augmenter"
        >
          +
        </button>
      </div>

      <button
        type="button"
        disabled={!product.in_stock}
        onClick={() => addItem(product, qty)}
        className="flex-1 px-6 py-3 bg-neutral-900 text-white text-sm font-medium rounded-md hover:bg-neutral-800 transition-colors disabled:bg-neutral-300 disabled:cursor-not-allowed"
      >
        {product.in_stock ? "Ajouter au panier" : "Indisponible"}
      </button>
    </div>
  );
}
