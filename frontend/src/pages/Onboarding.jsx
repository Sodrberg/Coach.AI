import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuickOnboard, getUserId } from '../hooks/useApi';
import LoadingSpinner from '../components/LoadingSpinner';

const daysOptions = [3, 4, 5, 6];
const weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
const weekdayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

const typeColors = {
  strength: 'bg-strength/20 text-strength',
  endurance: 'bg-endurance/20 text-endurance',
  intervals: 'bg-intervals/20 text-intervals',
  recovery: 'bg-recovery/20 text-recovery',
  tempo: 'bg-orange-400/20 text-orange-400',
  threshold: 'bg-pink-500/20 text-pink-500',
};

export default function Onboarding() {
  const navigate = useNavigate();
  const quickOnboard = useQuickOnboard();
  const [goalText, setGoalText] = useState('');
  const [daysPerWeek, setDaysPerWeek] = useState(4);
  const [trainingType, setTrainingType] = useState(null);
  const [gymAccess, setGymAccess] = useState(null);
  const [preferredDays, setPreferredDays] = useState([]);
  const [result, setResult] = useState(null);

  const toggleDay = (day) => {
    setPreferredDays((prev) =>
      prev.includes(day) ? prev.filter((d) => d !== day) : [...prev, day]
    );
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const userId = getUserId();

    quickOnboard.mutate(
      {
        user_id: userId,
        goal_text: goalText,
        training_days_per_week: daysPerWeek,
        training_type_preference: trainingType || null,
        gym_access: gymAccess || null,
        preferred_training_days: preferredDays.length > 0 ? preferredDays : null,
      },
      {
        onSuccess: (data) => {
          if (data?.error_code) {
            return;
          }
          setResult(data);
        },
      }
    );
  };

  // Loading phase
  if (quickOnboard.isPending) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center animate-in">
        <LoadingSpinner size="lg" message="Creating your personalized plan..." />
        <p className="text-text-secondary mt-6 max-w-md">
          Our AI coach is analyzing your goal and crafting a training plan
          tailored just for you.
        </p>
      </div>
    );
  }

  // Result phase
  if (result) {
    const { complete_plan } = result;
    const block = complete_plan.current_block;
    const overview = complete_plan.high_level_plan.overview_markdown;

    // Group day slots by week
    const weeks = [];
    for (let i = 0; i < block.day_slots.length; i += 7) {
      weeks.push(block.day_slots.slice(i, i + 7));
    }

    return (
      <div className="space-y-6 animate-in-up">
        <div className="mb-8 text-center">
          <div className="w-16 h-16 rounded-2xl bg-secondary/20 flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h1 className="text-2xl font-heading font-bold text-text-primary">
            Your Plan is Ready!
          </h1>
          <p className="text-text-secondary mt-2">
            Here's your 3-week training schedule
          </p>
        </div>

        {/* Overview / Reasoning */}
        <div className="card">
          <h2 className="section-header">Plan Overview</h2>
          <div className="text-text-secondary text-sm leading-relaxed whitespace-pre-line">
            {overview}
          </div>
        </div>

        {/* 3-Week Schedule */}
        <div className="card">
          <h2 className="section-header">3-Week Schedule</h2>
          <div className="space-y-6">
            {weeks.map((week, weekIdx) => (
              <div key={weekIdx}>
                <p className="text-text-muted text-xs font-medium uppercase tracking-wide mb-3">
                  Week {weekIdx + 1}
                </p>
                <div className="space-y-2">
                  {week.map((slot) => {
                    const date = new Date(slot.date + 'T00:00:00');
                    const dayName = date.toLocaleDateString('en', { weekday: 'short' });
                    const dateStr = date.toLocaleDateString('en', { month: 'short', day: 'numeric' });

                    return (
                      <div
                        key={slot.day_number}
                        className={`flex items-center gap-3 px-3 py-2.5 rounded-lg ${
                          slot.is_rest_day
                            ? 'bg-surface-elevated/50'
                            : 'bg-surface-card border border-border'
                        }`}
                      >
                        <div className="w-16 flex-shrink-0">
                          <p className="text-text-primary text-sm font-medium">{dayName}</p>
                          <p className="text-text-muted text-xs">{dateStr}</p>
                        </div>
                        {slot.is_rest_day ? (
                          <p className="text-text-muted text-sm">Rest day</p>
                        ) : (
                          <div className="flex items-center gap-2 flex-1">
                            <span className={`text-xs font-medium px-2 py-0.5 rounded capitalize ${
                              typeColors[slot.workout_type] || 'bg-accent/20 text-accent'
                            }`}>
                              {slot.workout_type}
                            </span>
                            {slot.target_duration_min && (
                              <span className="text-text-muted text-xs">
                                {slot.target_duration_min} min
                              </span>
                            )}
                            {slot.intensity_target && (
                              <span className="text-text-muted text-xs">
                                {slot.intensity_target}
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Start Training */}
        <button
          onClick={() => navigate('/')}
          className="btn-primary w-full py-4 text-base"
        >
          Start Training
        </button>
      </div>
    );
  }

  // Input phase
  return (
    <div className="space-y-6 animate-in-up">
      <div className="mb-8 text-center">
        <div className="w-20 h-20 rounded-2xl bg-surface-card border border-border flex items-center justify-center mx-auto mb-6 shadow-glow-sm">
          <span className="text-accent font-heading font-bold text-3xl">TC</span>
        </div>
        <h1 className="text-2xl font-heading font-bold text-text-primary">
          Let's get you started
        </h1>
        <p className="text-text-secondary mt-2 max-w-md mx-auto">
          Tell us about your goal and we'll create a personalized training plan in seconds.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Goal Text */}
        <div className="card">
          <h2 className="section-header">What's your goal?</h2>
          <p className="text-text-secondary text-sm mb-4">
            Describe what you want to achieve in your own words.
          </p>
          <textarea
            value={goalText}
            onChange={(e) => setGoalText(e.target.value)}
            placeholder='e.g., "I want to run Vasaloppet in March" or "Get stronger and build muscle over the next 3 months"'
            className="input min-h-[120px] resize-none"
            required
            minLength={3}
            maxLength={500}
          />
        </div>

        {/* Days Per Week */}
        <div className="card">
          <h2 className="section-header">How many days per week can you train?</h2>
          <div className="grid grid-cols-4 gap-3">
            {daysOptions.map((d) => (
              <button
                key={d}
                type="button"
                onClick={() => setDaysPerWeek(d)}
                className={`selection-card text-center ${
                  daysPerWeek === d ? 'selection-card-active' : ''
                }`}
              >
                <span className="text-2xl font-heading font-bold text-text-primary block">{d}</span>
                <span className="text-text-muted text-xs">days</span>
              </button>
            ))}
          </div>
        </div>

        {/* Training Type */}
        <div className="card">
          <h2 className="section-header">What type of training do you prefer?</h2>
          <p className="text-text-secondary text-sm mb-4">Optional — helps us tailor your plan.</p>
          <div className="grid grid-cols-3 gap-3">
            {[
              { value: 'cardio', label: 'Cardio' },
              { value: 'strength', label: 'Strength' },
              { value: 'both', label: 'Both' },
            ].map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setTrainingType(trainingType === opt.value ? null : opt.value)}
                className={`selection-card text-center ${
                  trainingType === opt.value ? 'selection-card-active' : ''
                }`}
              >
                <span className="text-sm font-medium text-text-primary">{opt.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Gym Access */}
        <div className="card">
          <h2 className="section-header">Do you have gym access?</h2>
          <p className="text-text-secondary text-sm mb-4">Optional — determines available equipment.</p>
          <div className="grid grid-cols-3 gap-3">
            {[
              { value: 'gym', label: 'Gym' },
              { value: 'no_gym', label: 'No Gym' },
              { value: 'both', label: 'Both' },
            ].map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setGymAccess(gymAccess === opt.value ? null : opt.value)}
                className={`selection-card text-center ${
                  gymAccess === opt.value ? 'selection-card-active' : ''
                }`}
              >
                <span className="text-sm font-medium text-text-primary">{opt.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Preferred Weekdays */}
        <div className="card">
          <h2 className="section-header">Which days do you prefer to train?</h2>
          <p className="text-text-secondary text-sm mb-4">Optional — select your preferred training days.</p>
          <div className="flex flex-wrap gap-2">
            {weekdays.map((day, i) => (
              <button
                key={day}
                type="button"
                onClick={() => toggleDay(day)}
                className={`selection-card text-center py-3 w-[calc(25%-6px)] sm:w-[calc(14.28%-7px)] ${
                  preferredDays.includes(day) ? 'selection-card-active' : ''
                }`}
              >
                <span className="text-xs font-medium text-text-primary">{weekdayLabels[i]}</span>
              </button>
            ))}
          </div>
          {preferredDays.length > 0 && preferredDays.length !== daysPerWeek && (
            <p className="text-text-muted text-xs mt-2">
              You selected {preferredDays.length} days but chose {daysPerWeek} days/week above.
            </p>
          )}
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={!goalText.trim() || quickOnboard.isPending}
          className="btn-primary w-full py-4 text-base disabled:opacity-50"
        >
          Generate My Plan
        </button>

        {quickOnboard.isError && (
          <p className="text-danger text-center text-sm">
            Something went wrong. Please try again.
          </p>
        )}
      </form>
    </div>
  );
}
