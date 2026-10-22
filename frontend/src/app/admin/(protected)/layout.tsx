"use client";

import { type ReactNode, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAdminAuth } from "@/components/admin/AdminAuthProvider";
import { AdminHeader } from "@/components/admin/AdminHeader";
import { ConfirmProvider } from "@/components/admin/ConfirmProvider";

export default function ProtectedAdminLayout({
  children,
}: {
  children: ReactNode;
}) {
  const { user, loading } = useAdminAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/admin/login");
    }
  }, [loading, user, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-sm text-brand-text-muted">Vérification…</p>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <ConfirmProvider>
      <div className="min-h-screen bg-brand-bg">
        <AdminHeader />
        <main>{children}</main>
      </div>
    </ConfirmProvider>
  );
}
