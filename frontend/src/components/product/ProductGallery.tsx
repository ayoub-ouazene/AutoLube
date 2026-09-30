/* eslint-disable @next/next/no-img-element */
"use client";
import { useState } from "react";
import type { Product } from "@/lib/types";

interface Props {
  product: Product;
}

export function ProductGallery({ product }: Props) {
  const { image_front_url, image_back_url, name } = product;

  const images: Array<{ url: string | null; label: string }> = [
    { url: image_front_url, label: "Vue avant" },
    ...(image_back_url ? [{ url: image_back_url, label: "Vue arrière" }] : []),
  ];

  const available = images.filter((img) => img.url !== null);

  const [selected, setSelected] = useState(0);

  if (available.length === 0) {
    return (
      <div className="relative aspect-square w-full bg-neutral-100 flex items-center justify-center">
        <span className="text-neutral-400 text-sm">Image non disponible</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Main image */}
      <div className="relative aspect-square w-full bg-neutral-100 overflow-hidden">
        <img
          src={available[selected].url!}
          alt={`${name} - ${available[selected].label}`}
          className="w-full h-full object-cover"
        />
      </div>

      {/* Thumbnails */}
      {available.length > 1 && (
        <div className="flex gap-2">
          {available.map((img, i) => (
            <button
              key={i}
              type="button"
              onClick={() => setSelected(i)}
              className={`relative w-16 h-16 border-2 overflow-hidden ${
                i === selected ? "border-neutral-900" : "border-neutral-200"
              }`}
            >
              <img
                src={img.url!}
                alt={img.label}
                className="w-full h-full object-cover"
              />
            </button>
          ))}
        </div>
      )}

      {/* Labels */}
      {available.length > 1 && (
        <div className="flex gap-2">
          {available.map((img, i) => (
            <span
              key={i}
              className={`text-xs ${
                i === selected ? "text-neutral-900 font-medium" : "text-neutral-400"
              }`}
            >
              {img.label}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
