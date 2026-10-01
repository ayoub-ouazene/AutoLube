"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Check } from "lucide-react";
import { useCart } from "@/components/cart/CartProvider";
import { useCreateOrder } from "@/hooks/useCreateOrder";
import { WILAYAS } from "@/lib/wilayas";

const PHONE_RE = /^(0|\+213)(5|6|7)[0-9]{8}$/;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const INPUT_CLASS =
  "w-full border border-neutral-300 rounded-md px-3 py-2 text-sm focus:border-neutral-900 focus:outline-none focus:ring-0";

type FormState = {
  full_name: string;
  phone: string;
  email: string;
  wilaya: string;
  city: string;
  notes: string;
};

type FieldErrors = Partial<Record<keyof FormState, string>>;

const EMPTY_FORM: FormState = {
  full_name: "",
  phone: "",
  email: "",
  wilaya: "",
  city: "",
  notes: "",
};

function formatDA(n: number): string {
  return `${n.toLocaleString("fr-DZ")} DA`;
}

function validate(form: FormState): FieldErrors {
  const errors: FieldErrors = {};
  if (form.full_name.trim().length < 2) {
    errors.full_name = "Indiquez votre nom complet (2 caractères minimum).";
  }
  if (!PHONE_RE.test(form.phone.trim())) {
    errors.phone = "Numéro invalide. Exemple : 0555123456 ou +213555123456.";
  }
  if (form.email.trim() && !EMAIL_RE.test(form.email.trim())) {
    errors.email = "Adresse e-mail invalide.";
  }
  if (!form.wilaya) {
    errors.wilaya = "Choisissez une wilaya.";
  }
  if (form.city.trim().length < 2) {
    errors.city = "Indiquez votre ville (2 caractères minimum).";
  }
  if (form.notes.length > 500) {
    errors.notes = "500 caractères maximum.";
  }
  return errors;
}

