import { useState, useEffect } from 'react';
import { useSwapWorkoutToToday } from '../hooks/useApi';
import WorkoutBuilder from './WorkoutBuilder';

export default function TrainAnywayModal({ isOpen, onClose, nextWorkoutDate, onWorkoutReady }) {
  const [showBuilder, setShowBuilder] = useState(false);
  const swapMutation = useSwapWorkoutToToday();

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setShowBuilder(false);
    }
  }, [isOpen]);

  // Close on escape key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        if (showBuilder) {
          setShowBuilder(false);
        } else {
          onClose();
        }
      }
    };
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [isOpen, showBuilder, onClose]);

  const handleMoveWorkout = async () => {
    try {
      const workout = await swapMutation.mutateAsync();
      onWorkoutReady?.(workout);
      onClose();
    } catch (error) {
      console.error('Failed to swap workout:', error);
    }
  };

  const handleCreateCustom = () => {
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/ec7cf0ec-5098-4120-a457-e76f87ea854b',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'TrainAnywayModal.jsx:48',message:'handleCreateCustom called',data:{isOpen,showBuilder:true},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'B'})}).catch(()=>{});
    // #endregion
    setShowBuilder(true);
  };

  const handleBuilderComplete = (workout) => {
    onWorkoutReady?.(workout);
    onClose();
  };

  const handleBuilderCancel = () => {
    setShowBuilder(false);
  };

  if (!isOpen) return null;

  // Show workout builder
  if (showBuilder) {
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/ec7cf0ec-5098-4120-a457-e76f87ea854b',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'TrainAnywayModal.jsx:65',message:'Rendering WorkoutBuilder branch',data:{showBuilder,isOpen},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'C'})}).catch(()=>{});
    // #endregion
    return (
      <WorkoutBuilder
        onComplete={handleBuilderComplete}
        onCancel={handleBuilderCancel}
      />
    );
  }

  // Format next workout date for display
  const formattedNextDate = nextWorkoutDate
    ? new Date(nextWorkoutDate).toLocaleDateString('en', {
        weekday: 'long',
        month: 'short',
        day: 'numeric',
      })
    : null;

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full sm:max-w-md bg-surface-card rounded-t-2xl sm:rounded-2xl 
                      border border-border shadow-2xl animate-in-up">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-border">
          <div>
            <h2 className="text-xl font-heading font-bold text-text-primary">
              Train Anyway
            </h2>
            <p className="text-sm text-text-muted mt-1">
              It's a rest day, but you want to train
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-text-muted hover:text-text-primary 
                       hover:bg-surface-elevated transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Options */}
        <div className="p-5 space-y-3">
          {/* Option 1: Move next workout */}
          {nextWorkoutDate && (
            <button
              onClick={handleMoveWorkout}
              disabled={swapMutation.isPending}
              className="w-full p-4 rounded-xl border border-border bg-surface-elevated 
                         hover:border-accent hover:bg-surface-hover transition-all text-left
                         disabled:opacity-50 disabled:cursor-not-allowed group"
            >
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center flex-shrink-0 
                                group-hover:bg-accent/20 transition-colors">
                  <svg className="w-5 h-5 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                          d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                  </svg>
                </div>
                <div className="flex-1">
                  <h3 className="font-heading font-semibold text-text-primary group-hover:text-accent transition-colors">
                    Move scheduled workout to today
                  </h3>
                  <p className="text-sm text-text-secondary mt-1">
                    Swap today's rest with your {formattedNextDate} workout
                  </p>
                </div>
                {swapMutation.isPending && (
                  <div className="w-5 h-5 border-2 border-accent border-t-transparent rounded-full animate-spin" />
                )}
              </div>
            </button>
          )}

          {/* Option 2: Create custom workout */}
          <button
            onClick={handleCreateCustom}
            className="w-full p-4 rounded-xl border border-border bg-surface-elevated 
                       hover:border-accent hover:bg-surface-hover transition-all text-left group"
          >
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center flex-shrink-0 
                              group-hover:bg-accent/20 transition-colors">
                <svg className="w-5 h-5 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                        d="M12 4v16m8-8H4" />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="font-heading font-semibold text-text-primary group-hover:text-accent transition-colors">
                  Create your own workout
                </h3>
                <p className="text-sm text-text-secondary mt-1">
                  Build a custom workout from scratch
                </p>
                <p className="text-xs text-text-muted mt-2 italic">
                  This won't affect your scheduled training plan
                </p>
              </div>
            </div>
          </button>
        </div>

        {/* Error display */}
        {swapMutation.isError && (
          <div className="px-5 pb-5">
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30">
              <p className="text-sm text-red-400">
                {swapMutation.error?.message || 'Failed to swap workout. Please try again.'}
              </p>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="p-4 border-t border-border bg-surface-elevated/50 rounded-b-2xl">
          <button
            onClick={onClose}
            className="w-full py-2.5 text-sm text-text-muted hover:text-text-secondary transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
