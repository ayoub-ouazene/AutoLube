"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff } from "lucide-react";
import { useAdminAuth } from "@/components/admin/AdminAuthProvider";

export default function AdminLoginPage() {
  const { user, loading, login, loginError } = useAdminAuth();
  const router = useRouter();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && user) {
      router.replace("/admin");
    }
  }, [loading, user, router]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLocalError(null);

    if (!username.trim() || !password) {
      setLocalError("Nom d'utilisateur et mot de passe requis.");
      return;
    }

    setSubmitting(true);
    try {
      const ok = await login(username.trim(), password);
      if (ok) {
        router.replace("/admin");
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-sm text-brand-text-muted">Chargement…</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-brand-dark px-4">
      <div className="w-full max-w-sm bg-brand-surface border border-brand-border rounded-md p-8">
        <h1 className="text-xl font-semibold text-brand-text mb-1">
          LubriStock — Administration
        </h1>
        <p className="text-sm text-brand-text-muted mb-6">
          Connexion réservée à l&apos;administrateur.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="username"
              className="block text-sm font-medium text-brand-text mb-1"
            >
              Nom d&apos;utilisateur
            </label>
            <input
              id="username"
              type="text"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={submitting}
              className="w-full border border-brand-border rounded px-3 py-2 text-sm focus:outline-none focus:border-brand-dark disabled:bg-brand-bg"
              required
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-brand-text mb-1"
            >
              Mot de passe
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={submitting}
                className="w-full border border-brand-border rounded px-3 py-2 pr-10 text-sm focus:outline-none focus:border-brand-dark disabled:bg-brand-bg"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword((visible) => !visible)}
                disabled={submitting}
                aria-label={
                  showPassword
                    ? "Masquer le mot de passe"
                    : "Afficher le mot de passe"
                }
                aria-pressed={showPassword}
                className="absolute inset-y-0 right-0 flex w-10 items-center justify-center text-brand-text-muted hover:text-brand-text disabled:opacity-50"
              >
                {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
              </button>
            </div>
          </div>

          {(localError || loginError) && (
            <p className="text-sm text-red-600">
              {localError ?? loginError}
            </p>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-brand-orange text-white text-sm font-medium py-2.5 rounded hover:bg-brand-orange-hover disabled:bg-neutral-400"
          >
            {submitting ? "Connexion…" : "Se connecter"}
          </button>
        </form>
      </div>
    </div>
  );
}
