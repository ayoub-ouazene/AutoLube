"use client";

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { Product } from "@/lib/types";
import { getProducts } from "@/lib/api";

export type CatalogFilters = {
  categories: string[];
  brands: string[];
  sizes: string[];
  minPrice: number | null;
  maxPrice: number | null;
  q: string;
  sort: "random" | "price_asc" | "price_desc";
  page: number;
  pageSize: number;
};

type CatalogContextValue = {
  allProducts: Product[];
  cacheComplete: boolean;
  total: number;
  filters: CatalogFilters;
  setFilters: (next: Partial<CatalogFilters>) => void;
  filteredProducts: Product[];
  paginatedProducts: Product[];
  pageCount: number;
};

const CatalogContext = createContext<CatalogContextValue | null>(null);

export function useCatalog(): CatalogContextValue {
  const ctx = useContext(CatalogContext);
  if (!ctx) throw new Error("useCatalog must be inside CatalogProvider");
  return ctx;
}

export function CatalogProvider({
  initialProducts,
  initialTotal,
  initialFilters,
  maxPageSize,
  children,
}: {
  initialProducts: Product[];
  initialTotal: number;
  initialFilters: CatalogFilters;
  maxPageSize: number;
  children: ReactNode;
}) {
  const [allProducts, setAllProducts] = useState<Product[]>(initialProducts);
  const [total, setTotal] = useState<number>(initialTotal);
  const [cacheComplete, setCacheComplete] = useState<boolean>(
    initialProducts.length >= initialTotal
  );
  const [filters, setFiltersState] = useState<CatalogFilters>(initialFilters);

  useEffect(() => {
    if (cacheComplete) return;
    let cancelled = false;

    async function fetchAll() {
      try {
        const collected: Product[] = [];
        let page = 1;
        let latestTotal = initialTotal;

        while (!cancelled && collected.length < latestTotal) {
          const result = await getProducts({
            page,
            page_size: maxPageSize,
          });
          if (cancelled) return;

          if (result.items.length === 0) break;

          collected.push(...result.items);
          latestTotal = result.total ?? latestTotal;

          setAllProducts([...collected]);
          setTotal(latestTotal);

          if (collected.length >= latestTotal) {
            setCacheComplete(true);
            return;
          }
          page += 1;
        }
        setCacheComplete(true);
      } catch (err) {
        console.error("[catalog] fetch-all failed", err);
      }
    }

    fetchAll();
    return () => {
      cancelled = true;
    };
  }, [cacheComplete, maxPageSize, initialTotal]);

  const setFilters = (next: Partial<CatalogFilters>) => {
    setFiltersState((prev) => {
      const merged = { ...prev, ...next };
      if (next.page === undefined) merged.page = 1;
      return merged;
    });
  };

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams();
    filters.categories.forEach((c) => params.append("category", c));
    filters.brands.forEach((b) => params.append("brand", b));
    filters.sizes.forEach((s) => params.append("size", s));
    if (filters.minPrice != null) params.set("min_price", String(filters.minPrice));
    if (filters.maxPrice != null) params.set("max_price", String(filters.maxPrice));
    if (filters.q) params.set("q", filters.q);
    if (filters.sort !== "random") params.set("sort", filters.sort);
    if (filters.page > 1) params.set("page", String(filters.page));
    const qs = params.toString();
    const url = qs ? `?${qs}` : window.location.pathname;
    window.history.replaceState(null, "", url);
  }, [filters]);

  const filteredProducts = useMemo(() => {
    let list = allProducts;
    if (filters.categories.length > 0) {
      list = list.filter((p) => filters.categories.includes(p.category));
    }
    if (filters.brands.length > 0) {
      list = list.filter((p) => filters.brands.includes(p.brand));
    }
    if (filters.sizes.length > 0) {
      list = list.filter((p) => p.size != null && filters.sizes.includes(p.size));
    }
    if (filters.minPrice != null) {
      list = list.filter((p) => p.price >= filters.minPrice!);
    }
    if (filters.maxPrice != null) {
      list = list.filter((p) => p.price <= filters.maxPrice!);
    }
    if (filters.q) {
      const needle = filters.q.toLowerCase();
      list = list.filter(
        (p) =>
          p.name.toLowerCase().includes(needle) ||
          p.brand.toLowerCase().includes(needle) ||
          (p.specification ?? "").toLowerCase().includes(needle) ||
          (p.viscosity ?? "").toLowerCase().includes(needle)
      );
    }
    if (filters.sort === "price_asc") {
      list = [...list].sort((a, b) => a.price - b.price);
    } else if (filters.sort === "price_desc") {
      list = [...list].sort((a, b) => b.price - a.price);
    }
    return list;
  }, [allProducts, filters]);

  const pageCount = Math.max(
    1,
    Math.ceil(filteredProducts.length / filters.pageSize)
  );
  const safePage = Math.min(filters.page, pageCount);
  const paginatedProducts = filteredProducts.slice(
    (safePage - 1) * filters.pageSize,
    safePage * filters.pageSize
  );

  const value: CatalogContextValue = {
    allProducts,
    cacheComplete,
    total,
    filters: safePage === filters.page ? filters : { ...filters, page: safePage },
    setFilters,
    filteredProducts,
    paginatedProducts,
    pageCount,
  };

  return (
    <CatalogContext.Provider value={value}>
      {children}
    </CatalogContext.Provider>
  );
}