export default function CheckoutPage() {
  const router = useRouter();
  const { items, totalPrice, clearCart } = useCart();
  const { state, submit } = useCreateOrder();

  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [submitted, setSubmitted] = useState(false);
  const [whatsappOpened, setWhatsappOpened] = useState(false);

  const clearedRef = useRef(false);
  useEffect(() => {
    if (state.status === "success" && !clearedRef.current) {
      clearedRef.current = true;
      clearCart();
    }
  }, [state.status, clearCart]);

  useEffect(() => {
    if (items.length === 0 && state.status !== "success") {
      router.replace("/products");
    }
  }, [items.length, state.status, router]);

  function setField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  const submitting = state.status === "submitting";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitted(true);
    if (Object.keys(validate(form)).length > 0) {
      setErrors(validate(form));
      return;
    }
    setErrors({});
    try {
      await submit(
        {
          full_name: form.full_name.trim(),
          phone: form.phone.trim(),
          email: form.email.trim() || undefined,
          wilaya: form.wilaya,
          city: form.city.trim(),
          notes: form.notes.trim() || undefined,
        },
        items
      );
    } catch {
      // error state is already in `state`
    }
  }

  if (state.status === "success") {
    return (
      <main className="max-w-2xl mx-auto px-4 md:px-6 py-12">
        <div className="text-center">
          <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto mb-4">
            <Check className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-semibold text-neutral-900">
            Commande enregistrée
          </h1>
          <p className="text-sm text-neutral-600 mt-2">
            Votre commande <strong>#{state.data.order_id}</strong> a été enregistrée pour un total de{" "}
            <strong>{state.data.total.toLocaleString("fr-DZ")} DA</strong>.
          </p>
        </div>

        {/* Warning block — prominent, amber */}
        <div className="mt-6 border border-amber-300 bg-amber-50 text-amber-900 p-4 rounded-md">
          <p className="text-sm font-medium">
            Confirmation WhatsApp obligatoire
          </p>
          <p className="text-sm mt-1">
            Votre commande ne sera <strong>traitée qu&apos;après confirmation via WhatsApp</strong>.
            Sans ce message, elle sera automatiquement ignorée.
          </p>
        </div>

        {/* Primary action */}
        <div className="mt-6">
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <a
              href={state.data.whatsapp_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => setWhatsappOpened(true)}
              className="inline-block px-6 py-3 bg-emerald-600 text-white text-sm font-medium rounded-md hover:bg-emerald-700 transition-colors"
            >
              Confirmer sur WhatsApp
            </a>

            {whatsappOpened && (
              <Link
                href="/"
                className="inline-block px-6 py-3 border border-neutral-300 text-sm font-medium text-neutral-900 rounded-md hover:bg-neutral-100 transition-colors"
              >
                J&apos;ai confirmé — Retour à l&apos;accueil
              </Link>
            )}
          </div>

          <p className="text-xs text-neutral-500 mt-3 text-center">
            Un message pré-rempli s&apos;ouvrira dans WhatsApp avec les détails de votre commande.
            Envoyez-le tel quel pour valider.
          </p>
        </div>
      </main>
    );
  }

  if (items.length === 0) {
    return (
      <main className="max-w-2xl mx-auto px-4 md:px-6 py-12 text-center">
        <p className="text-sm text-neutral-600">Votre panier est vide.</p>
        <Link
          href="/products"
          className="mt-4 inline-block text-sm text-neutral-900 underline underline-offset-4"
        >
          Parcourir le catalogue
        </Link>
      </main>
    );
  }

  const shown = submitted ? errors : {};

  return (
    <main className="max-w-7xl mx-auto px-4 md:px-6 py-6">
      <h1 className="text-2xl font-semibold text-neutral-900 mb-6">Passer la commande</h1>
      <div className="grid grid-cols-1 md:grid-cols-[1fr_360px] gap-8">
        <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
          <Field label="Nom complet" htmlFor="full_name" error={shown.full_name}>
            <input
              id="full_name"
              name="full_name"
              type="text"
              required
              autoComplete="name"
              value={form.full_name}
              onChange={(e) => setField("full_name", e.target.value)}
              className={INPUT_CLASS}
            />
          </Field>

          <Field label="Téléphone" htmlFor="phone" error={shown.phone}>
            <input
              id="phone"
              name="phone"
              type="tel"
              required
              autoComplete="tel"
              placeholder="+213 5XX XXX XXX"
              value={form.phone}
              onChange={(e) => setField("phone", e.target.value)}
              className={INPUT_CLASS}
            />
          </Field>

          <Field label="Email" htmlFor="email" error={shown.email} optional>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              value={form.email}
              onChange={(e) => setField("email", e.target.value)}
              className={INPUT_CLASS}
            />
          </Field>

          <Field label="Wilaya" htmlFor="wilaya" error={shown.wilaya}>
            <select
              id="wilaya"
              name="wilaya"
              required
              value={form.wilaya}
              onChange={(e) => setField("wilaya", e.target.value)}
              className={INPUT_CLASS}
            >
              <option value="">Choisir une wilaya</option>
              {WILAYAS.map((w) => (
                <option key={w.code} value={`${w.code} — ${w.name}`}>
                  {w.code} — {w.name}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Ville / Commune" htmlFor="city" error={shown.city}>
            <input
              id="city"
              name="city"
              type="text"
              required
              autoComplete="address-level2"
              value={form.city}
              onChange={(e) => setField("city", e.target.value)}
              className={INPUT_CLASS}
            />
          </Field>

          <Field label="Notes" htmlFor="notes" error={shown.notes} optional>
            <textarea
              id="notes"
              name="notes"
              maxLength={500}
              rows={4}
              value={form.notes}
              onChange={(e) => setField("notes", e.target.value)}
              className={INPUT_CLASS}
            />
            <p className="text-xs text-neutral-500 text-right">{form.notes.length}/500</p>
          </Field>

          {state.status === "error" && (
            <div className="border border-red-300 bg-red-50 text-red-700 text-sm p-3 rounded-md">
              {state.message}
            </div>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-neutral-900 text-white py-3 rounded-md text-sm font-medium hover:bg-neutral-800 disabled:bg-neutral-300 disabled:cursor-not-allowed"
          >
            {submitting ? "Envoi en cours…" : "Confirmer la commande"}
          </button>
        </form>

        <aside className="md:sticky md:top-6 h-fit border border-neutral-200 p-4">
          <h2 className="text-sm font-medium text-neutral-900 mb-3">Récapitulatif</h2>
          <ul className="flex flex-col gap-3">
            {items.map((it) => (
              <li key={`${it.category}-${it.id}`} className="flex gap-3">
                <div className="w-12 h-12 bg-neutral-100 border border-neutral-200 relative shrink-0">
                  {it.image_front_url ? (
                    // eslint-disable-next-line @next/next/no-img-element -- remote URLs, next.config.ts can't be changed
                    <img
                      src={it.image_front_url}
                      alt={it.name}
                      className="absolute inset-0 w-full h-full object-cover"
                    />
                  ) : (
                    <span className="absolute inset-0 flex items-center justify-center text-[10px] text-neutral-400">—</span>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-neutral-900 truncate">{it.name}</p>
                  <p className="text-xs text-neutral-500">Qté {it.quantity}</p>
                </div>
                <p className="text-sm text-neutral-900 shrink-0">
                  {formatDA(it.price * it.quantity)}
                </p>
              </li>
            ))}
          </ul>
          <div className="mt-4 pt-3 border-t border-neutral-200 flex items-center justify-between text-sm">
            <span className="text-neutral-500">Sous-total</span>
            <span className="text-neutral-900">{formatDA(totalPrice)}</span>
          </div>
          <div className="mt-2 flex items-center justify-between">
            <span className="text-base font-semibold text-neutral-900">Total</span>
            <span className="text-lg font-semibold text-neutral-900">{formatDA(totalPrice)}</span>
          </div>
        </aside>
      </div>
    </main>
  );
}

function Field({
  label,
  htmlFor,
  error,
  optional,
  children,
}: {
  label: string;
  htmlFor: string;
  error?: string;
  optional?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={htmlFor} className="text-sm text-neutral-700">
        {label}
        {optional && <span className="text-neutral-400"> (optionnel)</span>}
      </label>
      {children}
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}
