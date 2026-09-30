"use client";

import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Search } from "lucide-react";

export function SearchBar() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [value, setValue] = useState(searchParams.get("q") ?? "");
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Sync from URL when it changes externally (e.g. browser back/forward)
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- intentional URL sync
    setValue(searchParams.get("q") ?? "");
  }, [searchParams]);

  function handleChange(next: string) {
    setValue(next);
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      const params = new URLSearchParams(searchParams.toString());
      params.delete("page");
      if (next.trim()) params.set("q", next.trim());
      else params.delete("q");
      router.replace(`${pathname}?${params.toString()}`);
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