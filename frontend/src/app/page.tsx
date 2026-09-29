export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col justify-center px-6 py-16">
      <p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-800">
        AutoLube
      </p>
      <h1 className="mt-4 max-w-2xl text-4xl font-semibold tracking-tight sm:text-5xl">
        The storefront starts here.
      </h1>
      <p className="mt-5 max-w-xl text-lg leading-8 text-neutral-600">
        Your Next.js frontend is ready to connect to the AutoLube API.
      </p>
    </main>
  );
}