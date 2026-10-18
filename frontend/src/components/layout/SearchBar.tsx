"use client";

import { useEffect, useRef, useState } from "react";
import { Search } from "lucide-react";
import { useCatalog } from "@/components/product/CatalogProvider";

export function SearchBar() {
  const { filters, setFilters } = useCatalog();

  const [value, setValue] = useState(filters.q);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- sync after catalog reset
    setValue(filters.q);
  }, [filters.q]);

  useEffect(
    () => () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    },
    []
  );

  function handleChange(next: string) {
    setValue(next);
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      setFilters({ q: next.trim() });
    }, 300);
  }

  return (
    <div className="relative">
      <Search className="w-4 h-4 text-neutral-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
      <input
        type="search"
        placeholder="Rechercher un produit, une marque, une spécification…"
        value={value}
        onChange={(e) => handleChange(e.target.value)}
        className="w-full border border-neutral-300 rounded-md pl-9 pr-3 py-2.5 text-sm focus:outline-none focus:border-neutral-900"
      />
    </div>
  );
}