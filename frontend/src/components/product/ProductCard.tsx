"use client";

/* eslint-disable @next/next/no-img-element */
import { useState } from "react";
import type { Product } from "@/lib/types";
import { ProductModal } from "./ProductModal";

interface Props {
  product: Product;
}

export default function ProductCard({ product }: Props) {
  const {
    brand,
    name,
    specification,
    price,
    in_stock,
    image_front_url,
    image_back_url,
  } = product;

  const [hovered, setHovered] = useState(false);
  const [open, setOpen] = useState(false);

  const hasFront = !!image_front_url;
  const hasBack = !!image_back_url;
  const showBack = hasBack && hasFront && hovered;

  const formattedPrice = price.toLocaleString("fr-DZ") + " DA";

  return (
    <div
      className="group border border-neutral-200 bg-white relative cursor-pointer"
      onClick={() => setOpen(true)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Image area */}
      <div className="relative aspect-square w-full bg-neutral-100 overflow-hidden">
        {hasFront || hasBack ? (
          <img
            src={showBack ? image_back_url! : image_front_url!}
            alt={name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <span className="text-neutral-400 text-xs">Image non disponible</span>
          </div>
        )}

        {/* Out-of-stock badge */}
        {!in_stock && (
          <span className="absolute top-2 right-2 text-xs px-2 py-0.5 bg-white border border-neutral-200 rounded text-neutral-600">
            Rupture
          </span>
        )}

        {/* Hover button */}
        <button
          type="button"
          disabled={!in_stock}
          onClick={(e) => {
            e.stopPropagation();
            setOpen(true);
          }}
          className="absolute bottom-2 left-2 right-2 bg-neutral-900 text-white text-xs font-medium py-1.5 rounded-md opacity-0 md:group-hover:opacity-100 transition-opacity disabled:bg-neutral-300 disabled:cursor-not-allowed"
        >
          {in_stock ? "Plus de détails" : "Indisponible"}
        </button>
      </div>

      {/* Card body */}
      <div className="p-2.5 flex flex-col gap-0.5">
        <p className="text-xs uppercase tracking-wide text-neutral-500">
          {brand}
        </p>
        <p className="text-sm font-medium text-neutral-900 line-clamp-1">
          {name}
        </p>
        <p className="text-xs text-neutral-500 line-clamp-1">
          {specification}
        </p>
        <p className="mt-1 text-base font-semibold text-neutral-900">
          {formattedPrice}
        </p>
      </div>

      {open && <ProductModal product={product} onClose={() => setOpen(false)} />}
    </div>
  );
}
