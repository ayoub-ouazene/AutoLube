"use client";

import Link from "next/link";
import { type AdminStockItem, categoryLabel } from "@/lib/adminStock";

function formatPrice(p: number): string {
  return (
    new Intl.NumberFormat("fr-DZ", {
      style: "decimal",
      maximumFractionDigits: 0,
    }).format(p) + " DA"
  );
}

export function StockTable({
  items,
  onDelete,
}: {
  items: AdminStockItem[];
  onDelete: (item: AdminStockItem) => void;
}) {
  return (
    <div className="bg-brand-surface border border-brand-border rounded-md overflow-x-auto">
      <table className="w-full min-w-[1050px] text-sm">
        <thead className="bg-brand-bg text-brand-text-muted text-xs uppercase">
          <tr>
            <th className="px-3 py-2 text-left">Image</th>
            <th className="px-3 py-2 text-left">Catégorie</th>
            <th className="px-3 py-2 text-left">Marque</th>
            <th className="px-3 py-2 text-left">Nom</th>
            <th className="px-3 py-2 text-left">Spécification</th>
            <th className="px-3 py-2 text-left">Viscosité</th>
            <th className="px-3 py-2 text-left">Taille</th>
            <th className="px-3 py-2 text-right">Prix</th>
            <th className="px-3 py-2 text-right">Quantité</th>
            <th className="px-3 py-2 text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr
              key={`${item.category}-${item.id}`}
              className="border-t border-brand-border hover:bg-brand-bg"
            >
              <td className="px-3 py-2">
                {item.image_front_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={item.image_front_url}
                    alt=""
                    className="w-10 h-10 object-cover rounded border border-brand-border"
                  />
                ) : (
                  <div className="w-10 h-10 rounded border border-brand-border bg-brand-bg" />
                )}
              </td>
              <td className="px-3 py-2 text-brand-text-muted">
                {categoryLabel(item.category)}
              </td>
              <td className="px-3 py-2 font-medium">{item.brand}</td>
              <td className="px-3 py-2 text-brand-text">{item.name}</td>
              <td className="px-3 py-2 text-brand-text-muted">
                {item.specification}
              </td>
              <td className="px-3 py-2 text-brand-text-muted">
                {item.viscosity ?? "—"}
              </td>
              <td className="px-3 py-2 text-brand-text-muted">
                {item.size ?? "—"}
              </td>
              <td className="px-3 py-2 text-right">
                {formatPrice(item.price)}
              </td>
              <td className="px-3 py-2 text-right">
                <span
                  className={
                    item.quantity === 0
                      ? "text-red-600 font-medium"
                      : item.quantity < 5
                        ? "text-amber-600 font-medium"
                        : ""
                  }
                >
                  {item.quantity}
                </span>
              </td>
              <td className="px-3 py-2 text-right">
                <div className="flex items-center justify-end gap-2">
                  <Link
                    href={`/admin/stock/${item.category}/${item.id}`}
                    className="text-xs border border-brand-border px-2 py-1 rounded hover:bg-brand-bg"
                  >
                    Modifier
                  </Link>
                  <button
                    type="button"
                    onClick={() => onDelete(item)}
                    className="text-xs border border-red-200 text-red-700 px-2 py-1 rounded hover:bg-red-50"
                  >
                    Supprimer
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
