import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getUserId, useMoveWorkout, useWorkoutByDate } from '../hooks/useApi';
import LoadingSpinner from '../components/LoadingSpinner';
import PlanDetailModal from '../components/PlanDetailModal';
import WorkoutCard from '../components/WorkoutCard';
import { Link } from 'react-router-dom';

export default function Plan() {
  const userId = getUserId();
  const [selectedDay, setSelectedDay] = useState(null);
  const [detailDay, setDetailDay] = useState(null);
  const [showPlanDetail, setShowPlanDetail] = useState(false);
  const moveMutation = useMoveWorkout();
  const detailDate = detailDay && !detailDay.is_rest_day ? detailDay.date : null;
  const { data: workoutDetail, isLoading: isLoadingWorkout } = useWorkoutByDate(detailDate);

  const { data: plan, isLoading, error } = useQuery({
    queryKey: ['plan', userId],
    queryFn: async () => {
      const res = await fetch(`/api/v1/plan/complete?user_id=${userId}`);
      if (!res.ok) throw new Error('Failed to fetch plan');
      return res.json();
    },
    retry: false,
  });

  // Close detail modal on Escape
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') setDetailDay(null);
    };
    if (detailDay) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [detailDay]);

  const handleDayClick = (day) => {
    const today = new Date().toISOString().split('T')[0];
    if (day.date < today) return;

    if (selectedDay) {
      // In move mode: complete the move or deselect
      if (selectedDay.date === day.date) {
        setSelectedDay(null);
      } else {
        moveMutation.mutate(
          { fromDate: selectedDay.date, toDate: day.date },
          {
            onSuccess: () => setSelectedDay(null),
            onError: (err) => {
              console.error('Failed to move workout:', err);
              setSelectedDay(null);
            },
          }
        );
      }
    } else {
      // Normal mode: open detail modal
      setDetailDay(day);
    }
  };

  const handleStartMove = () => {
    // Enter move mode from the detail modal
    setSelectedDay(detailDay);
    setDetailDay(null);
  };

  const cancelSelection = () => {
    setSelectedDay(null);
  };

  if (isLoading) {
    return <LoadingSpinner message="Loading your plan..." />;
  }

  if (error || !plan) {
    return (
      <div className="text-center py-16 animate-in">
        <div className="w-16 h-16 rounded-full bg-surface-card flex items-center justify-center mx-auto mb-6">
          <span className="text-2xl">📋</span>
        </div>
        <h2 className="text-xl font-heading font-semibold text-text-primary mb-3">
          No Plan Yet
        </h2>
        <p className="text-text-secondary mb-8 max-w-sm mx-auto">
          Complete your profile and goal to generate a personalized training plan.
        </p>
        <Link to="/profile" className="btn-primary">
          Get Started
        </Link>
      </div>
    );
  }

  const { high_level_plan, current_block } = plan;

  // Group days by week
  const weeks = [];
  if (current_block?.day_slots) {
    for (let i = 0; i < current_block.day_slots.length; i += 7) {
      weeks.push(current_block.day_slots.slice(i, i + 7));
    }
  }

  const today = new Date().toISOString().split('T')[0];

  return (
    <div className="space-y-6 animate-in">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-heading font-bold text-text-primary">Your Training Plan</h1>
        <p className="text-text-secondary mt-2">
          {high_level_plan?.duration_weeks || 8} week plan • Block {current_block?.block_number || 1}
        </p>
      </div>

      {/* Plan Summary */}
      {high_level_plan && (
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <h2 className="section-header !mb-0">Plan Overview</h2>
            <button
              onClick={() => setShowPlanDetail(true)}
              className="text-sm text-accent font-medium hover:text-accent-dark transition-colors flex items-center gap-1.5"
            >
              View Plan
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
          {high_level_plan.phase_breakdown && (
            <div className="flex flex-wrap gap-2">
              {high_level_plan.phase_breakdown.map((phase, index) => (
                <span
                  key={index}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-surface-elevated border border-border text-sm"
                >
                  <span className="text-accent font-heading font-semibold text-xs">Wk {phase.weeks}</span>
                  <span className="text-text-secondary">{phase.focus}</span>
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      <PlanDetailModal
        isOpen={showPlanDetail}
        onClose={() => setShowPlanDetail(false)}
        overviewMarkdown={high_level_plan?.overview_markdown}
        phaseBreakdown={high_level_plan?.phase_breakdown}
      />

      {/* Calendar View */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="section-header !mb-0">Current Block Schedule</h2>
          {selectedDay && (
            <button
              onClick={cancelSelection}
              className="text-sm text-text-muted hover:text-text-primary transition-colors"
            >
              Cancel
            </button>
          )}
        </div>

        {/* Selection instruction banner */}
        {selectedDay && (
          <div className="mb-4 p-3 rounded-lg bg-accent/10 border border-accent/30 flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center flex-shrink-0">
              <svg className="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
              </svg>
            </div>
            <div className="flex-1">
              <p className="text-sm text-accent font-medium">
                Moving {selectedDay.workout_type} workout from{' '}
                {new Date(selectedDay.date).toLocaleDateString('en', { weekday: 'short', month: 'short', day: 'numeric' })}
              </p>
              <p className="text-xs text-text-muted mt-0.5">
                Tap another day to move it there, or tap the same day to cancel
              </p>
            </div>
            {moveMutation.isPending && (
              <div className="w-5 h-5 border-2 border-accent/30 border-t-accent rounded-full animate-spin" />
            )}
          </div>
        )}

        {/* Error message */}
        {moveMutation.isError && (
          <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30">
            <p className="text-sm text-red-400">
              Failed to move workout. Please try again.
            </p>
          </div>
        )}
        
        {weeks.map((week, weekIndex) => (
          <div key={weekIndex} className="mb-8 last:mb-0">
            <h3 className="text-sm font-heading font-medium text-text-muted uppercase tracking-wide mb-3">
              Week {weekIndex + 1}
            </h3>
            <div className="grid grid-cols-7 gap-2">
              {week.map((day) => {
                const isToday = day.date === today;
                const isPast = day.date < today;
                const isSelected = selectedDay?.date === day.date;
                const isValidTarget = selectedDay && !isPast && selectedDay.date !== day.date;
                const tileStyle = day.is_rest_day
                  ? 'bg-surface-elevated'
                  : 'bg-accent/15';

                return (
                  <button
                    key={day.day_number}
                    onClick={() => handleDayClick(day)}
                    disabled={isPast || moveMutation.isPending}
                    className={`relative p-2 sm:p-3 rounded-lg text-center transition-all ${tileStyle} ${
                      isToday ? 'ring-2 ring-accent ring-offset-2 ring-offset-surface-card' : ''
                    } ${isPast ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer hover:scale-105'} ${
                      isSelected ? 'ring-2 ring-accent scale-105' : ''
                    } ${isValidTarget ? 'ring-1 ring-accent/50 ring-dashed' : ''}`}
                  >
                    <div className="text-xs text-text-muted font-medium">
                      {new Date(day.date).toLocaleDateString('en', { weekday: 'short' })}
                    </div>
                    <div className="text-sm font-heading font-semibold text-text-primary mt-0.5">
                      {new Date(day.date).getDate()}
                    </div>
                    {day.is_rest_day && (
                      <div className="text-xs mt-1 text-text-muted">Rest</div>
                    )}
                    {day.status === 'completed' && (
                      <span className="absolute top-1 right-1 w-4 h-4 rounded-full bg-secondary flex items-center justify-center">
                        <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </svg>
                      </span>
                    )}
                    {isSelected && (
                      <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-accent flex items-center justify-center">
                        <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Day Detail Modal */}
      {detailDay && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
          onClick={() => setDetailDay(null)}
        >
          <div
            className="bg-surface-card border border-border rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6 shadow-xl animate-in"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-heading font-semibold text-text-primary">
                {new Date(detailDay.date).toLocaleDateString('en', {
                  weekday: 'long',
                  month: 'long',
                  day: 'numeric',
                })}
              </h3>
              <button
                onClick={() => setDetailDay(null)}
                className="w-8 h-8 rounded-full bg-surface-elevated flex items-center justify-center text-text-muted hover:text-text-primary transition-colors"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {detailDay.is_rest_day ? (
              <p className="text-text-secondary">Rest day — recover and recharge.</p>
            ) : (
              <div className="space-y-4">
                {/* Slot metadata */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3 rounded-lg bg-surface-elevated">
                  <div>
                    <span className="text-text-muted text-xs block">Type</span>
                    <span className="text-text-primary text-sm font-medium capitalize">{detailDay.workout_type}</span>
                  </div>
                  {detailDay.target_duration_min && (
                    <div>
                      <span className="text-text-muted text-xs block">Duration</span>
                      <span className="text-text-primary text-sm font-medium">{detailDay.target_duration_min} min</span>
                    </div>
                  )}
                  {detailDay.target_distance_km && (
                    <div>
                      <span className="text-text-muted text-xs block">Distance</span>
                      <span className="text-text-primary text-sm font-medium">{detailDay.target_distance_km} km</span>
                    </div>
                  )}
                  {detailDay.intensity_target && (
                    <div>
                      <span className="text-text-muted text-xs block">Intensity</span>
                      <span className="text-text-primary text-sm font-medium">{detailDay.intensity_target}</span>
                    </div>
                  )}
                </div>

                {/* Workout detail */}
                {isLoadingWorkout ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="w-6 h-6 border-2 border-accent/30 border-t-accent rounded-full animate-spin" />
                  </div>
                ) : workoutDetail?.sections ? (
                  <WorkoutCard workout={workoutDetail} editable={false} />
                ) : workoutDetail?.status === 'not_generated' ? (
                  <div className="text-center py-6 px-4 rounded-lg bg-surface-elevated border border-border">
                    <p className="text-text-secondary text-sm">
                      This workout will be generated closer to the date.
                    </p>
                  </div>
                ) : null}
              </div>
            )}

            <div className="mt-6 flex gap-3">
              {!detailDay.is_rest_day && detailDay.date >= today && (
                <button
                  onClick={handleStartMove}
                  className="flex-1 px-4 py-2.5 rounded-lg bg-surface-elevated border border-border text-text-primary text-sm font-medium hover:bg-surface-elevated/80 transition-colors"
                >
                  Move Workout
                </button>
              )}
              <button
                onClick={() => setDetailDay(null)}
                className="flex-1 px-4 py-2.5 rounded-lg bg-accent text-white text-sm font-medium hover:bg-accent-dark transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
