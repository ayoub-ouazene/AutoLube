export default function ProductDetailLoading() {
  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Back link and breadcrumb skeletons */}
      <div className="h-4 w-40 bg-neutral-200 rounded animate-pulse mb-6" />
      <div className="h-3 w-48 bg-neutral-200 rounded animate-pulse mb-6" />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-12">
        {/* Gallery skeleton */}
        <div className="w-full max-w-md space-y-3">
          <div className="aspect-square bg-neutral-200 rounded-md animate-pulse" />
          <div className="flex gap-2">
            <div className="w-16 h-16 bg-neutral-200 rounded animate-pulse" />
            <div className="w-16 h-16 bg-neutral-200 rounded animate-pulse" />
          </div>
        </div>

        {/* Details skeleton */}
        <div className="space-y-5">
          <div className="space-y-2">
            <div className="h-3 w-20 bg-neutral-200 rounded animate-pulse" />
            <div className="h-8 w-3/4 bg-neutral-200 rounded animate-pulse" />
          </div>
          <div className="flex items-center gap-3">
            <div className="h-9 w-32 bg-neutral-200 rounded animate-pulse" />
            <div className="h-4 w-20 bg-neutral-100 rounded animate-pulse" />
          </div>

          <div className="overflow-hidden rounded-lg border border-neutral-200 divide-y divide-neutral-200">
            {[0, 1, 2, 3].map((row) => (
              <div key={row} className="flex gap-4 px-4 py-3">
                <div className="h-4 w-28 shrink-0 bg-neutral-200 rounded animate-pulse" />
                <div className="h-4 flex-1 bg-neutral-100 rounded animate-pulse" />
              </div>
            ))}
          </div>

          <div className="flex gap-3 pt-1">
            <div className="h-10 w-24 bg-neutral-200 rounded animate-pulse" />
            <div className="h-10 w-40 bg-neutral-200 rounded animate-pulse" />
          </div>
        </div>
      </div>
    </div>
  );
}