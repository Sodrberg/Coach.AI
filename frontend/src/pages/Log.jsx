import { useForm } from 'react-hook-form';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTodayWorkout, useLogWorkout, getUserId } from '../hooks/useApi';
import { useToast } from '../hooks/useToast';
import LoadingSpinner from '../components/LoadingSpinner';
import { useState } from 'react';

const rpeDescriptions = {
  1: 'Very Light',
  2: 'Light',
  3: 'Light-Moderate',
  4: 'Moderate',
  5: 'Moderate',
  6: 'Moderate-Hard',
  7: 'Hard',
  8: 'Very Hard',
  9: 'Very Hard',
  10: 'Maximum',
};

const rpeColors = {
  1: 'bg-secondary',
  2: 'bg-secondary',
  3: 'bg-secondary',
  4: 'bg-secondary',
  5: 'bg-accent',
  6: 'bg-accent',
  7: 'bg-accent',
  8: 'bg-danger',
  9: 'bg-danger',
  10: 'bg-danger',
};

export default function Log() {
  const navigate = useNavigate();
  const location = useLocation();
  const toast = useToast();
  const passedWorkout = location.state?.workout;
  const passedDurationMin = location.state?.durationMin;
  const { data: fetchedWorkout, isLoading } = useTodayWorkout();
  const workout = passedWorkout || fetchedWorkout;
  const logWorkout = useLogWorkout();
  const [selectedRpe, setSelectedRpe] = useState(7);
  const [completionData, setCompletionData] = useState(null);

  const { register, handleSubmit } = useForm({
    defaultValues: {
      completed: true,
      feedback: 'felt_great',
      intensity: 'medium',
      notes: '',
    },
  });

  const onSubmit = (data) => {
    const exercises = [];
    if (workout?.sections) {
      workout.sections.forEach((section) => {
        section.items.forEach((item) => {
          exercises.push({
            name: item.name,
            sets: item.sets,
            reps: item.reps,
            weight_kg: item.weight_kg,
            duration_per_set_sec: item.duration_min ? item.duration_min * 60 : null,
            distance_km: item.distance_km,
            rest_sec: item.rest_sec,
          });
        });
      });
    }

    const log = {
      log_id: `log_${Date.now()}`,
      user_id: getUserId(),
      workout_id: workout?.workout_id,
      date: new Date().toISOString(),
      completed: data.completed,
      workout_type: workout?.workout_type || 'general',
      duration_min: parseInt(data.duration_min) || passedDurationMin || workout?.estimated_duration_min || 45,
      rpe_actual: selectedRpe,
      exercises,
      feedback: data.feedback,
      intensity: data.intensity,
      notes: data.notes || null,
    };

    logWorkout.mutate(log, {
      onSuccess: (response) => {
        toast.success('Workout logged!');
        setCompletionData(response);
      },
    });
  };

  if (isLoading && !passedWorkout) {
    return <LoadingSpinner message="Loading workout..." />;
  }

  // Show completion screen after successful log
  if (completionData) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4 animate-in-up">
        {/* Success Animation */}
        <div className="relative mb-8">
          <div className="w-24 h-24 rounded-full bg-secondary/20 flex items-center justify-center">
            <svg className="w-12 h-12 text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div className="absolute -top-1 -right-1 w-8 h-8 rounded-full bg-accent flex items-center justify-center shadow-glow-sm">
            <span className="text-lg">🎉</span>
          </div>
        </div>

        {/* Completion Message */}
        <h1 className="text-2xl font-heading font-bold text-text-primary mb-3">
          {completionData.message || "Workout Logged!"}
        </h1>
        
        <p className="text-text-secondary mb-10 max-w-sm">
          Great job staying consistent with your training!
        </p>

        {/* Next Workout Info */}
        {completionData.next_workout_message && (
          <div className="card w-full max-w-sm mb-10">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center flex-shrink-0">
                <span className="text-xl">📅</span>
              </div>
              <div className="text-left">
                <p className="font-heading font-semibold text-text-primary">
                  {completionData.next_workout_message}
                </p>
                {completionData.next_workout_type && (
                  <p className="text-sm text-text-secondary capitalize mt-0.5">
                    {completionData.next_workout_type} workout
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* No Next Workout */}
        {!completionData.next_workout_message && completionData.next_workout_date && (
          <div className="card w-full max-w-sm mb-10">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center flex-shrink-0">
                <span className="text-xl">📅</span>
              </div>
              <div className="text-left">
                <p className="font-heading font-semibold text-text-primary">
                  Next workout: {new Date(completionData.next_workout_date).toLocaleDateString('en', {
                    weekday: 'long',
                    month: 'short',
                    day: 'numeric'
                  })}
                </p>
                {completionData.next_workout_type && (
                  <p className="text-sm text-text-secondary capitalize mt-0.5">
                    {completionData.next_workout_type} workout
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Done Button */}
        <button
          onClick={() => navigate('/')}
          className="btn-primary px-12 py-3.5"
        >
          Done
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in">
      <div className="mb-8">
        <h1 className="text-2xl font-heading font-bold text-text-primary">Log Workout</h1>
        <p className="text-text-secondary mt-2">
          {workout?.title || "Record your workout"}
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Completion Status */}
        <div className="card">
          <h2 className="section-header">Did you complete the workout?</h2>
          <div className="flex gap-3">
            <label className="flex-1">
              <input
                type="radio"
                {...register('completed')}
                value={true}
                className="sr-only peer"
              />
              <div className="selection-card text-center peer-checked:selection-card-active peer-checked:border-secondary peer-checked:bg-secondary/10">
                <span className="text-3xl block mb-2">✓</span>
                <span className="font-heading font-medium">Yes, completed!</span>
              </div>
            </label>
            <label className="flex-1">
              <input
                type="radio"
                {...register('completed')}
                value={false}
                className="sr-only peer"
              />
              <div className="selection-card text-center peer-checked:border-danger peer-checked:bg-danger/10">
                <span className="text-3xl block mb-2">⏭️</span>
                <span className="font-heading font-medium">Skipped</span>
              </div>
            </label>
          </div>
        </div>

        {/* RPE */}
        <div className="card">
          <h2 className="section-header">How hard was it?</h2>
          <p className="text-sm text-text-secondary mb-4">
            RPE {selectedRpe} — {rpeDescriptions[selectedRpe]}
          </p>
          <div className="grid grid-cols-5 sm:grid-cols-10 gap-1.5">
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((rpe) => (
              <button
                key={rpe}
                type="button"
                onClick={() => setSelectedRpe(rpe)}
                aria-label={`RPE ${rpe} - ${rpeDescriptions[rpe]}`}
                className={`py-3.5 sm:py-3 rounded-lg font-heading font-semibold text-sm transition-all ${
                  selectedRpe === rpe
                    ? `${rpeColors[rpe]} text-white shadow-sm`
                    : 'bg-surface-elevated text-text-muted hover:bg-surface-hover hover:text-text-secondary'
                }`}
              >
                {rpe}
              </button>
            ))}
          </div>
        </div>

        {/* Duration */}
        <div className="card">
          <h2 className="section-header">Actual Duration</h2>
          <div className="flex items-center gap-3">
            <input
              type="number"
              {...register('duration_min')}
              defaultValue={passedDurationMin || workout?.estimated_duration_min || 45}
              className="input w-28"
              min={1}
              aria-label="Workout duration in minutes"
            />
            <span className="text-text-secondary">minutes</span>
          </div>
        </div>

        {/* How did you feel? */}
        <div className="card">
          <h2 className="section-header">How did you feel?</h2>
          <div className="grid grid-cols-2 gap-3">
            {[
              { value: 'felt_great', label: 'Felt great!', icon: '💪' },
              { value: 'sore', label: 'Sore', icon: '😣' },
              { value: 'tired', label: 'Tired', icon: '😴' },
              { value: 'pain', label: 'Had pain', icon: '🤕' },
            ].map((option) => (
              <label key={option.value}>
                <input
                  type="radio"
                  {...register('feedback')}
                  value={option.value}
                  className="sr-only peer"
                />
                <div className="selection-card text-center peer-checked:selection-card-active">
                  <span className="text-2xl block mb-2">{option.icon}</span>
                  <span className="text-sm font-heading font-medium">{option.label}</span>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Notes */}
        <div className="card">
          <h2 className="section-header">Notes (optional)</h2>
          <textarea
            {...register('notes')}
            placeholder="Any notes about the workout..."
            className="input min-h-[100px] resize-none"
          />
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={logWorkout.isPending}
          className="btn-primary w-full py-4 text-base disabled:opacity-50"
        >
          {logWorkout.isPending ? 'Saving...' : 'Save Workout Log'}
        </button>

        {logWorkout.isError && (
          <p className="text-danger text-center text-sm">
            Failed to save. Please try again.
          </p>
        )}
      </form>
    </div>
  );
}
