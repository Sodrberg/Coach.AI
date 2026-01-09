import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { useGoal, useSaveGoal, useGeneratePlan, getUserId } from '../hooks/useApi';
import LoadingSpinner from '../components/LoadingSpinner';
import { useState } from 'react';

const goalTypes = [
  { value: 'race', label: 'Race / Event', icon: '🏆' },
  { value: 'strength', label: 'Build Strength', icon: '💪' },
  { value: 'weight_loss', label: 'Lose Weight', icon: '⚖️' },
  { value: 'general_fitness', label: 'General Fitness', icon: '🎯' },
];

const priorities = [
  { value: 'performance', label: 'Performance', description: 'Push for best results' },
  { value: 'health', label: 'Health', description: 'Sustainable long-term approach' },
  { value: 'enjoyment', label: 'Enjoyment', description: 'Keep training fun and varied' },
];

export default function Goal() {
  const navigate = useNavigate();
  const { data: goal, isLoading } = useGoal();
  const saveGoal = useSaveGoal();
  const generatePlan = useGeneratePlan();
  const [isGenerating, setIsGenerating] = useState(false);

  const { register, handleSubmit, formState: { errors }, watch } = useForm({
    defaultValues: goal || {
      goal_type: 'general_fitness',
      target_event: '',
      target_date: new Date(Date.now() + 60 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      priority: 'health',
    },
  });

  const selectedGoalType = watch('goal_type');

  const onSubmit = async (data) => {
    const userId = getUserId();
    const goalId = `goal_${Date.now()}`;
    
    const goalData = {
      ...data,
      goal_id: goalId,
      user_id: userId,
      current_baseline: null,
    };

    saveGoal.mutate(goalData, {
      onSuccess: async () => {
        setIsGenerating(true);
        generatePlan.mutate(
          { userId, goalId },
          {
            onSuccess: () => {
              navigate('/');
            },
            onError: () => {
              setIsGenerating(false);
            },
          }
        );
      },
    });
  };

  if (isLoading) {
    return <LoadingSpinner message="Loading goal..." />;
  }

  if (isGenerating) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center animate-in">
        <LoadingSpinner size="lg" message="Creating your personalized training plan..." />
        <p className="text-text-secondary mt-6 max-w-md">
          Our AI coach is analyzing your profile and crafting an 8-week plan
          tailored to your goals.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in">
      <div className="mb-8">
        <h1 className="text-2xl font-heading font-bold text-text-primary">Set Your Goal</h1>
        <p className="text-text-secondary mt-2">
          What do you want to achieve? We'll create a plan to get you there.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Goal Type */}
        <div className="card">
          <h2 className="section-header">What's your goal?</h2>
          
          <div className="grid grid-cols-2 gap-3">
            {goalTypes.map((type) => (
              <label
                key={type.value}
                className={`selection-card ${
                  selectedGoalType === type.value ? 'selection-card-active' : ''
                }`}
              >
                <input
                  type="radio"
                  {...register('goal_type')}
                  value={type.value}
                  className="sr-only"
                />
                <span className="text-3xl block mb-3">{type.icon}</span>
                <span className="font-heading font-medium text-text-primary">{type.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Target Event (if race) */}
        {selectedGoalType === 'race' && (
          <div className="card animate-in">
            <h2 className="section-header">Target Event</h2>
            <input
              type="text"
              {...register('target_event')}
              placeholder="e.g., Vasaloppet 90km, Boston Marathon"
              className="input"
            />
          </div>
        )}

        {/* Target Date */}
        <div className="card">
          <h2 className="section-header">Target Date</h2>
          <p className="text-text-secondary text-sm mb-4">
            When do you want to achieve this goal?
          </p>
          <input
            type="date"
            {...register('target_date', { required: true })}
            className="input"
            min={new Date().toISOString().split('T')[0]}
          />
          {errors.target_date && (
            <span className="text-danger text-sm mt-2 block">Please select a target date</span>
          )}
        </div>

        {/* Priority */}
        <div className="card">
          <h2 className="section-header">What's your priority?</h2>
          
          <div className="space-y-3">
            {priorities.map((p) => (
              <label
                key={p.value}
                className={`flex items-center selection-card ${
                  watch('priority') === p.value ? 'selection-card-active' : ''
                }`}
              >
                <input
                  type="radio"
                  {...register('priority')}
                  value={p.value}
                  className="sr-only"
                />
                <div className="flex-1">
                  <span className="font-heading font-medium text-text-primary block">{p.label}</span>
                  <p className="text-sm text-text-secondary mt-0.5">{p.description}</p>
                </div>
                {watch('priority') === p.value && (
                  <div className="w-5 h-5 rounded-full bg-accent flex items-center justify-center ml-3">
                    <svg className="w-3 h-3 text-surface-base" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                )}
              </label>
            ))}
          </div>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={saveGoal.isPending}
          className="btn-primary w-full py-4 text-base disabled:opacity-50"
        >
          {saveGoal.isPending ? 'Saving...' : 'Generate My Training Plan'}
        </button>

        {(saveGoal.isError || generatePlan.isError) && (
          <p className="text-danger text-center text-sm">
            Something went wrong. Please try again.
          </p>
        )}
      </form>
    </div>
  );
}
