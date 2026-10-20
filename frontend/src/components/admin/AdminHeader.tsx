"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAdminAuth } from "./AdminAuthProvider";

export function AdminHeader() {
  const { user, logout } = useAdminAuth();
  const router = useRouter();
  const pathname = usePathname();

  const handleLogout = async () => {
    await logout();
    router.replace("/admin/login");
  };

  const navItems = [
    { href: "/admin", label: "Tableau de bord" },
    { href: "/admin/stock", label: "Stock" },
    { href: "/admin/orders", label: "Commandes" },
  ];

  return (
    <header className="bg-white border-b border-neutral-200">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link href="/admin" className="text-sm font-semibold text-neutral-900">
            AutoLube — Admin
          </Link>
          <nav className="flex items-center gap-1">
            {navItems.map((item) => {
              const active =
                item.href === "/admin"
                  ? pathname === "/admin"
                  : pathname?.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`text-sm px-3 py-1.5 rounded ${
                    active
                      ? "bg-neutral-100 text-neutral-900 font-medium"
                      : "text-neutral-600 hover:text-neutral-900"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="flex items-center gap-3">
          {user && (
            <span className="text-xs text-neutral-500">{user.username}</span>
          )}
          <button
            type="button"
            onClick={handleLogout}
            className="text-sm border border-neutral-300 px-3 py-1.5 rounded hover:bg-neutral-100"
          >
            Déconnexion
          </button>
        </div>
      </div>
    </header>
  );
}
