import { getProducts } from "@/lib/api";
import type { ProductListParams } from "@/lib/types";
import { ProductGrid } from "@/components/product/ProductGrid";
import { Pagination } from "@/components/product/Pagination";
import { CatalogSidebar } from "@/components/product/CatalogSidebar";
import { SearchBar } from "@/components/layout/SearchBar";

type SearchParams = Record<string, string | string[] | undefined>;

function firstString(v: string | string[] | undefined): string | undefined {
  if (v === undefined) return undefined;
  return Array.isArray(v) ? v[0] : v;
}

function allStrings(v: string | string[] | undefined): string[] | undefined {
  if (v === undefined) return undefined;
  return Array.isArray(v) ? v : [v];
}

function toNumber(v: string | string[] | undefined): number | undefined {
  const s = firstString(v);
  if (s === undefined) return undefined;
  const n = Number(s);
  return Number.isFinite(n) ? n : undefined;
}

export default async function ProductsPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const params = await searchParams;

  const apiParams: ProductListParams = {
    category: allStrings(params.category),
    brand: allStrings(params.brand),
    min_price: toNumber(params.min_price),
    max_price: toNumber(params.max_price),
    size: allStrings(params.size),
    q: firstString(params.q),
    page: toNumber(params.page) ?? 1,
    page_size: toNumber(params.page_size) ?? 20,
  };

  let data = null;
  let errorMsg: string | null = null;
  let catalogMaxPrice = 10000;
  try {
    const maxPriceData = await getProducts({ sort: "price_desc", page_size: 1 });
    catalogMaxPrice = maxPriceData.items[0]?.price ?? 10000;
  } catch {
    // Secondary call failed — keep the fallback, don't block the page.
  }

  let allBrands: string[] = [];
  let allSizes: string[] = [];
  try {
    const firstPage = await getProducts({ page_size: 100, page: 1 });
    const all: typeof firstPage.items = [...firstPage.items];
    const totalPages = Math.ceil(firstPage.total / firstPage.page_size);
    for (let p = 2; p <= totalPages && p <= 5; p++) {
      const nextPage = await getProducts({ page_size: 100, page: p });
      all.push(...nextPage.items);
    }
    allBrands = Array.from(new Set(all.map((p) => p.brand)))
      .sort((a, b) => a.localeCompare(b, "fr"));
    allSizes = Array.from(
      new Set(all.map((p) => p.size).filter((s): s is string => !!s))
    ).sort();
  } catch {
    // best-effort; empty lists are fine
  }

  try {
    data = await getProducts(apiParams);
  } catch (err) {
    console.error("Products fetch error:", err);
    errorMsg = "Erreur lors du chargement des produits.";
  }

  return (
    <main className="max-w-7xl mx-auto px-4 md:px-6 py-6">
      <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-neutral-900">Catalogue</h1>
          {data && (
            <p className="text-sm text-neutral-500 mt-1">
              {data.total} produit{data.total !== 1 ? "s" : ""}
            </p>
          )}
        </div>
        <div className="w-full md:w-96">
          <SearchBar />
        </div>
      </div>

      <div className="flex flex-col md:flex-row gap-6">
        <CatalogSidebar maxPrice={catalogMaxPrice} brands={allBrands} sizes={allSizes} />
        <div className="flex-1 w-full">
          {errorMsg ? (
            <div className="p-4 border border-neutral-200 text-sm text-neutral-700">
              {errorMsg}
            </div>
          ) : data ? (
            <>
              <ProductGrid products={data.items} />
              <Pagination
                page={data.page}
                pageSize={data.page_size}
                total={data.total}
              />
            </>
          ) : null}
        </div>
      </div>
    </main>
  );
}
