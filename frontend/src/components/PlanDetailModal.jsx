import { useEffect } from 'react';
import renderMarkdown from '../utils/renderMarkdown';

export default function PlanDetailModal({ isOpen, onClose, overviewMarkdown, phaseBreakdown }) {
  useEffect(() => {
    if (!isOpen) return;

    document.body.style.overflow = 'hidden';
    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleEscape);

    return () => {
      document.body.style.overflow = '';
      window.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[90] flex items-end sm:items-center justify-center p-0 sm:p-4" role="dialog" aria-modal="true" aria-label="Plan Details">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-surface-card border border-border rounded-t-2xl sm:rounded-2xl shadow-xl w-full sm:max-w-lg max-h-[85vh] flex flex-col animate-toast-in">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-border flex-shrink-0">
          <h2 className="text-lg font-heading font-bold text-text-primary">Training Plan</h2>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-surface-elevated flex items-center justify-center text-text-muted hover:text-text-primary transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Scrollable body */}
        <div className="overflow-y-auto p-5 space-y-6">
          {/* Overview markdown */}
          {overviewMarkdown && (
            <div>{renderMarkdown(overviewMarkdown)}</div>
          )}

          {/* Phase breakdown */}
          {phaseBreakdown && phaseBreakdown.length > 0 && (
            <div>
              <h2 className="text-lg font-heading font-bold text-text-primary mt-2 mb-3">Training Phases</h2>
              <div className="space-y-3">
                {phaseBreakdown.map((phase, index) => (
                  <div
                    key={index}
                    className="p-4 bg-surface-elevated rounded-lg border border-border"
                  >
                    <div className="flex items-center gap-3 mb-1">
                      <span className="px-2.5 py-1 rounded-md bg-accent/10 text-accent text-xs font-heading font-semibold">
                        Wk {phase.weeks}
                      </span>
                      <span className="font-heading font-medium text-text-primary text-sm">{phase.focus}</span>
                    </div>
                    {phase.description && (
                      <p className="text-sm text-text-secondary mt-2 leading-relaxed">{phase.description}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
