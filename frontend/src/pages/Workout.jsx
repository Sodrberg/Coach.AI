import { useState, useEffect } from 'react';
import { useTodayWorkout } from '../hooks/useApi';
import LoadingSpinner from '../components/LoadingSpinner';
import WorkoutCard from '../components/WorkoutCard';
import FeedbackForm from '../components/FeedbackForm';
import { Link } from 'react-router-dom';

export default function Workout() {
  const { data: workout, isLoading, error, refetch } = useTodayWorkout();
  const [showFeedback, setShowFeedback] = useState(true);
  const [adjustedWorkout, setAdjustedWorkout] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [modifiedWorkout, setModifiedWorkout] = useState(null);

  // Base workout is either the adjusted one (from feedback) or the original
  const baseWorkout = adjustedWorkout || workout;
  
  // Display workout is the modified one if in edit mode, otherwise the base
  const displayWorkout = modifiedWorkout || baseWorkout;

  // Track if there are unsaved changes
  const hasChanges = modifiedWorkout !== null;

  // Reset modified workout when base workout changes
  useEffect(() => {
    setModifiedWorkout(null);
    setIsEditing(false);
  }, [baseWorkout?.workout_id]);

  const handleFeedbackComplete = (result) => {
    if (result && result.workout_id) {
      setAdjustedWorkout(result);
    }
    setShowFeedback(false);
  };

  const handleWorkoutChange = (updatedWorkout) => {
    setModifiedWorkout(updatedWorkout);
  };

  const handleDiscardChanges = () => {
    setModifiedWorkout(null);
    setIsEditing(false);
  };

  const handleToggleEdit = () => {
    if (isEditing && hasChanges) {
      // If exiting edit mode with changes, ask to confirm
      if (window.confirm('Discard unsaved changes?')) {
        handleDiscardChanges();
      }
    } else {
      setIsEditing(!isEditing);
    }
  };

  if (isLoading) {
    return <LoadingSpinner message="Loading today's workout..." />;
  }

  if (error) {
    return (
      <div className="text-center py-16 animate-in">
        <div className="w-16 h-16 rounded-full bg-surface-card flex items-center justify-center mx-auto mb-6">
          <span className="text-2xl">🏋️</span>
        </div>
        <h2 className="text-xl font-heading font-semibold text-text-primary mb-3">
          No Workout Found
        </h2>
        <p className="text-text-secondary mb-8 max-w-sm mx-auto">
          You may need to generate a training plan first.
        </p>
        <Link to="/profile" className="btn-primary">
          Set Up Profile
        </Link>
      </div>
    );
  }

  // Check if it's a rest day
  if (workout?.is_rest_day) {
    return (
      <div className="text-center py-16 animate-in">
        <div className="w-20 h-20 rounded-full bg-surface-card flex items-center justify-center mx-auto mb-6">
          <span className="text-3xl">🧘</span>
        </div>
        <h2 className="text-2xl font-heading font-bold text-text-primary mb-3">
          Rest Day
        </h2>
        <p className="text-text-secondary mb-8 max-w-sm mx-auto">
          Today is a scheduled rest day. Take time to recover!
        </p>
        
        <div className="card max-w-md mx-auto text-left">
          <h3 className="font-heading font-semibold text-text-primary mb-4">Recovery Tips</h3>
          <ul className="space-y-3">
            {workout.recovery_tips?.map((tip, i) => (
              <li key={i} className="flex items-start gap-3 text-text-secondary">
                <span className="w-1.5 h-1.5 rounded-full bg-accent mt-2 flex-shrink-0" />
                <span>{tip}</span>
              </li>
            )) || (
              <>
                <li className="flex items-start gap-3 text-text-secondary">
                  <span className="w-1.5 h-1.5 rounded-full bg-accent mt-2 flex-shrink-0" />
                  <span>Stay hydrated throughout the day</span>
                </li>
                <li className="flex items-start gap-3 text-text-secondary">
                  <span className="w-1.5 h-1.5 rounded-full bg-accent mt-2 flex-shrink-0" />
                  <span>Get quality sleep tonight</span>
                </li>
                <li className="flex items-start gap-3 text-text-secondary">
                  <span className="w-1.5 h-1.5 rounded-full bg-accent mt-2 flex-shrink-0" />
                  <span>Light stretching or walking is fine</span>
                </li>
              </>
            )}
          </ul>
        </div>
        
        {workout.next_workout_date && (
          <p className="text-text-muted mt-8 text-sm">
            Next workout: {new Date(workout.next_workout_date).toLocaleDateString('en', {
              weekday: 'long',
              month: 'short',
              day: 'numeric'
            })}
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div>
          <h1 className="text-2xl font-heading font-bold text-text-primary">Today's Workout</h1>
          <p className="text-text-secondary mt-1">
            {new Date().toLocaleDateString('en', {
              weekday: 'long',
              month: 'long',
              day: 'numeric'
            })}
          </p>
        </div>
        {!showFeedback && displayWorkout && (
          <div className="flex items-center gap-2">
            <button
              onClick={handleToggleEdit}
              className={`btn-secondary text-sm flex items-center gap-2 ${
                isEditing ? 'bg-accent/10 border-accent text-accent' : ''
              }`}
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                      d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              {isEditing ? 'Done' : 'Edit'}
            </button>
            {!isEditing && (
              <button
                onClick={() => setShowFeedback(true)}
                className="btn-secondary text-sm"
              >
                Update Status
              </button>
            )}
          </div>
        )}
      </div>

      {/* Changes indicator */}
      {hasChanges && (
        <div className="flex items-center justify-between p-3 bg-accent/10 border border-accent/30 rounded-lg animate-in">
          <p className="text-sm text-accent font-medium">
            You have unsaved changes to this workout
          </p>
          <button
            onClick={handleDiscardChanges}
            className="text-sm text-accent hover:text-accent-dark font-medium underline"
          >
            Discard
          </button>
        </div>
      )}

      {/* Feedback Form */}
      {showFeedback && (
        <FeedbackForm onComplete={handleFeedbackComplete} />
      )}

      {/* Workout Card */}
      {displayWorkout && !showFeedback && (
        <>
          <WorkoutCard 
            workout={displayWorkout}
            editable={isEditing}
            onWorkoutChange={handleWorkoutChange}
          />
          
          {/* Action Buttons */}
          <div className="flex gap-3">
            <Link 
              to="/log" 
              state={{ workout: displayWorkout }}
              className="btn-primary flex-1 text-center py-3.5"
            >
              {hasChanges ? 'Start Modified Workout' : 'Complete Workout'}
            </Link>
            {!isEditing && (
              <button
                onClick={() => refetch()}
                className="btn-secondary px-4"
                title="Refresh workout"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
            )}
          </div>
        </>
      )}
    </div>
  );
}
