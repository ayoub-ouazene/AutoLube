import Link from "next/link";
import { Camera, Mail, MapPin, Phone, Truck } from "lucide-react";

export default function Footer() {
  return (
    <footer className="bg-brand-dark text-brand-text-inverse mt-12 px-4 py-12">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-8">
          {/* Brand blurb */}
          <div>
            <span className="heading-brand text-xl text-white">
              LubriStock
            </span>
            <p className="max-w-sm mt-3 text-brand-text-muted text-sm leading-relaxed">
              Lubrifiants automobiles et huiles de boîte pour toutes les
              marques. Livraison dans toute l&apos;Algérie.
            </p>
          </div>

          {/* Categories */}
          <div>
            <p className="text-sm font-semibold text-white mb-3 uppercase tracking-wide">
              Catégories
            </p>
            <ul>
              <li>
                <Link href="/products?category=engine_oil" className="block py-1 text-sm text-brand-text-muted hover:text-brand-orange transition-colors">
                  Huile moteur
                </Link>
              </li>
              <li>
                <Link href="/products?category=gearbox_oil" className="block py-1 text-sm text-brand-text-muted hover:text-brand-orange transition-colors">
                  Huile de boîte
                </Link>
              </li>
              <li>
                <Link href="/products?category=oil_filter" className="block py-1 text-sm text-brand-text-muted hover:text-brand-orange transition-colors">
                  Filtres à huile
                </Link>
              </li>
              <li>
                <Link href="/products?category=additional" className="block py-1 text-sm text-brand-text-muted hover:text-brand-orange transition-colors">
                  Autres produits
                </Link>
              </li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <p className="text-sm font-semibold text-white mb-3 uppercase tracking-wide">
              Contact
            </p>
            <ul className="text-sm text-brand-text-muted">
              <li className="flex items-center gap-2 py-1">
                <Phone size={15} className="shrink-0 text-brand-orange" />
                <a href="tel:+213555000000" className="hover:text-brand-orange transition-colors">
                  +213 5XX XX XX XX
                </a>
              </li>
              <li className="flex items-center gap-2 py-1">
                <Mail size={15} className="shrink-0 text-brand-orange" />
                <a href="mailto:contact@lubristock.dz" className="break-all hover:text-brand-orange transition-colors">
                  contact@lubristock.dz
                </a>
              </li>
              <li className="flex items-center gap-2 py-1">
                <MapPin size={15} className="shrink-0 text-brand-orange" />
                <span>Alger, Algérie</span>
              </li>
              <li className="flex items-center gap-2 py-1">
                <Camera size={15} className="shrink-0 text-brand-orange" />
                <a
                  href="https://instagram.com/lubristock"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-brand-orange transition-colors"
                >
                  @lubristock
                </a>
              </li>
              <li className="flex items-center gap-2 pt-2 text-xs">
                <Truck size={15} className="shrink-0 text-brand-orange" />
                <span>Livraison dans les 58 wilayas</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Copyright strip */}
        <div className="mt-10 pt-6 border-t border-brand-dark-light text-center text-xs text-brand-text-muted">
          © {new Date().getFullYear()} LubriStock. Tous droits réservés.
        </div>
      </div>
    </footer>
  );
}
