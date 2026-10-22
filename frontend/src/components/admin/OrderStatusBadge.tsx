import { type OrderStatus, statusLabel } from "@/lib/adminOrders";

const COLORS: Record<OrderStatus, string> = {
  pending: "bg-amber-50 text-amber-800 border-amber-200",
  confirmed: "bg-green-50 text-green-800 border-green-200",
  cancelled: "bg-brand-bg text-brand-text-muted border-brand-border",
  delivered: "bg-blue-50 text-blue-800 border-blue-200",
};

export function OrderStatusBadge({ status }: { status: OrderStatus }) {
  const color = COLORS[status] ?? COLORS.pending;
  return (
    <span
      className={`inline-block text-xs font-medium px-2 py-0.5 rounded border ${color}`}
    >
      {statusLabel(status)}
    </span>
  );
}
