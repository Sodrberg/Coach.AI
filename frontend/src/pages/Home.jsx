import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useProfile, useGoal, useTodayWorkout } from '../hooks/useApi';
import LoadingSpinner from '../components/LoadingSpinner';
import TrainAnywayModal from '../components/TrainAnywayModal';

const typeStyles = {
  strength: 'text-strength',
  endurance: 'text-endurance',
  intervals: 'text-intervals',
  recovery: 'text-recovery',
};

export default function Home() {
  const { data: profile, isLoading: profileLoading, error: profileError } = useProfile();
  const { data: goal } = useGoal();
  const { data: workout, isLoading: workoutLoading, refetch } = useTodayWorkout();
  const [showTrainAnyway, setShowTrainAnyway] = useState(false);
  const [customWorkout, setCustomWorkout] = useState(null);
  const navigate = useNavigate();

  const isLoading = profileLoading || workoutLoading;

  // Use custom workout if available, otherwise use fetched workout
  const todayWorkout = customWorkout || workout;

  const handleWorkoutReady = (newWorkout) => {
    setShowTrainAnyway(false);
    setCustomWorkout(newWorkout);  // Store the workout directly for immediate display
    refetch();  // Still refetch to update cache
    navigate('/workout');
  };

  // If no profile, show onboarding
  if (!profileLoading && (profileError || !profile)) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh] text-center px-4 animate-in-up">
        <div className="w-20 h-20 rounded-2xl bg-surface-card border border-border flex items-center justify-center mb-8 shadow-glow-sm">
          <span className="text-accent font-heading font-bold text-3xl">TC</span>
        </div>
        <h1 className="text-3xl font-heading font-bold text-text-primary mb-4">
          Welcome to Training Coach
        </h1>
        <p className="text-text-secondary mb-10 max-w-md text-lg">
          Get personalized AI-powered training plans designed for your goals,
          schedule, and fitness level.
        </p>
        <Link to="/profile" className="btn-primary text-lg px-10 py-4">
          Get Started
        </Link>
      </div>
    );
  }

  if (isLoading) {
    return <LoadingSpinner message="Loading your dashboard..." />;
  }

  // Calculate days until goal
  const daysUntilGoal = goal?.target_date
    ? Math.ceil((new Date(goal.target_date) - new Date()) / (1000 * 60 * 60 * 24))
    : null;

  const today = new Date().toLocaleDateString('en', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  });

  const greeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <div className="space-y-6 animate-in">
      {/* Header */}
      <div className="mb-8">
        <p className="text-text-muted text-sm font-medium uppercase tracking-wide">{today}</p>
        <h1 className="text-2xl font-heading font-bold text-text-primary mt-2">
          {greeting()}{profile?.name ? `, ${profile.name.split(' ')[0]}` : ''}
        </h1>
      </div>

      {/* Goal Progress */}
      {goal && daysUntilGoal !== null && (
        <div className="card-glow relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-accent/5 to-transparent" />
          <div className="relative flex items-center justify-between">
            <div>
              <p className="text-text-muted text-sm font-medium uppercase tracking-wide">Your Goal</p>
              <p className="font-heading font-semibold text-text-primary text-lg mt-1">
                {goal.target_event || goal.goal_type.replace('_', ' ')}
              </p>
            </div>
            <div className="text-right">
              <p className="text-4xl font-heading font-bold text-accent">{daysUntilGoal}</p>
              <p className="text-text-muted text-sm">days to go</p>
            </div>
          </div>
        </div>
      )}

      {/* Today's Workout Summary */}
      <div className="card">
        <h2 className="section-header">Today's Workout</h2>
        
        {todayWorkout?.is_rest_day ? (
          <div className="text-center py-6">
            <div className="w-16 h-16 rounded-full bg-surface-elevated flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">🧘</span>
            </div>
            <p className="font-heading font-semibold text-text-primary text-lg">Rest Day</p>
            <p className="text-text-secondary mt-1">Take time to recover and recharge</p>
            <button
              onClick={() => setShowTrainAnyway(true)}
              className="btn-secondary mt-4"
            >
              Train Anyway
            </button>
          </div>
        ) : todayWorkout?.is_completed ? (
          <div className="text-center py-6">
            <div className="w-16 h-16 rounded-full bg-secondary/20 flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <p className="font-heading font-semibold text-text-primary text-lg">Workout Completed!</p>
            <p className="text-text-secondary mt-1">{todayWorkout.title}</p>
            {todayWorkout.next_workout_date && (
              <p className="text-text-muted text-sm mt-3">
                Next workout: {new Date(todayWorkout.next_workout_date).toLocaleDateString('en', {
                  weekday: 'long',
                  month: 'short',
                  day: 'numeric'
                })}
              </p>
            )}
            <Link to="/workout" className="text-accent hover:text-accent-light text-sm mt-3 inline-block transition-colors">
              View Details
            </Link>
          </div>
        ) : todayWorkout ? (
          <div>
            <div className="flex items-start justify-between mb-5">
              <div>
                <p className={`text-sm font-medium capitalize ${typeStyles[todayWorkout.workout_type] || 'text-text-secondary'}`}>
                  {todayWorkout.workout_type}
                </p>
                <p className="text-xl font-heading font-bold text-text-primary mt-1">
                  {todayWorkout.title}
                </p>
              </div>
              <div className="text-right bg-surface-elevated rounded-lg px-4 py-2">
                <p className="text-2xl font-heading font-bold text-text-primary">
                  {todayWorkout.estimated_duration_min}
                </p>
                <p className="text-text-muted text-xs uppercase tracking-wide">min</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3 text-sm text-text-secondary mb-6">
              <span className="px-2.5 py-1 bg-surface-elevated rounded-md">{todayWorkout.intensity_target}</span>
              <span className="text-text-muted">•</span>
              <span>
                {todayWorkout.sections?.reduce((acc, s) => acc + s.items.length, 0) || 0} exercises
              </span>
            </div>

            <Link to="/workout" className="btn-primary w-full text-center py-3.5">
              Start Workout
            </Link>
          </div>
        ) : (
          <div className="text-center py-6">
            <p className="text-text-secondary">No workout scheduled for today</p>
            <Link to="/plan" className="text-accent hover:text-accent-light text-sm mt-2 inline-block transition-colors">
              View your plan
            </Link>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 gap-4">
        <Link to="/plan" className="card-hover group">
          <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center mb-3 group-hover:bg-accent/20 transition-colors">
            <span className="text-accent text-lg">📅</span>
          </div>
          <p className="font-heading font-semibold text-text-primary">View Plan</p>
          <p className="text-sm text-text-muted mt-0.5">See your schedule</p>
        </Link>
        <Link to="/profile" className="card-hover group">
          <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center mb-3 group-hover:bg-accent/20 transition-colors">
            <span className="text-accent text-lg">⚙️</span>
          </div>
          <p className="font-heading font-semibold text-text-primary">Settings</p>
          <p className="text-sm text-text-muted mt-0.5">Update profile</p>
        </Link>
      </div>

      {/* Tip of the day */}
      <div className="card border-dashed border-border-light bg-surface-elevated/50">
        <div className="flex gap-4">
          <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center flex-shrink-0">
            <span className="text-accent">💡</span>
          </div>
          <div>
            <h3 className="font-heading font-semibold text-text-primary mb-1">Quick Tip</h3>
            <p className="text-sm text-text-secondary leading-relaxed">
              Consistency beats perfection. Even a shortened workout is better than skipping entirely.
              Listen to your body and adjust as needed.
            </p>
          </div>
        </div>
      </div>

      {/* Train Anyway Modal */}
      <TrainAnywayModal
        isOpen={showTrainAnyway}
        onClose={() => setShowTrainAnyway(false)}
        nextWorkoutDate={todayWorkout?.next_workout_date}
        onWorkoutReady={handleWorkoutReady}
      />
    </div>
  );
}
