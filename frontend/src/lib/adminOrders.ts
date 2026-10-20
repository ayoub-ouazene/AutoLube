import { apiAdminFetch } from "./adminAuth";

export type OrderStatus =
  | "pending"
  | "confirmed"
  | "cancelled"
  | "delivered";

export const ORDER_STATUSES: { value: OrderStatus; label: string }[] = [
  { value: "pending", label: "En attente" },
  { value: "confirmed", label: "Confirmée" },
  { value: "cancelled", label: "Annulée" },
  { value: "delivered", label: "Livrée" },
];

export function statusLabel(status: string): string {
  return ORDER_STATUSES.find((item) => item.value === status)?.label ?? status;
}

export type AdminOrderSummary = {
  id: number;
  created_at: string;
  customer_name: string;
  customer_phone: string;
  wilaya: string;
  city: string;
  total: number;
  status: OrderStatus;
  item_count: number;
};

export type AdminOrderListResponse = {
  items: AdminOrderSummary[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
};

export type AdminOrderItemDetail = {
  id: number;
  category: string;
  product_id: number;
  brand: string;
  name: string;
  specification: string;
  size: string | null;
  unit_price: number;
  quantity: number;
  line_total: number;
};

export type AdminOrderDetail = {
  id: number;
  created_at: string;
  customer_name: string;
  customer_phone: string;
  customer_email: string | null;
  wilaya: string;
  city: string;
  notes: string | null;
  total: number;
  status: OrderStatus;
  items: AdminOrderItemDetail[];
};

export type OrderStatusResponse = {
  order_id: number;
  status: OrderStatus;
};

export async function listOrders(params: {
  status?: OrderStatus;
  page?: number;
  page_size?: number;
}): Promise<AdminOrderListResponse> {
  const query = new URLSearchParams();
  if (params.status) query.set("status", params.status);
  if (params.page) query.set("page", String(params.page));
  if (params.page_size) query.set("page_size", String(params.page_size));
  const suffix = query.toString();
  return apiAdminFetch<AdminOrderListResponse>(
    `/admin/orders${suffix ? `?${suffix}` : ""}`
  );
}

export async function getOrder(id: number): Promise<AdminOrderDetail> {
  return apiAdminFetch<AdminOrderDetail>(`/admin/orders/${id}`);
}

export async function confirmOrder(id: number): Promise<OrderStatusResponse> {
  return apiAdminFetch<OrderStatusResponse>(
    `/admin/orders/${id}/confirm`,
    { method: "POST" }
  );
}

export async function cancelOrder(id: number): Promise<OrderStatusResponse> {
  return apiAdminFetch<OrderStatusResponse>(
    `/admin/orders/${id}/cancel`,
    { method: "POST" }
  );
}

export function formatPrice(value: number): string {
  return (
    new Intl.NumberFormat("fr-DZ", {
      style: "decimal",
      maximumFractionDigits: 0,
    }).format(value) + " DA"
  );
}

export function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString("fr-FR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function whatsappUrl(phone: string): string {
  let digits = phone.replace(/\D/g, "");
  if (digits.startsWith("0")) {
    digits = "213" + digits.slice(1);
  }
  return `https://wa.me/${digits}`;
}
