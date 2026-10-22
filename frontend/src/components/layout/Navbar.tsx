"use client";

import Link from "next/link";
import { ShoppingCart } from "lucide-react";
import { usePathname } from "next/navigation";
import { useCart } from "@/components/cart/CartProvider";

export default function Navbar() {
  const { totalItems, openCart } = useCart();
  const pathname = usePathname();
  const productsActive = pathname.startsWith("/products");

  return (
    <header>
      {/* Main navigation bar */}
      <div className="bg-brand-surface text-brand-text border-y border-brand-orange/40">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between gap-6">
          <div className="flex items-center gap-8">
            {/* Brand */}
            <Link href="/" className="flex items-center gap-2 shrink-0">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/LubriStock.png"
                alt="LubriStock"
                className="h-9 sm:h-10 w-auto"
              />
            </Link>

            {/* Products link */}
            <Link
              href="/products"
              className={`text-sm transition-colors ${
                productsActive
                  ? "text-brand-orange font-semibold"
                  : "font-medium text-brand-text hover:text-brand-orange"
              }`}
            >
              Produits
            </Link>
          </div>

          {/* Cart icon */}
          <button
            type="button"
            onClick={openCart}
            aria-label="Ouvrir le panier"
            className="relative shrink-0 text-brand-text hover:text-brand-orange transition-colors"
          >
            <ShoppingCart size={20} />
            <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] flex items-center justify-center px-1 text-xs font-medium bg-brand-orange text-white rounded-full">
              {totalItems > 99 ? "99+" : totalItems}
            </span>
          </button>
        </div>
      </div>
    </header>
  );
}
