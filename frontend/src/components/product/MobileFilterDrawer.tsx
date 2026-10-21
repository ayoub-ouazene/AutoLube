"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { X } from "lucide-react";
import { useCatalog } from "./CatalogProvider";

export function MobileFilterDrawer({
  open,
  onClose,
  children,
}: {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
}) {
  const { filteredProducts } = useCatalog();
  const drawerRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    const previouslyFocused = document.activeElement as HTMLElement | null;
    const original = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeButtonRef.current?.focus();
    return () => {
      document.body.style.overflow = original;
      previouslyFocused?.focus();
    };
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
        return;
      }
      if (event.key !== "Tab") return;

      const focusable = drawerRef.current?.querySelectorAll<HTMLElement>(
        'button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [href], [tabindex]:not([tabindex="-1"])'
      );
      if (!focusable?.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  // If responsive mode crosses into desktop while the drawer is open,
  // close it so the body scroll lock is released immediately.
  useEffect(() => {
    if (!open) return;
    const desktop = window.matchMedia("(min-width: 768px)");
    const closeOnDesktop = () => {
      if (desktop.matches || window.innerWidth >= 768) onClose();
    };
    desktop.addEventListener("change", closeOnDesktop);
    window.addEventListener("resize", closeOnDesktop);
    return () => {
      desktop.removeEventListener("change", closeOnDesktop);
      window.removeEventListener("resize", closeOnDesktop);
    };
  }, [open, onClose]);

  return (
    <>
      <div
        className={
          "fixed inset-0 z-40 bg-black/40 md:hidden transition-opacity duration-200 " +
          (open
            ? "opacity-100 pointer-events-auto"
            : "opacity-0 pointer-events-none")
        }
        onClick={onClose}
        aria-hidden="true"
      />

      <div
        ref={drawerRef}
        role="dialog"
        aria-modal={open ? "true" : undefined}
        aria-hidden={!open}
        aria-label="Filtres"
        inert={!open}
        className={
          "fixed top-0 right-0 bottom-0 z-50 w-[85%] max-w-sm bg-white md:hidden " +
          "flex flex-col shadow-xl transition-transform duration-200 " +
          (open
            ? "translate-x-0 pointer-events-auto"
            : "translate-x-full pointer-events-none")
        }
      >
        <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-200">
          <h2 className="text-base font-semibold text-neutral-900">
            Filtres
          </h2>
          <button
            ref={closeButtonRef}
            type="button"
            onClick={onClose}
            aria-label="Fermer les filtres"
            className="p-1 hover:bg-neutral-100 rounded"
          >
            <X size={20} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">{children}</div>

        <div className="border-t border-neutral-200 p-3">
          <button
            type="button"
            onClick={onClose}
            className="w-full bg-neutral-900 text-white text-sm font-medium py-2.5 rounded hover:bg-neutral-800"
          >
            Voir {filteredProducts.length} résultat
            {filteredProducts.length === 1 ? "" : "s"}
          </button>
        </div>
      </div>
    </>
  );
}
