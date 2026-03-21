export default function ConfirmModal({ isOpen, title, message, confirmLabel = 'Confirm', cancelLabel = 'Cancel', onConfirm, onCancel, variant = 'danger' }) {
  if (!isOpen) return null;

  const confirmStyles = variant === 'danger'
    ? 'bg-danger hover:bg-red-600 text-white'
    : 'bg-accent hover:bg-accent-dark text-surface-base';

  return (
    <div className="fixed inset-0 z-[90] flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-label={title}>
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onCancel} />

      {/* Modal */}
      <div className="relative bg-surface-card border border-border rounded-2xl shadow-xl max-w-sm w-full p-6 animate-toast-in">
        <h3 className="text-lg font-heading font-semibold text-text-primary mb-2">
          {title}
        </h3>
        <p className="text-text-secondary text-sm mb-6">
          {message}
        </p>
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="btn-secondary flex-1 py-2.5"
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            className={`btn flex-1 py-2.5 font-semibold ${confirmStyles}`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
