export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`skeleton rounded-lg ${className}`} aria-hidden="true" />;
}

export function SkeletonKpiCard() {
  return (
    <div className="rounded-2xl border border-border bg-background-elevated p-5">
      <Skeleton className="h-3 w-24" />
      <Skeleton className="mt-3 h-8 w-32" />
      <Skeleton className="mt-3 h-3 w-20" />
    </div>
  );
}

export function SkeletonChart() {
  return (
    <div className="rounded-2xl border border-border bg-background-elevated p-5">
      <Skeleton className="h-3 w-40" />
      <Skeleton className="mt-4 h-64 w-full" />
    </div>
  );
}

export function SkeletonTableRow() {
  return (
    <tr>
      {Array.from({ length: 7 }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <Skeleton className="h-4 w-full" />
        </td>
      ))}
    </tr>
  );
}
