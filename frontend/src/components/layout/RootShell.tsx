"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { CartProvider } from "@/components/cart/CartProvider";
import { ChatProvider } from "@/components/chat/ChatProvider";
import Navbar from "./Navbar";
import Footer from "./Footer";
import { CartDrawer } from "@/components/cart/CartDrawer";
import { CartToast } from "@/components/cart/CartToast";
import { ChatWidget } from "@/components/chat/ChatWidget";

export function RootShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const isAdmin = pathname?.startsWith("/admin") ?? false;

  if (isAdmin) {
    return <>{children}</>;
  }

  return (
    <CartProvider>
      <ChatProvider>
        <div className="min-h-screen flex flex-col">
          <Navbar />
          <main className="flex-1">{children}</main>
          <Footer />
        </div>
        <CartDrawer />
        <CartToast />
        <ChatWidget />
      </ChatProvider>
    </CartProvider>
  );
}
