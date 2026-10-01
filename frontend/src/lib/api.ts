import type { Product, ProductListParams, ProductListResponse } from "./types";

function getBaseUrl(): string {
  const url = process.env.NEXT_PUBLIC_API_URL;
  if (!url) {
    throw new Error("NEXT_PUBLIC_API_URL is not defined");
  }
  // Ensure trailing slash so that relative paths append correctly.
  return url.endsWith("/") ? url : url + "/";
}

export async function apiGet<T>(
  path: string,
  params?: Record<string, string | number | boolean | string[] | null | undefined>,
): Promise<T> {
  // Strip leading slash from path so it is treated as relative to the full
  // base URL (including its /api/v1 prefix) rather than replacing it.
  const relativePath = path.startsWith("/") ? path.slice(1) : path;
  const url = new URL(relativePath, getBaseUrl());

  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value === undefined || value === null) continue;

      if (Array.isArray(value)) {
        for (const item of value) {
          url.searchParams.append(key, String(item));
        }
      } else {
        url.searchParams.append(key, String(value));
      }
    }
  }

  const response = await fetch(url.toString(), { cache: "no-store" });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`API error ${response.status}: ${body}`);
  }

  return response.json() as Promise<T>;
}

export function getProducts(params?: ProductListParams): Promise<ProductListResponse> {
  return apiGet<ProductListResponse>("/products", params as Record<string, string | number | boolean | string[] | null | undefined>);
}

export function getProduct(category: string, id: number): Promise<Product> {
  return apiGet<Product>(`/products/${category}/${id}`);
}

export async function apiPost<T>(
  path: string,
  body: unknown
): Promise<T> {
  const base = getBaseUrl();
  const relativePath = path.startsWith("/") ? path.slice(1) : path;
  const url = new URL(relativePath, base);
  const res = await fetch(url.toString(), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}
