/* eslint-disable @next/next/no-img-element */
"use client";
import { useState } from "react";
import type { Product } from "@/lib/types";

interface Props {
  product: Product;
  compact?: boolean;
  modalLayout?: boolean;
}

export function ProductGallery({ product, compact = false, modalLayout = false }: Props) {
  const { image_front_url, image_back_url, name } = product;

  const images: Array<{ url: string | null; label: string }> = [
    { url: image_front_url, label: "Vue avant" },
    ...(image_back_url ? [{ url: image_back_url, label: "Vue arrière" }] : []),
  ];

  const available = images.filter((img) => img.url !== null);

  const [selected, setSelected] = useState(0);

  if (available.length === 0) {
    return (
      <div
        className={`relative w-full bg-brand-bg flex items-center justify-center ${
          compact ? "aspect-[4/3] max-md:max-h-28" : "aspect-square"
        } ${modalLayout ? "max-md:col-span-2" : ""}`}
      >
        <span className="text-brand-text-muted text-sm">Image non disponible</span>
      </div>
    );
  }

  return (
    <div className={modalLayout ? "contents md:flex md:flex-col md:gap-3" : "flex flex-col gap-3"}>
      {/* Main image */}
      <div
        className={`relative w-full bg-brand-bg overflow-hidden ${
          compact ? "aspect-[4/3] max-md:max-h-44" : "aspect-square"
        } ${modalLayout ? "max-md:col-span-2" : ""}`}
      >
        <img
          src={available[selected].url!}
          alt={`${name} - ${available[selected].label}`}
          className={`w-full h-full ${compact ? "object-contain" : "object-cover"}`}
        />
      </div>

      {/* Thumbnails */}
      {available.length > 1 && (
        <div className="flex flex-wrap md:flex-nowrap gap-1 md:gap-2 max-md:col-start-2 max-md:row-start-2 max-md:self-start">
          {available.map((img, i) => (
            <button
              key={i}
              type="button"
              onClick={() => setSelected(i)}
              className={`relative w-12 h-12 md:w-16 md:h-16 border-2 overflow-hidden ${
                i === selected ? "border-brand-orange" : "border-brand-border"
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
        <div className="hidden md:flex gap-2">
          {available.map((img, i) => (
            <span
              key={i}
              className={`text-xs ${
                i === selected ? "text-brand-text font-medium" : "text-brand-text-muted"
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
