"use client";

import type { Product } from "@/lib/types";
import { SearchBar } from "@/components/layout/SearchBar";
import { CatalogSidebar } from "./CatalogSidebar";
import { ProductGrid } from "./ProductGrid";
import { Pagination } from "./Pagination";
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

      <div className="flex flex-col md:flex-row gap-6">
        <CatalogSidebar
          maxPrice={maxPriceBound}
          brands={allBrands}
          sizes={allSizes}
        />
        <div className="flex-1 w-full">
          <ProductGrid />
          {!cacheComplete && filteredProducts.length < filters.pageSize && (
            <p className="text-xs text-neutral-500 mt-4">
              Chargement du catalogue complet…
            </p>
          )}
          <Pagination />
        </div>
      </div>
    </>
  );
}
