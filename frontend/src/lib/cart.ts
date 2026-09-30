export type CartItem = {
  category: string;
  id: number;
  brand: string;
  name: string;
  specification: string;
  size: string | null;
  price: number;
  image_front_url: string | null;
  quantity: number;
};

export const CART_STORAGE_KEY = "autolube_cart_v1";
export const MAX_QUANTITY_PER_ITEM = 50;

export function loadCart(): CartItem[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(CART_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(isValidCartItem);
  } catch {
    return [];
  }
}

export function saveCart(items: CartItem[]): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(items));
  } catch {
    // quota or private mode — silently ignore
  }
}

export function isSameItem(a: CartItem, b: { category: string; id: number }): boolean {
  return a.category === b.category && a.id === b.id;
}

function isValidCartItem(x: unknown): x is CartItem {
  if (!x || typeof x !== "object") return false;
  const it = x as Record<string, unknown>;
  return (
    typeof it.category === "string" &&
    typeof it.id === "number" &&
    typeof it.brand === "string" &&
    typeof it.name === "string" &&
    typeof it.price === "number" &&
    typeof it.quantity === "number" &&
    it.quantity > 0
  );
}
