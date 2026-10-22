/* eslint-disable @next/next/no-img-element -- public brand asset */
import Link from "next/link";
import {
  ArrowRight, Camera, Droplets, Filter, Mail, MapPin, Package,
  Phone, ShieldCheck, Truck, Wallet, Wrench,
} from "lucide-react";
import { getProducts } from "@/lib/api";
import ProductCard from "@/components/product/ProductCard";
import { OpenChatButton } from "@/components/home/OpenChatButton";

const categories = [
  { id: "engine_oil", title: "Huile moteur", description: "Pour l’entretien de votre moteur", icon: Droplets, number: "01" },
  { id: "gearbox_oil", title: "Huile de boîte", description: "Pour vos transmissions", icon: Wrench, number: "02" },
  { id: "oil_filter", title: "Filtre à huile", description: "Pour une filtration efficace", icon: Filter, number: "03" },
  { id: "additional", title: "Produits additionnels", description: "Pour compléter votre entretien", icon: Package, number: "04" },
] as const;

async function FeaturedProducts() {
  let items;
  try {
    const data = await getProducts({ page: 1, page_size: 4, sort: "random" });
    items = data.items;
  } catch {
    return null;
  }
  if (!items.length) return null;

  return (
    <section className="border-t border-brand-border bg-brand-surface py-12 sm:py-16" aria-labelledby="featured-title">
      <div className="mx-auto max-w-7xl px-4 md:px-6">
        <div className="mb-6 flex flex-wrap items-end justify-between gap-4 border-b border-brand-border pb-5">
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-[0.14em] text-brand-orange">En rayon</p>
            <h2 id="featured-title" className="text-2xl font-semibold tracking-tight text-brand-text sm:text-3xl">Une sélection du catalogue</h2>
          </div>
          <Link href="/products" className="inline-flex items-center gap-2 text-sm font-semibold text-brand-text hover:text-brand-orange">
            Tous les produits <ArrowRight size={16} aria-hidden="true" />
          </Link>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
          {items.map((product) => (
            <ProductCard key={`${product.category}-${product.id}`} product={product} />
          ))}
        </div>
      </div>
    </section>
  );
}

