import { useState } from "react";
import { apiPost } from "@/lib/api";
import type { CartItem } from "@/lib/cart";

export type OrderCustomer = {
  full_name: string;
  phone: string;
  email?: string;
  wilaya: string;
  city: string;
  notes?: string;
};

export type OrderCreatePayload = {
  customer: OrderCustomer;
  items: { category: string; id: number; quantity: number }[];
};

export type OrderCreateResponse = {
  order_id: number;
  total: number;
  items: {
    category: string;
    product_id: number;
    name: string;
    size: string | null;
    unit_price: number;
    quantity: number;
    line_total: number;
  }[];
  whatsapp_url: string;
};

export type SubmitState =
  | { status: "idle" }
  | { status: "submitting" }
  | { status: "success"; data: OrderCreateResponse }
  | { status: "error"; message: string };

export function cartToOrderItems(cart: CartItem[]) {
  return cart.map((it) => ({
    category: it.category,
    id: it.id,
    quantity: it.quantity,
  }));
}

export async function submitOrder(
  customer: OrderCustomer,
  cart: CartItem[]
): Promise<OrderCreateResponse> {
  const payload: OrderCreatePayload = {
    customer,
    items: cartToOrderItems(cart),
  };
  return apiPost<OrderCreateResponse>("/orders", payload);
}

export function useCreateOrder() {
  const [state, setState] = useState<SubmitState>({ status: "idle" });

  async function submit(customer: OrderCustomer, cart: CartItem[]) {
    setState({ status: "submitting" });
    try {
      const data = await submitOrder(customer, cart);
      setState({ status: "success", data });
      return data;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Erreur inconnue.";
      setState({ status: "error", message });
      throw err;
    }
  }

  function reset() {
    setState({ status: "idle" });
  }

  return { state, submit, reset };
}
