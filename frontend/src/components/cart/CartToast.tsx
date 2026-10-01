"use client";

import { useEffect } from "react";
import { Check } from "lucide-react";
import { useCart } from "./CartProvider";

export function CartToast() {
  const { lastAdded, clearLastAdded, openCart } = useCart();

  useEffect(() => {
    if (!lastAdded) return;
    const t = setTimeout(() => clearLastAdded(), 2500);
    return () => clearTimeout(t);
  }, [lastAdded, clearLastAdded]);

  if (!lastAdded) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed bottom-24 left-1/2 -translate-x-1/2 z-[90] bg-neutral-900 text-white text-sm rounded-md shadow-lg px-4 py-3 flex items-center gap-3 max-w-[calc(100vw-2rem)] animate-[toastIn_200ms_ease-out]"
    >
      <Check className="w-4 h-4 text-emerald-400 shrink-0" />
      <span className="truncate">
        <strong className="font-medium">{lastAdded.name}</strong> ajouté au panier
      </span>
      <button
        type="button"
        onClick={() => {
          clearLastAdded();
          openCart();
        }}
        className="text-xs underline underline-offset-2 whitespace-nowrap hover:text-neutral-300"
      >
        Voir le panier
      </button>
    </div>
  );
}
