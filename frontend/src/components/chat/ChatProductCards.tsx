"use client";

import { useState } from "react";
import type { ChatProduct } from "@/lib/chat";
import type { Product } from "@/lib/types";
import { ProductModal } from "@/components/product/ProductModal";

function formatDA(n: number): string {
  return `${n.toLocaleString("fr-DZ")} DA`;
}

export function ChatProductCards({ products }: { products: ChatProduct[] }) {
  const [selected, setSelected] = useState<ChatProduct | null>(null);

  return (
    <>
      <div className="flex gap-2 overflow-x-auto pb-1 mt-2 -mx-1 px-1">
        {products.map((p) => (
          <button
            key={`${p.category}-${p.id}`}
            type="button"
            onClick={() => setSelected(p)}
            className="w-40 shrink-0 border border-neutral-200 bg-white rounded-md overflow-hidden cursor-pointer text-left"
          >
            <div className="aspect-square bg-neutral-100 relative">
              {p.image_front_url ? (
                // eslint-disable-next-line @next/next/no-img-element -- remote URLs, next.config.ts can't be changed
                <img
                  src={p.image_front_url}
                  alt={p.name}
                  className="absolute inset-0 w-full h-full object-cover"
                />
              ) : (
                <span className="absolute inset-0 flex items-center justify-center text-neutral-400">
                  —
                </span>
              )}
            </div>
            <div className="p-2">
              <p className="text-[10px] uppercase tracking-wide text-neutral-500">
                {p.brand}
              </p>
              <p className="text-xs text-neutral-900 truncate">{p.name}</p>
              <p className="text-sm font-medium text-neutral-900 mt-1">
                {formatDA(p.price)}
              </p>
            </div>
          </button>
        ))}
      </div>

      {selected && (
        <ProductModal
          product={selected as unknown as Product}
          onClose={() => setSelected(null)}
        />
      )}
    </>
  );
}
