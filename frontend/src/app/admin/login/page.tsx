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
        <p className="text-sm text-neutral-500">Chargement…</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-neutral-50 px-4">
      <div className="w-full max-w-sm bg-white border border-neutral-200 rounded-md p-8">
        <h1 className="text-xl font-semibold text-neutral-900 mb-1">
          AutoLube — Administration
        </h1>
        <p className="text-sm text-neutral-500 mb-6">
          Connexion réservée à l&apos;administrateur.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="username"
              className="block text-sm font-medium text-neutral-700 mb-1"
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
              className="w-full border border-neutral-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-neutral-900 disabled:bg-neutral-100"
              required
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-neutral-700 mb-1"
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
                className="w-full border border-neutral-300 rounded px-3 py-2 pr-10 text-sm focus:outline-none focus:border-neutral-900 disabled:bg-neutral-100"
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
                className="absolute inset-y-0 right-0 flex w-10 items-center justify-center text-neutral-500 hover:text-neutral-900 disabled:opacity-50"
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
            className="w-full bg-neutral-900 text-white text-sm font-medium py-2.5 rounded hover:bg-neutral-800 disabled:bg-neutral-400"
          >
            {submitting ? "Connexion…" : "Se connecter"}
          </button>
        </form>
      </div>
    </div>
  );
}
