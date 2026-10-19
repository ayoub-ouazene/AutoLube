import { AdminAuthError, apiAdminFetch } from "./adminAuth";

export type StockCategory =
  | "engine_oil"
  | "gearbox_oil"
  | "oil_filter"
  | "additional";

export const STOCK_CATEGORIES: { value: StockCategory; label: string }[] = [
  { value: "engine_oil", label: "Huile moteur" },
  { value: "gearbox_oil", label: "Huile de boîte" },
  { value: "oil_filter", label: "Filtre à huile" },
  { value: "additional", label: "Produit additionnel" },
];

export function categoryLabel(c: string): string {
  return STOCK_CATEGORIES.find((x) => x.value === c)?.label ?? c;
}

export type AdminStockItem = {
  category: StockCategory;
  id: number;
  brand: string;
  name: string;
  specification: string;
  viscosity: string | null;
  size: string | null;
  price: number;
  quantity: number;
  in_stock: boolean;
  image_front_url: string | null;
  image_back_url: string | null;
};

export type AdminStockListResponse = {
  items: AdminStockItem[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
};

export type StockCreatePayload = {
  category: StockCategory;
  brand: string;
  specification: string;
  viscosity?: string;
  size?: string;
  price: number;
  quantity: number;
  category_type?: string;
};

export type StockUpdatePayload = Partial<Omit<StockCreatePayload, "category">>;

export async function listStock(params: {
  category?: StockCategory;
  q?: string;
  page?: number;
  page_size?: number;
}): Promise<AdminStockListResponse> {
  const search = new URLSearchParams();
  if (params.category) search.set("category", params.category);
  if (params.q) search.set("q", params.q);
  if (params.page) search.set("page", String(params.page));
  if (params.page_size) search.set("page_size", String(params.page_size));
  const qs = search.toString();
  return apiAdminFetch<AdminStockListResponse>(
    `/admin/stock${qs ? `?${qs}` : ""}`
  );
}

export async function createStock(
  payload: StockCreatePayload
): Promise<AdminStockItem> {
  return apiAdminFetch<AdminStockItem>("/admin/stock", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateStock(
  category: StockCategory,
  id: number,
  payload: StockUpdatePayload
): Promise<AdminStockItem> {
  return apiAdminFetch<AdminStockItem>(
    `/admin/stock/${category}/${id}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    }
  );
}

export async function deleteStock(
  category: StockCategory,
  id: number
): Promise<void> {
  await apiAdminFetch<void>(`/admin/stock/${category}/${id}`, {
    method: "DELETE",
  });
}

export async function getStockItem(
  category: StockCategory,
  id: number
): Promise<AdminStockItem> {
  return apiAdminFetch<AdminStockItem>(
    `/admin/stock/${category}/${id}`
  );
}

/**
 * Fetch a single stock item by category and id.
 * Uses the direct GET endpoint (Phase 2.5) — no more pagination loop.
 */
export async function findStockItem(
  category: StockCategory,
  id: number
): Promise<AdminStockItem | null> {
  try {
    return await getStockItem(category, id);
  } catch (err) {
    if (err instanceof AdminAuthError && err.status === 404) {
      return null;
    }
    throw err;
  }
}

export type ImagePosition = "front" | "back";

export async function uploadStockImage(
  category: StockCategory,
  id: number,
  position: ImagePosition,
  file: File
): Promise<AdminStockItem> {
  const form = new FormData();
  form.append(position, file);
  return apiAdminFetch<AdminStockItem>(
    `/admin/stock/${category}/${id}/images`,
    { method: "POST", body: form }
  );
}

export async function deleteStockImage(
  category: StockCategory,
  id: number,
  position: ImagePosition
): Promise<AdminStockItem> {
  return apiAdminFetch<AdminStockItem>(
    `/admin/stock/${category}/${id}/images/${position}`,
    { method: "DELETE" }
  );
}
