import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-[70vh] flex items-center justify-center px-4 py-16">
      <div className="max-w-md w-full text-center">
        <p className="text-6xl font-bold text-neutral-200 mb-4">404</p>
        <h1 className="text-2xl font-semibold text-neutral-900 mb-2">
          Page introuvable
        </h1>
        <p className="text-sm text-neutral-600 mb-8">
          La page que vous recherchez n&apos;existe pas ou a été déplacée.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/"
            className="bg-neutral-900 text-white text-sm font-medium px-5 py-2.5 rounded hover:bg-neutral-800"
          >
            Retour à l&apos;accueil
          </Link>
          <Link
            href="/products"
            className="border border-neutral-300 text-neutral-800 text-sm font-medium px-5 py-2.5 rounded hover:bg-neutral-100"
          >
            Voir les produits
          </Link>
        </div>
      </div>
    </div>
  );
}