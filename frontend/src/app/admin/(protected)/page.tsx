"use client";

import Link from "next/link";

export default function AdminDashboardPage() {
  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h2 className="text-2xl font-semibold text-brand-text mb-6">
        Tableau de bord
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link
          href="/admin/stock"
          className="block bg-brand-surface border border-brand-border rounded-md p-6 hover:border-brand-dark transition-colors"
        >
          <h3 className="font-medium text-brand-text mb-1">
            Stock &amp; Inventaire
          </h3>
          <p className="text-sm text-brand-text-muted mb-4">
            Gérez les produits, les prix, les quantités et les images.
          </p>
          <span className="text-sm text-brand-orange underline">
            Gérer le stock →
          </span>
        </Link>

        <Link
          href="/admin/orders"
          className="block bg-brand-surface border border-brand-border rounded-md p-6 hover:border-brand-dark transition-colors"
        >
          <h3 className="font-medium text-brand-text mb-1">Commandes</h3>
          <p className="text-sm text-brand-text-muted mb-4">
            Consultez, confirmez et annulez les commandes clients.
          </p>
          <span className="text-sm text-brand-orange underline">
            Voir les commandes →
          </span>
        </Link>
      </div>
    </div>
  );
}
