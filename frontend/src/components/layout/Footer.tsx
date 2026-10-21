import Link from "next/link";

export default function Footer() {
  return (
    <footer className="border-t border-neutral-200 bg-neutral-50 mt-12">
      <div className="max-w-7xl mx-auto px-4 py-8 sm:py-10 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-8 sm:gap-x-10 text-sm">
        {/* Brand blurb */}
        <div className="sm:col-span-2 md:col-span-1">
          <p className="font-bold uppercase tracking-widest text-neutral-900 mb-3">
            AutoLube
          </p>
          <p className="max-w-sm text-neutral-600 leading-relaxed">
            Votre fournisseur d&apos;huiles et lubrifiants automobiles en
            Algérie. Castrol, Total, Elf, Motul et bien d&apos;autres marques.
          </p>
        </div>

        {/* Categories */}
        <div>
          <p className="text-xs uppercase tracking-wide text-neutral-500 mb-3">
            Catégories
          </p>
          <ul className="space-y-1.5">
            <li>
              <Link href="/products?category=engine_oil" className="text-neutral-600 hover:text-neutral-900">
                Huile moteur
              </Link>
            </li>
            <li>
              <Link href="/products?category=gearbox_oil" className="text-neutral-600 hover:text-neutral-900">
                Huile de boîte
              </Link>
            </li>
            <li>
              <Link href="/products?category=oil_filter" className="text-neutral-600 hover:text-neutral-900">
                Filtres à huile
              </Link>
            </li>
            <li>
              <Link href="/products?category=additional" className="text-neutral-600 hover:text-neutral-900">
                Autres produits
              </Link>
            </li>
          </ul>
        </div>

        {/* Contact */}
        <div>
          <p className="text-xs uppercase tracking-wide text-neutral-500 mb-3">
            Contact
          </p>
          <ul className="space-y-1.5 text-neutral-600 break-words">
            <li className="whitespace-nowrap">Tél : +213 XX XX XX XX</li>
            <li>Alger, Algérie</li>
            <li>contact@autolube.dz</li>
          </ul>
        </div>
      </div>

      {/* Copyright strip */}
      <div className="border-t border-neutral-200">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <p className="text-xs text-neutral-500">
            © 2026 AutoLube. Tous droits réservés.
          </p>
        </div>
      </div>
    </footer>
  );
}