export default function HomePage() {
  return (
    <main>
      <section className="relative overflow-hidden bg-brand-dark text-white" aria-labelledby="hero-title">
        <div className="pointer-events-none absolute inset-0" aria-hidden="true">
          <div className="absolute -left-24 top-0 h-[28rem] w-[28rem] rounded-full bg-white/[0.045] blur-3xl" />
          <div className="absolute -right-16 bottom-[-8rem] h-[26rem] w-[26rem] rounded-full bg-brand-orange/[0.14] blur-3xl" />
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_72%_42%,rgba(255,255,255,0.08),transparent_28%),radial-gradient(circle_at_18%_80%,rgba(255,85,0,0.10),transparent_32%)]" />
          <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.11)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.11)_1px,transparent_1px)] bg-[size:56px_56px] [mask-image:radial-gradient(ellipse_at_center,black_12%,transparent_86%)]" />
          <div className="absolute inset-0 bg-[linear-gradient(90deg,transparent_49.25%,rgba(255,255,255,0.14)_49.25%,rgba(255,255,255,0.14)_50.75%,transparent_50.75%),linear-gradient(transparent_49.25%,rgba(255,255,255,0.14)_49.25%,rgba(255,255,255,0.14)_50.75%,transparent_50.75%)] bg-[size:112px_112px] opacity-70" />
          <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
        </div>
        <div className="relative mx-auto grid max-w-7xl gap-8 px-4 py-12 sm:py-16 md:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)] md:items-center md:gap-4 md:px-6 lg:py-20">
          <div>
            <p className="mb-5 flex items-center gap-3 text-xs font-semibold uppercase tracking-[0.18em] text-white/65">
              <span className="h-px w-7 bg-brand-orange" aria-hidden="true" />Lubrifiants automobiles · Algérie
            </p>
            <h1 id="hero-title" className="heading-brand max-w-2xl text-[clamp(2.4rem,5.5vw,4.6rem)] leading-[1.02] text-white">
              L’entretien commence avec le bon produit.
            </h1>
            <p className="mt-6 max-w-xl text-sm leading-relaxed text-white/75 sm:text-base">
              Huiles moteur, huiles de boîte et filtres pour votre véhicule. Retrouvez Castrol, Total, Elf, Motul, Febi et d’autres références dans un catalogue pensé pour choisir sans perdre de temps.
            </p>
            <Link href="/products" className="mt-8 inline-flex w-fit items-center justify-center gap-2 rounded bg-brand-orange px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-brand-orange-hover md:gap-3 md:px-6 md:py-3">
              Explorer le catalogue <ArrowRight size={18} aria-hidden="true" />
            </Link>
          </div>
          <div className="relative hidden items-center justify-center md:flex">
            <div className="pointer-events-none absolute inset-[25%] rounded-full bg-white/80 blur-3xl" aria-hidden="true" />
            <div className="pointer-events-none absolute inset-[28%] rounded-[2.5rem] bg-[radial-gradient(circle,rgba(255,255,255,0.92)_0%,rgba(247,248,250,0.55)_42%,transparent_72%)]" aria-hidden="true" />
            <div className="pointer-events-none absolute right-[4%] top-[20%] h-32 w-32 rounded-full bg-brand-orange/30 blur-3xl" aria-hidden="true" />
            <img src="/LubriStock.png" alt="LubriStock" className="relative w-full max-w-lg h-auto object-contain drop-shadow-[0_18px_40px_rgba(0,0,0,0.35)] animate-[hero-logo-pulse_5s_ease-in-out_infinite] motion-reduce:animate-none" />
          </div>
        </div>
      </section>

      <section className="border-b border-brand-border bg-brand-surface" aria-label="Nos engagements">
        <div className="mx-auto grid max-w-7xl grid-cols-1 divide-y divide-brand-border px-4 sm:grid-cols-3 sm:divide-x sm:divide-y-0 md:px-6">
          {[
            { icon: ShieldCheck, title: "Marques reconnues", description: "Des références pour votre entretien" },
            { icon: Truck, title: "58 wilayas", description: "Livraison dans toute l’Algérie" },
            { icon: Wallet, title: "Paiement à la livraison", description: "Commandez en toute simplicité" },
          ].map(({ icon: Icon, title, description }) => (
            <div key={title} className="flex items-center gap-3 py-4 sm:px-5 sm:first:pl-0 sm:last:pr-0">
              <Icon size={21} className="shrink-0 text-brand-text" strokeWidth={1.75} aria-hidden="true" />
              <div><p className="text-sm font-semibold text-brand-text">{title}</p><p className="text-xs text-brand-text-muted">{description}</p></div>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-brand-bg py-14 sm:py-20" aria-labelledby="categories-title">
        <div className="mx-auto max-w-7xl px-4 md:px-6">
        <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="mb-3 flex items-center gap-3 text-xs font-semibold uppercase tracking-[0.14em] text-brand-orange"><span className="h-px w-8 bg-brand-orange" aria-hidden="true" />Le catalogue</p>
            <h2 id="categories-title" className="text-2xl font-semibold tracking-tight text-brand-text sm:text-3xl">Choisissez votre catégorie</h2>
          </div>
          <p className="max-w-xs text-sm text-brand-text-muted">Accédez directement aux produits dont vous avez besoin.</p>
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {categories.map(({ id, title, description, icon: Icon, number }) => (
            <Link key={id} href={`/products?category=${id}`} className="group relative flex min-h-28 flex-col justify-between overflow-hidden rounded-md border border-brand-dark-light bg-brand-dark p-4 transition-colors duration-200 hover:border-brand-orange">
              <span className="absolute left-0 top-0 h-1 w-0 bg-brand-orange transition-all duration-200 group-hover:w-full" aria-hidden="true" />
              <div className="flex items-start justify-between">
                <Icon size={21} strokeWidth={1.7} className="text-brand-orange" aria-hidden="true" />
                <span className="text-[11px] font-medium tabular-nums text-white/55">{number} / 04</span>
              </div>
              <div className="mt-4">
                <div className="flex items-center justify-between gap-3">
                  <h3 className="text-sm font-semibold text-white">{title}</h3>
                  <ArrowRight size={16} className="shrink-0 text-white/60 transition-colors group-hover:text-brand-orange" aria-hidden="true" />
                </div>
                <p className="mt-1 text-[11px] leading-relaxed text-white/60">{description}</p>
              </div>
            </Link>
          ))}
        </div>
        </div>
      </section>

      <FeaturedProducts />

      <section className="mx-auto grid max-w-7xl gap-8 px-4 py-12 sm:py-16 md:grid-cols-[1fr_1.1fr] md:gap-16 md:px-6" aria-labelledby="about-title">
        <div className="border-l-2 border-brand-orange pl-5">
          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.14em] text-brand-text-muted">Notre métier</p>
          <h2 id="about-title" className="max-w-sm text-2xl font-semibold leading-tight text-brand-text sm:text-3xl">Votre entretien automobile, sans détour.</h2>
        </div>
        <div className="max-w-2xl space-y-4 text-sm leading-relaxed text-brand-text-muted sm:text-base">
          <p>LubriStock est un détaillant algérien spécialisé dans les huiles et lubrifiants automobiles. Nous réunissons huiles moteur, huiles de boîte, filtres et produits additionnels dans un seul catalogue.</p>
          <p>Notre sélection comprend des marques reconnues comme Castrol, Total, Elf, Motul et Febi. Particulier ou professionnel, parcourez les références et contactez-nous si vous avez besoin d’un conseil avant de commander.</p>
        </div>
      </section>

      <section className="border-t border-brand-border bg-brand-surface" aria-labelledby="contact-title">
        <div className="mx-auto grid max-w-7xl gap-8 px-4 py-12 sm:py-16 md:grid-cols-[0.8fr_1.2fr] md:items-start md:gap-16 md:px-6">
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-[0.14em] text-brand-text-muted">Une question ?</p>
            <h2 id="contact-title" className="text-2xl font-semibold tracking-tight text-brand-text sm:text-3xl">Parlons de votre véhicule.</h2>
            <p className="mt-3 max-w-sm text-sm leading-relaxed text-brand-text-muted">Un doute sur un produit ou une référence ? Écrivez-nous ou échangez directement avec notre assistant.</p>
            <OpenChatButton className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-brand-text underline decoration-brand-orange decoration-2 underline-offset-4 hover:text-brand-orange" />
          </div>
          <address className="grid grid-cols-1 gap-px overflow-hidden border border-brand-border bg-brand-border not-italic sm:grid-cols-2">
            <a href="tel:+213555000000" className="flex items-start gap-3 bg-brand-surface p-4 text-sm text-brand-text hover:text-brand-orange">
              <Phone size={17} className="mt-0.5 shrink-0" aria-hidden="true" /><span><span className="block text-xs text-brand-text-muted">Téléphone</span>+213 5XX XX XX XX</span>
            </a>
            <a href="mailto:contact@lubristock.dz" className="flex min-w-0 items-start gap-3 bg-brand-surface p-4 text-sm text-brand-text hover:text-brand-orange">
              <Mail size={17} className="mt-0.5 shrink-0" aria-hidden="true" /><span className="min-w-0 break-all"><span className="block text-xs text-brand-text-muted">E-mail</span>contact@lubristock.dz</span>
            </a>
            <div className="flex items-start gap-3 bg-brand-surface p-4 text-sm text-brand-text">
              <MapPin size={17} className="mt-0.5 shrink-0" aria-hidden="true" /><span><span className="block text-xs text-brand-text-muted">Adresse</span>Alger, Algérie</span>
            </div>
            <a href="https://instagram.com/lubristock" target="_blank" rel="noopener noreferrer" className="flex items-start gap-3 bg-brand-surface p-4 text-sm text-brand-text hover:text-brand-orange">
              <Camera size={17} className="mt-0.5 shrink-0" aria-hidden="true" /><span><span className="block text-xs text-brand-text-muted">Instagram</span>@lubristock</span>
            </a>
          </address>
        </div>
      </section>
    </main>
  );
}