import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import { CartProvider } from "@/components/cart/CartProvider";
import { CartDrawer } from "@/components/cart/CartDrawer";
import { CartToast } from "@/components/cart/CartToast";
import { ChatProvider } from "@/components/chat/ChatProvider";
import { ChatWidget } from "@/components/chat/ChatWidget";

export const metadata: Metadata = {
  title: {
    default: "AutoLube",
    template: "%s | AutoLube",
  },
  description: "Votre boutique d'huiles et lubrifiants automobiles en Algérie.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr">
      <body className="min-h-screen bg-white text-neutral-900 antialiased">
        <CartProvider>
          <ChatProvider>
            <Navbar />
            {children}
            <Footer />
            <CartDrawer />
            <CartToast />
            <ChatWidget />
          </ChatProvider>
        </CartProvider>
      </body>
    </html>
  );
}