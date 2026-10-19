"use client";

import Link from "next/link";

export default function AdminDashboardPage() {
  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h2 className="text-2xl font-semibold text-neutral-900 mb-6">
        Tableau de bord
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link
          href="/admin/stock"
          className="block bg-white border border-neutral-200 rounded-md p-6 hover:border-neutral-400 transition-colors"
        >
          <h3 className="font-medium text-neutral-900 mb-1">
            Stock &amp; Inventaire
          </h3>
          <p className="text-sm text-neutral-500 mb-4">
            Gérez les produits, les prix, les quantités et les images.
          </p>
          <span className="text-sm text-neutral-700 underline">
            Gérer le stock →
          </span>
        </Link>

        <div className="bg-white border border-neutral-200 rounded-md p-6">
          <h3 className="font-medium text-neutral-900 mb-1">Commandes</h3>
          <p className="text-sm text-neutral-500 mb-4">
            Consultez, confirmez et annulez les commandes clients.
          </p>
          <span className="text-xs text-neutral-400">
            Disponible à une étape ultérieure.
          </span>
        </div>
      </div>
    </div>
  );
}
