import Link from "next/link";
import { ArrowRight } from "lucide-react";

const categoryCards = [
  {
    title: "Huile moteur",
    description: "Huiles moteur toutes viscosités pour voitures et utilitaires.",
    href: "/products?category=engine_oil",
  },
  {
    title: "Huile de boîte",
    description: "Huiles de transmission, boîte manuelle et automatique.",
    href: "/products?category=gearbox_oil",
  },
  {
    title: "Filtres à huile",
    description: "Filtres compatibles avec les grandes marques du marché.",
    href: "/products?category=oil_filter",
  },
];

export default function HomePage() {
  return (
    <main className="max-w-7xl mx-auto px-4 py-10">
      {/* À propos section */}
      <section className="mb-10 border-b border-neutral-200 pb-8">
        <h2 className="text-lg font-medium text-neutral-900 mb-3">À propos d&apos;AutoLube</h2>
        <p className="text-sm text-neutral-600 max-w-2xl leading-relaxed">
          AutoLube est un distributeur algérien spécialisé dans la vente d&apos;huiles moteur,
          huiles de transmission et lubrifiants automobiles. Nous proposons un large choix
          de marques reconnues — Castrol, Total, Elf, Motul, Febi — pour les particuliers
          et les professionnels à travers l&apos;Algérie.
        </p>
      </section>

      {/* Catégories section */}
      <section>
        <h2 className="text-lg font-medium text-neutral-900 mb-4">Catégories</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {categoryCards.map((card) => (
            <Link
              key={card.href}
              href={card.href}
              className="flex items-start justify-between border border-neutral-200 rounded-md p-4 hover:bg-neutral-50 transition-colors"
            >
              <div>
                <p className="text-sm font-medium text-neutral-900 mb-1">{card.title}</p>
                <p className="text-xs text-neutral-500 leading-relaxed">{card.description}</p>
              </div>
              <ArrowRight size={16} className="text-neutral-400 shrink-0 mt-0.5 ml-3" />
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}