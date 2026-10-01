"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { Product } from "@/lib/types";
import {
  CartItem,
  MAX_QUANTITY_PER_ITEM,
  isSameItem,
  loadCart,
  saveCart,
} from "@/lib/cart";

type CartContextValue = {
  items: CartItem[];
  totalItems: number;
  totalPrice: number;
  isOpen: boolean;
  openCart: () => void;
  closeCart: () => void;
  addItem: (product: Product, qty: number, options?: { openDrawer?: boolean }) => void;
  updateQty: (category: string, id: number, qty: number) => void;
  removeItem: (category: string, id: number) => void;
  clearCart: () => void;
  lastAdded: { name: string; at: number } | null;
  clearLastAdded: () => void;
};

const CartContext = createContext<CartContextValue | null>(null);

export function CartProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<CartItem[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [hydrated, setHydrated] = useState(false);
  const [lastAdded, setLastAdded] = useState<{ name: string; at: number } | null>(null);

  // Load once on mount. localStorage is only available after hydration.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- one-time client hydration from localStorage
    setItems(loadCart());
    setHydrated(true);
  }, []);

  // Persist on every change (after hydration)
  useEffect(() => {
    if (hydrated) saveCart(items);
  }, [items, hydrated]);

  const addItem = useCallback(
    (product: Product, qty: number, options?: { openDrawer?: boolean }) => {
      const openDrawer = options?.openDrawer ?? true;

      setItems((prev) => {
        const existing = prev.find((it) =>
          isSameItem(it, { category: product.category, id: product.id })
        );
        if (existing) {
          return prev.map((it) =>
            isSameItem(it, { category: product.category, id: product.id })
              ? { ...it, quantity: Math.min(it.quantity + qty, MAX_QUANTITY_PER_ITEM) }
              : it
          );
        }
        return [
          ...prev,
          {
            category: product.category,
            id: product.id,
            brand: product.brand,
            name: product.name,
            specification: product.specification,
            size: product.size,
            price: product.price,
            image_front_url: product.image_front_url,
            quantity: Math.min(qty, MAX_QUANTITY_PER_ITEM),
          },
        ];
      });

      if (openDrawer) {
        setIsOpen(true);
      } else {
        setLastAdded({ name: product.name, at: Date.now() });
      }
    },
    []
  );

  const updateQty = useCallback((category: string, id: number, qty: number) => {
    setItems((prev) =>
      prev.map((it) =>
        isSameItem(it, { category, id })
          ? { ...it, quantity: Math.max(1, Math.min(qty, MAX_QUANTITY_PER_ITEM)) }
          : it
      )
    );
  }, []);

  const removeItem = useCallback((category: string, id: number) => {
    setItems((prev) => prev.filter((it) => !isSameItem(it, { category, id })));
  }, []);

  const clearCart = useCallback(() => setItems([]), []);

  const openCart = useCallback(() => setIsOpen(true), []);
  const closeCart = useCallback(() => setIsOpen(false), []);
  const clearLastAdded = useCallback(() => setLastAdded(null), []);

  const totalItems = useMemo(
    () => items.reduce((sum, it) => sum + it.quantity, 0),
    [items]
  );

  const totalPrice = useMemo(
    () => items.reduce((sum, it) => sum + it.price * it.quantity, 0),
    [items]
  );

  const value: CartContextValue = {
    items,
    totalItems,
    totalPrice,
    isOpen,
    openCart,
    closeCart,
    addItem,
    updateQty,
    removeItem,
    clearCart,
    lastAdded,
    clearLastAdded,
  };

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart must be used inside <CartProvider>");
  return ctx;
}
