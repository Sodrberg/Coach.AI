export default function LoadingSpinner({ size = 'md', message }) {
  const sizeClasses = {
    sm: 'w-5 h-5',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  return (
    <div className="flex flex-col items-center justify-center gap-4 py-12">
      <div className="relative">
        <div
          className={`${sizeClasses[size]} border-2 border-border rounded-full`}
        />
        <div
          className={`${sizeClasses[size]} border-2 border-transparent border-t-accent rounded-full animate-spin absolute inset-0`}
        />
      </div>
      {message && (
        <p className="text-text-secondary text-sm font-medium">{message}</p>
      )}
    </div>
  );
}
