import { getProducts } from "@/lib/api";
import type { ProductListParams } from "@/lib/types";
import { CatalogClient } from "@/components/product/CatalogClient";
import type { CatalogFilters } from "@/components/product/CatalogProvider";

const MAX_PAGE_SIZE = 100;

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
  const sortParam = firstString(params.sort);
  const sort: CatalogFilters["sort"] =
    sortParam === "price_asc" || sortParam === "price_desc"
      ? sortParam
      : "random";
  const page = toNumber(params.page) ?? 1;
  const pageSize = toNumber(params.page_size) ?? 20;

  const apiParams: ProductListParams = {
    category: allStrings(params.category),
    brand: allStrings(params.brand),
    min_price: toNumber(params.min_price),
    max_price: toNumber(params.max_price),
    size: allStrings(params.size),
    q: firstString(params.q),
    sort,
    page,
    page_size: pageSize,
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

  if (errorMsg || !data) {
    return (
      <main className="max-w-7xl mx-auto px-4 md:px-6 py-6">
        <div className="p-4 border border-neutral-200 text-sm text-neutral-700">
          {errorMsg ?? "Erreur lors du chargement des produits."}
        </div>
      </main>
    );
  }

  const initialFilters: CatalogFilters = {
    categories: allStrings(params.category) ?? [],
    brands: allStrings(params.brand) ?? [],
    sizes: allStrings(params.size) ?? [],
    minPrice: toNumber(params.min_price) ?? null,
    maxPrice: toNumber(params.max_price) ?? null,
    q: firstString(params.q) ?? "",
    sort,
    page,
    pageSize,
  };

  return (
    <main className="max-w-7xl mx-auto px-4 md:px-6 py-6">
      <CatalogClient
        initialProducts={data.items}
        initialTotal={data.total}
        initialFilters={initialFilters}
        maxPageSize={MAX_PAGE_SIZE}
        allBrands={allBrands}
        allSizes={allSizes}
        maxPriceBound={catalogMaxPrice}
      />
    </main>
  );
}
