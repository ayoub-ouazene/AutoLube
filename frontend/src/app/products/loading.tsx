export default function CatalogLoading() {
  return (
    <div className="max-w-7xl mx-auto px-4 md:px-6 py-6">
      {/* Catalog heading and search skeleton */}
      <div className="mb-6 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="space-y-2">
          <div className="h-7 w-32 bg-neutral-200 rounded animate-pulse" />
          <div className="h-4 w-20 bg-neutral-100 rounded animate-pulse" />
        </div>
        <div className="h-10 w-full md:w-96 bg-neutral-200 rounded animate-pulse" />
      </div>

      {/* Mobile filter and sort row skeleton */}
      <div className="md:hidden mb-4 flex items-center gap-2">
        <div className="h-9 w-24 bg-neutral-200 rounded animate-pulse" />
        <div className="h-9 w-32 bg-neutral-200 rounded animate-pulse ml-auto" />
      </div>

      {/* Desktop layout: sidebar and product grid */}
      <div className="flex gap-6">
        <aside className="hidden md:block w-60 shrink-0">
          <div className="space-y-5">
            {[0, 1, 2, 3].map((section) => (
              <div key={section} className="space-y-2">
                <div className="h-4 w-20 bg-neutral-200 rounded animate-pulse" />
                {[0, 1, 2].map((row) => (
                  <div
                    key={row}
                    className="h-3 w-full bg-neutral-100 rounded animate-pulse"
                  />
                ))}
              </div>
            ))}
          </div>
        </aside>

        <main className="flex-1 min-w-0">
          <div className="hidden md:flex justify-end mb-3">
            <div className="h-8 w-32 bg-neutral-200 rounded animate-pulse" />
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {Array.from({ length: 10 }).map((_, index) => (
              <div
                key={index}
                className="border border-neutral-200 rounded-md p-2 space-y-2"
              >
                <div className="aspect-square bg-neutral-200 rounded animate-pulse" />
                <div className="h-3 w-16 bg-neutral-200 rounded animate-pulse" />
                <div className="h-3 w-full bg-neutral-100 rounded animate-pulse" />
                <div className="h-3 w-3/4 bg-neutral-100 rounded animate-pulse" />
                <div className="h-4 w-20 bg-neutral-200 rounded animate-pulse" />
              </div>
            ))}
          </div>
        </main>
      </div>
    </div>
  );
}