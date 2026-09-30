import Link from "next/link";
import { notFound } from "next/navigation";
import { getProduct } from "@/lib/api";
import { ProductGallery } from "@/components/product/ProductGallery";

interface Props {
  params: Promise<{ category: string; id: string }>;
}

export default async function ProductDetailPage({ params }: Props) {
  const { category, id } = await params;
  const productId = Number(id);

  if (isNaN(productId)) {
    notFound();
  }

  let product;
  try {
    product = await getProduct(category, productId);
  } catch {
    notFound();
  }

  const formattedPrice = product.price.toLocaleString("fr-DZ") + " DA";

  const categoryLabels: Record<string, string> = {
    engine_oil: "Huile moteur",
    gearbox_oil: "Huile boîte de vitesses",
    oil_filter: "Filtre à huile",
    additional: "Accessoires",
  };

  return (
    <main className="max-w-6xl mx-auto px-4 py-8">
      {/* Back link */}
      <Link
        href="/products"
        className="inline-flex items-center gap-1 text-sm text-neutral-500 hover:text-neutral-900 mb-6 transition-colors"
      >
        ← Retour aux produits
      </Link>

      {/* Breadcrumb */}
      <p className="text-xs text-neutral-400 uppercase tracking-wide mb-6">
        {categoryLabels[product.category] ?? product.category} / {product.brand}
      </p>

      {/* Layout: gallery left, info right */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-12">
        {/* Gallery */}
        <div className="w-full max-w-md">
          <ProductGallery product={product} />
        </div>

        {/* Info */}
        <div className="flex flex-col gap-5">
          {/* Brand + name */}
          <div className="flex flex-col gap-1">
            <p className="text-xs uppercase tracking-wide text-neutral-500">
              {product.brand}
            </p>
            <h1 className="text-2xl font-semibold text-neutral-900">
              {product.name}
            </h1>
          </div>

          {/* Price */}
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-neutral-900">
              {formattedPrice}
            </span>
            {product.in_stock ? (
              <span className="text-sm text-green-700 font-medium">En stock</span>
            ) : (
              <span className="text-sm text-red-600 font-medium">Rupture de stock</span>
            )}
          </div>

          {/* Specs table */}
          <div className="border border-neutral-200 divide-y divide-neutral-200 text-sm">
            {product.specification && (
              <div className="flex gap-4 px-4 py-2.5">
                <span className="w-36 flex-shrink-0 text-neutral-500">Spécification</span>
                <span className="text-neutral-900">{product.specification}</span>
              </div>
            )}
            {product.viscosity && (
              <div className="flex gap-4 px-4 py-2.5">
                <span className="w-36 flex-shrink-0 text-neutral-500">Viscosité</span>
                <span className="text-neutral-900">{product.viscosity}</span>
              </div>
            )}
            {product.size && (
              <div className="flex gap-4 px-4 py-2.5">
                <span className="w-36 flex-shrink-0 text-neutral-500">Contenance</span>
                <span className="text-neutral-900">{product.size}</span>
              </div>
            )}
            <div className="flex gap-4 px-4 py-2.5">
              <span className="w-36 flex-shrink-0 text-neutral-500">Marque</span>
              <span className="text-neutral-900">{product.brand}</span>
            </div>
          </div>

          {/* Add to cart */}
          <div className="mt-2">
            {product.in_stock ? (
              <button
                type="button"
                className="w-full bg-neutral-900 text-white font-medium py-3 rounded-md hover:bg-neutral-700 transition-colors"
              >
                Ajouter au panier
              </button>
            ) : (
              <button
                type="button"
                disabled
                className="w-full bg-neutral-200 text-neutral-400 font-medium py-3 rounded-md cursor-not-allowed"
              >
                Indisponible
              </button>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}