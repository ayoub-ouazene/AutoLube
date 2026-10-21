"use client";

import { useCallback, useState } from "react";
import { SlidersHorizontal } from "lucide-react";
import type { Product } from "@/lib/types";
import { SearchBar } from "@/components/layout/SearchBar";
import { CatalogSidebar } from "./CatalogSidebar";
import { ProductGrid } from "./ProductGrid";
import { Pagination } from "./Pagination";
import { MobileFilterDrawer } from "./MobileFilterDrawer";
import { SortSelect } from "./SortSelect";
import {
  CatalogProvider,
  useCatalog,
  type CatalogFilters,
} from "./CatalogProvider";

export function CatalogClient({
  initialProducts,
  initialTotal,
  initialFilters,
  maxPageSize,
  allBrands,
  allSizes,
  maxPriceBound,
}: {
  initialProducts: Product[];
  initialTotal: number;
  initialFilters: CatalogFilters;
  maxPageSize: number;
  allBrands: string[];
  allSizes: string[];
  maxPriceBound: number;
}) {
  return (
    <CatalogProvider
      initialProducts={initialProducts}
      initialTotal={initialTotal}
      initialFilters={initialFilters}
      maxPageSize={maxPageSize}
    >
      <CatalogBody
        allBrands={allBrands}
        allSizes={allSizes}
        maxPriceBound={maxPriceBound}
      />
    </CatalogProvider>
  );
}

function CatalogBody({
  allBrands,
  allSizes,
  maxPriceBound,
}: {
  allBrands: string[];
  allSizes: string[];
  maxPriceBound: number;
}) {
  const { cacheComplete, filteredProducts, filters } = useCatalog();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const closeDrawer = useCallback(() => setDrawerOpen(false), []);

  const activeFilterCount =
    filters.categories.length +
    filters.brands.length +
    filters.sizes.length +
    (filters.minPrice != null ? 1 : 0) +
    (filters.maxPrice != null ? 1 : 0);

  const sidebar = (
    <CatalogSidebar
      maxPrice={maxPriceBound}
      brands={allBrands}
      sizes={allSizes}
    />
  );

  return (
    <>
      <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-neutral-900">Catalogue</h1>
          <p className="text-sm text-neutral-500 mt-1">
            {filteredProducts.length} produit{filteredProducts.length !== 1 ? "s" : ""}
          </p>
        </div>
        <div className="w-full md:w-96">
          <SearchBar />
        </div>
      </div>

      <div className="md:hidden mb-4 flex items-center justify-between gap-2">
        <button
          type="button"
          onClick={() => setDrawerOpen(true)}
          className="inline-flex items-center gap-2 text-sm border border-neutral-300 px-3 py-2 rounded hover:bg-neutral-100"
        >
          <SlidersHorizontal size={16} />
          Filtres
          {activeFilterCount > 0 && (
            <span className="ml-1 bg-neutral-900 text-white text-xs px-1.5 py-0.5 rounded-full">
              {activeFilterCount}
            </span>
          )}
        </button>
        <SortSelect className="min-w-0" />
      </div>

      <div className="flex gap-6">
        <aside className="hidden md:block w-60 shrink-0">{sidebar}</aside>
        <div className="flex-1 min-w-0 w-full">
          <div className="hidden md:flex items-center justify-end mb-3">
            <SortSelect />
          </div>
          <ProductGrid />
          {!cacheComplete && filteredProducts.length < filters.pageSize && (
            <p className="text-xs text-neutral-500 mt-4">
              Chargement du catalogue complet…
            </p>
          )}
          <Pagination />
        </div>
      </div>

      <MobileFilterDrawer open={drawerOpen} onClose={closeDrawer}>
        {sidebar}
      </MobileFilterDrawer>
    </>
  );
}
