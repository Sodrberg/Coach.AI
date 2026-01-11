import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getUserId, useMoveWorkout } from '../hooks/useApi';
import LoadingSpinner from '../components/LoadingSpinner';
import { Link } from 'react-router-dom';

const typeColors = {
  strength: 'bg-strength/20 text-strength',
  endurance: 'bg-endurance/20 text-endurance',
  intervals: 'bg-intervals/20 text-intervals',
  recovery: 'bg-recovery/20 text-recovery',
  tempo: 'bg-orange-400/20 text-orange-400',
  threshold: 'bg-pink-500/20 text-pink-500',
};

const typeBgColors = {
  strength: 'bg-strength/30',
  endurance: 'bg-endurance/30',
  intervals: 'bg-intervals/30',
  recovery: 'bg-recovery/30',
  tempo: 'bg-orange-400/30',
  threshold: 'bg-pink-500/30',
};

export default function Plan() {
  const userId = getUserId();
  const [selectedDay, setSelectedDay] = useState(null);
  const moveMutation = useMoveWorkout();
  
  const { data: plan, isLoading, error } = useQuery({
    queryKey: ['plan', userId],
    queryFn: async () => {
      const res = await fetch(`/api/v1/plan/complete?user_id=${userId}`);
      if (!res.ok) throw new Error('Failed to fetch plan');
      return res.json();
    },
    retry: false,
  });

  const handleDayClick = (day) => {
    // Don't allow selecting past days
    const today = new Date().toISOString().split('T')[0];
    if (day.date < today) return;

    if (!selectedDay) {
      // Only allow selecting workout days (not rest days)
      if (!day.is_rest_day) {
        setSelectedDay(day);
      }
    } else if (selectedDay.date === day.date) {
      // Deselect if clicking the same day
      setSelectedDay(null);
    } else {
      // Move the workout to the clicked day
      moveMutation.mutate(
        { fromDate: selectedDay.date, toDate: day.date },
        {
          onSuccess: () => {
            setSelectedDay(null);
          },
          onError: (error) => {
            console.error('Failed to move workout:', error);
            setSelectedDay(null);
          },
        }
      );
    }
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

      {/* Plan Overview */}
      {high_level_plan?.overview_markdown && (
        <div className="card">
          <h2 className="section-header">Overview</h2>
          <p className="text-text-secondary leading-relaxed whitespace-pre-line">
            {high_level_plan.overview_markdown.slice(0, 500)}
            {high_level_plan.overview_markdown.length > 500 && '...'}
          </p>
        </div>
      )}

      {/* Phase Breakdown */}
      {high_level_plan?.phase_breakdown && (
        <div className="card">
          <h2 className="section-header">Training Phases</h2>
          <div className="space-y-3">
            {high_level_plan.phase_breakdown.map((phase, index) => (
              <div
                key={index}
                className="flex items-start gap-4 p-4 bg-surface-elevated rounded-lg border border-border"
              >
                <div className="px-3 py-1.5 rounded-md bg-accent/10 text-accent text-sm font-heading font-semibold">
                  Wk {phase.weeks}
                </div>
                <div className="flex-1">
                  <p className="font-heading font-medium text-text-primary">{phase.focus}</p>
                  {phase.description && (
                    <p className="text-sm text-text-secondary mt-1">{phase.description}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

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
                const typeStyle = day.is_rest_day
                  ? 'bg-surface-elevated text-text-muted'
                  : typeBgColors[day.workout_type] || 'bg-surface-elevated';

                return (
                  <button
                    key={day.day_number}
                    onClick={() => handleDayClick(day)}
                    disabled={isPast || moveMutation.isPending}
                    className={`relative p-2 sm:p-3 rounded-lg text-center transition-all ${typeStyle} ${
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
                    {!day.is_rest_day && (
                      <div className="text-xs mt-1 capitalize font-medium truncate">
                        {day.workout_type?.slice(0, 4) || ''}
                      </div>
                    )}
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

      {/* Legend */}
      <div className="card">
        <h3 className="text-sm font-heading font-medium text-text-muted uppercase tracking-wide mb-4">Legend</h3>
        <div className="flex flex-wrap gap-3">
          {Object.entries(typeColors).map(([type, colorClass]) => (
            <div key={type} className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded ${colorClass.split(' ')[0]}`} />
              <span className="text-sm text-text-secondary capitalize">{type}</span>
            </div>
          ))}
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-surface-elevated border border-border" />
            <span className="text-sm text-text-secondary">Rest</span>
          </div>
        </div>
      </div>
    </div>
  );
}
