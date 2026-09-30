export type ProductCategory = "engine_oil" | "gearbox_oil" | "oil_filter" | "additional";

export interface Product {
  category: ProductCategory;
  id: number;
  brand: string;
  name: string;
  specification: string;
  viscosity: string | null;
  size: string | null;
  price: number;
  in_stock: boolean;
  image_front_url: string | null;
  image_back_url: string | null;
}

export interface ProductListParams {
  category?: string[];
  brand?: string[];
  min_price?: number;
  max_price?: number;
  size?: string[];
  size_min?: number;
  size_max?: number;
  q?: string;
  sort?: "random" | "price_asc" | "price_desc";
  page?: number;
  page_size?: number;
}

export interface ProductListResponse {
  items: Product[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}
