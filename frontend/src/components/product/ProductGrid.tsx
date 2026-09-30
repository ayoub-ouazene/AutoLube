import type { Product } from "@/lib/types";
import ProductCard from "./ProductCard";

interface Props {
  products: Product[];
}

export function ProductGrid({ products }: Props) {
  if (products.length === 0) {
    return (
      <div className="flex items-center justify-center py-16 border border-neutral-200">
        <p className="text-sm text-neutral-500">
          Aucun produit ne correspond à votre recherche.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
      {products.map((product) => (
        <ProductCard key={`${product.category}-${product.id}`} product={product} />
      ))}
    </div>
  );
}
