"use client";

import { Trash2 } from "lucide-react";
import type { CartItem } from "@/lib/cart";
import { useCart } from "./CartProvider";

function formatDA(n: number): string {
  return `${n.toLocaleString("fr-DZ")} DA`;
}

export function CartItemRow({ item }: { item: CartItem }) {
  const { updateQty, removeItem } = useCart();

  return (
    <li className="flex gap-3 px-4 py-3">
      {/* Image */}
      <div className="w-16 h-16 bg-neutral-100 flex-shrink-0 relative border border-neutral-200">
        {item.image_front_url ? (
          // eslint-disable-next-line @next/next/no-img-element -- remote URLs, next.config.ts can't be changed
          <img src={item.image_front_url} alt={item.name} className="absolute inset-0 w-full h-full object-cover" />
        ) : (
          <span className="absolute inset-0 flex items-center justify-center text-[10px] text-neutral-400">—</span>
        )}
      </div>

      {/* Info + controls */}
      <div className="flex-1 min-w-0">
        <p className="text-xs uppercase tracking-wide text-neutral-500">{item.brand}</p>
        <p className="text-sm text-neutral-900 truncate">{item.name}</p>
        {item.size && <p className="text-xs text-neutral-500 mt-0.5">{item.size}</p>}
        <p className="text-sm font-medium text-neutral-900 mt-1">{formatDA(item.price)}</p>

        <div className="flex items-center justify-between mt-2">
          <div className="flex items-center border border-neutral-300 rounded-md">
            <button
              type="button"
              onClick={() => updateQty(item.category, item.id, item.quantity - 1)}
              disabled={item.quantity <= 1}
              className="w-7 h-7 flex items-center justify-center hover:bg-neutral-100 disabled:opacity-40"
              aria-label="Diminuer"
            >
              −
            </button>
            <span className="w-8 text-center text-sm">{item.quantity}</span>
            <button
              type="button"
              onClick={() => updateQty(item.category, item.id, item.quantity + 1)}
              className="w-7 h-7 flex items-center justify-center hover:bg-neutral-100"
              aria-label="Augmenter"
            >
              +
            </button>
          </div>

          <button
            type="button"
            onClick={() => removeItem(item.category, item.id)}
            aria-label="Retirer"
            className="text-neutral-400 hover:text-red-600"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </li>
  );
}
