import type { Metadata } from "next";
import "./globals.css";
import { RootShell } from "@/components/layout/RootShell";

export const metadata: Metadata = {
  title: {
    default: "LubriStock",
    template: "%s | LubriStock",
  },
  description: "Votre boutique d'huiles et lubrifiants automobiles en Algérie.",
  icons: {
    icon: "/LubriStock.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr">
      <body className="min-h-screen text-neutral-900 antialiased">
        <RootShell>{children}</RootShell>
      </body>
    </html>
  );
}