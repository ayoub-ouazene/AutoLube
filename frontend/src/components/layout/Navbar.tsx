import Link from "next/link";
import { ShoppingCart } from "lucide-react";

export default function Navbar() {
  return (
    <header className="bg-white border-b border-neutral-200">
      {/* Utility strip */}
      <div className="max-w-7xl mx-auto px-4 flex items-center justify-between py-1.5">
        <span className="text-xs text-neutral-500">Livraison en Algérie</span>
        <div className="flex items-center gap-4">
          <Link href="/contact" className="text-xs text-neutral-500 hover:text-neutral-900 transition-colors">
            Contact
          </Link>
          <Link href="/about" className="text-xs text-neutral-500 hover:text-neutral-900 transition-colors">
            À propos
          </Link>
        </div>
      </div>

      {/* Main navigation bar */}
      <div className="max-w-7xl mx-auto px-4 flex items-center justify-between py-3 gap-6">
        {/* Brand */}
        <Link
          href="/"
          className="text-base font-bold uppercase tracking-widest text-neutral-900 shrink-0"
        >
          AUTOLUBE
        </Link>

        {/* Products link */}
        <Link
          href="/products"
          className="text-sm font-medium text-neutral-900 hover:text-neutral-600"
        >
          Produits
        </Link>

        {/* Cart icon */}
        <div className="relative shrink-0">
          <ShoppingCart size={20} className="text-neutral-700" />
          <span className="absolute -top-1.5 -right-1.5 flex items-center justify-center w-4 h-4 text-[10px] font-medium bg-neutral-900 text-white rounded-full">
            0
          </span>
        </div>
      </div>
    </header>
  );
}
