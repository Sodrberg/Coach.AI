function Pulse({ className = '' }) {
  return <div className={`animate-pulse rounded-lg bg-surface-elevated ${className}`} />;
}

function SkeletonCard({ children }) {
  return (
    <div className="bg-surface-card rounded-xl p-6 border border-border">
      {children}
    </div>
  );
}

export function DashboardSkeleton() {
  return (
    <div className="space-y-6 animate-in">
      {/* Header */}
      <div className="mb-8">
        <Pulse className="h-4 w-32 mb-3" />
        <Pulse className="h-8 w-48" />
      </div>

      {/* Goal card */}
      <SkeletonCard>
        <div className="flex items-center justify-between">
          <div>
            <Pulse className="h-3 w-20 mb-3" />
            <Pulse className="h-6 w-40" />
          </div>
          <div className="text-right">
            <Pulse className="h-10 w-16 mb-1" />
            <Pulse className="h-3 w-14 ml-auto" />
          </div>
        </div>
      </SkeletonCard>

      {/* Workout card */}
      <SkeletonCard>
        <Pulse className="h-5 w-36 mb-5" />
        <div className="flex items-start justify-between mb-5">
          <div>
            <Pulse className="h-4 w-20 mb-3" />
            <Pulse className="h-7 w-52" />
          </div>
          <Pulse className="h-14 w-16 rounded-lg" />
        </div>
        <Pulse className="h-4 w-40 mb-6" />
        <Pulse className="h-12 w-full rounded-lg" />
      </SkeletonCard>

      {/* Quick actions */}
      <div className="grid grid-cols-2 gap-4">
        <SkeletonCard>
          <Pulse className="h-10 w-10 rounded-lg mb-3" />
          <Pulse className="h-5 w-24 mb-1" />
          <Pulse className="h-3 w-28" />
        </SkeletonCard>
        <SkeletonCard>
          <Pulse className="h-10 w-10 rounded-lg mb-3" />
          <Pulse className="h-5 w-20 mb-1" />
          <Pulse className="h-3 w-24" />
        </SkeletonCard>
      </div>
    </div>
  );
}

export function WorkoutSkeleton() {
  return (
    <div className="space-y-6 animate-in">
      {/* Header */}
      <div className="mb-2">
        <Pulse className="h-8 w-48 mb-3" />
        <Pulse className="h-4 w-40" />
      </div>

      {/* Feedback card */}
      <SkeletonCard>
        <Pulse className="h-6 w-52 mb-4" />
        <div className="grid grid-cols-2 gap-3">
          {[1, 2, 3, 4].map((i) => (
            <Pulse key={i} className="h-20 rounded-xl" />
          ))}
        </div>
      </SkeletonCard>

      {/* Workout card */}
      <SkeletonCard>
        <Pulse className="h-7 w-56 mb-3" />
        <div className="flex gap-3 mb-5">
          <Pulse className="h-6 w-20 rounded-full" />
          <Pulse className="h-6 w-16" />
          <Pulse className="h-6 w-20" />
        </div>
        <Pulse className="h-16 w-full mb-3 rounded-lg" />
        <div className="space-y-1">
          {[1, 2, 3, 4].map((i) => (
            <Pulse key={i} className="h-16 w-full" />
          ))}
        </div>
      </SkeletonCard>
    </div>
  );
}
