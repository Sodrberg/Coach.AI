import { useState, useEffect, useRef, useCallback } from 'react';
import { useTodayWorkout } from '../hooks/useApi';
import { WorkoutSkeleton } from '../components/SkeletonLoader';
import ConfirmModal from '../components/ConfirmModal';
import WorkoutCard from '../components/WorkoutCard';
import FeedbackForm from '../components/FeedbackForm';
import TrainAnywayModal from '../components/TrainAnywayModal';
import SetTracker from '../components/SetTracker';
import { useToast } from '../hooks/useToast';
import { Link, useNavigate } from 'react-router-dom';

function formatElapsed(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  return `${m}:${String(s).padStart(2, '0')}`;
}

export default function Workout() {
  const navigate = useNavigate();
  const toast = useToast();
  const { data: workout, isLoading, error, refetch } = useTodayWorkout();
  const [showFeedback, setShowFeedback] = useState(true);
  const [adjustedWorkout, setAdjustedWorkout] = useState(null);
  const [modifiedWorkout, setModifiedWorkout] = useState(null);
  const [showTrainAnyway, setShowTrainAnyway] = useState(false);
  const [customWorkout, setCustomWorkout] = useState(null);
  const [showCompletedDetails, setShowCompletedDetails] = useState(true);
  const [showDiscardConfirm, setShowDiscardConfirm] = useState(false);
  const [trackingData, setTrackingData] = useState({});
  const [activeTrackerExercise, setActiveTrackerExercise] = useState(null); // { key, exercise }

  // Timer state
  const [timerRunning, setTimerRunning] = useState(false);
  const [timerPaused, setTimerPaused] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const timerRef = useRef(null);
  const startTimeRef = useRef(null);
  const accumulatedSecondsRef = useRef(0);

  const timerActive = timerRunning || timerPaused;

  const startWorkout = useCallback(() => {
    accumulatedSecondsRef.current = 0;
    startTimeRef.current = Date.now();
    setElapsedSeconds(0);
    setTimerRunning(true);
    setTimerPaused(false);
    timerRef.current = setInterval(() => {
      setElapsedSeconds(accumulatedSecondsRef.current + Math.floor((Date.now() - startTimeRef.current) / 1000));
    }, 1000);
  }, []);

  const pauseWorkout = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    accumulatedSecondsRef.current += Math.floor((Date.now() - startTimeRef.current) / 1000);
    setElapsedSeconds(accumulatedSecondsRef.current);
    setTimerRunning(false);
    setTimerPaused(true);
  }, []);

  const resumeWorkout = useCallback(() => {
    startTimeRef.current = Date.now();
    setTimerRunning(true);
    setTimerPaused(false);
    timerRef.current = setInterval(() => {
      setElapsedSeconds(accumulatedSecondsRef.current + Math.floor((Date.now() - startTimeRef.current) / 1000));
    }, 1000);
  }, []);

  const completeWorkout = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    const finalSeconds = timerPaused
      ? accumulatedSecondsRef.current
      : accumulatedSecondsRef.current + Math.floor((Date.now() - startTimeRef.current) / 1000);
    setTimerRunning(false);
    setTimerPaused(false);
    setElapsedSeconds(finalSeconds);
    navigate('/log', {
      state: {
        workout: modifiedWorkout || adjustedWorkout || customWorkout || workout,
        trackingData,
        durationMin: Math.max(1, Math.round(finalSeconds / 60)),
      },
    });
  }, [navigate, modifiedWorkout, adjustedWorkout, customWorkout, workout, trackingData, timerPaused]);

  // Cleanup interval on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  // Use custom workout if available (from train anyway), otherwise use fetched workout
  const todayWorkout = customWorkout || workout;

  // Base workout is either the adjusted one (from feedback) or the original
  const baseWorkout = adjustedWorkout || todayWorkout;
  
  // Display workout is the modified one if in edit mode, otherwise the base
  const displayWorkout = modifiedWorkout || baseWorkout;

  // Track if there are unsaved changes
  const hasChanges = modifiedWorkout !== null;

  // Reset modified workout when base workout changes
  useEffect(() => {
    setModifiedWorkout(null);
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
    toast('Changes discarded');
  };

  // Handle tracking data changes from WorkoutCard
  const handleTrackingChange = (key, data, action) => {
    if (action === 'open') {
      // Find the exercise from the displayed workout
      const [sectionIdx, exerciseIdx] = key.split('-').map(Number);
      const exercise = displayWorkout?.sections?.[sectionIdx]?.items?.[exerciseIdx];
      if (exercise) {
        setActiveTrackerExercise({ key, exercise });
      }
      return;
    }
    setTrackingData(prev => ({ ...prev, [key]: data }));
  };

  // Handle SetTracker update
  const handleTrackerUpdate = (data) => {
    if (activeTrackerExercise) {
      setTrackingData(prev => ({ ...prev, [activeTrackerExercise.key]: data }));
    }
  };

  const handleTrainAnywayComplete = (newWorkout) => {
    setShowTrainAnyway(false);
    setCustomWorkout(newWorkout);  // Store the workout directly for immediate display
    setShowFeedback(false);  // Skip feedback form for custom workout
    refetch();  // Still refetch to update cache
  };

  if (isLoading) {
    return <WorkoutSkeleton />;
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

  // Check if it's a rest day (use todayWorkout which includes custom workout)
  if (todayWorkout?.is_rest_day) {
    return (
      <>
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
              {todayWorkout.recovery_tips?.map((tip, i) => (
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
          
          <button
            onClick={() => setShowTrainAnyway(true)}
            className="btn-primary mt-8"
          >
            Train Anyway
          </button>
          
          {todayWorkout.next_workout_date && (
            <p className="text-text-muted mt-6 text-sm">
              Next workout: {new Date(todayWorkout.next_workout_date).toLocaleDateString('en', {
                weekday: 'long',
                month: 'short',
                day: 'numeric'
              })}
            </p>
          )}
        </div>
        
        <TrainAnywayModal
          isOpen={showTrainAnyway}
          onClose={() => setShowTrainAnyway(false)}
          nextWorkoutDate={todayWorkout.next_workout_date}
          onWorkoutReady={handleTrainAnywayComplete}
        />
      </>
    );
  }

  // Check if workout is already completed
  if (todayWorkout?.is_completed) {
    // Use displayWorkout for completed view to support editing
    const completedDisplayWorkout = modifiedWorkout || todayWorkout;
    const completedHasChanges = modifiedWorkout !== null;

    return (
      <div className="space-y-6 animate-in">
        {/* Header with completion status */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-secondary/20 flex items-center justify-center">
              <svg className="w-5 h-5 text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div>
              <h1 className="text-2xl font-heading font-bold text-text-primary">Workout Completed!</h1>
              <p className="text-text-secondary mt-1">
                {new Date().toLocaleDateString('en', {
                  weekday: 'long',
                  month: 'long',
                  day: 'numeric'
                })}
              </p>
            </div>
          </div>
        </div>

        {/* Changes indicator */}
        {completedHasChanges && (
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

        {/* Workout Summary Card (shown when details are hidden) */}
        {!showCompletedDetails && (
          <div className="card text-left">
            <div className="flex items-start justify-between mb-4">
              <div>
                <p className="text-sm font-medium text-text-muted uppercase tracking-wide">Completed</p>
                <p className="text-lg font-heading font-bold text-text-primary mt-1">
                  {todayWorkout.title}
                </p>
              </div>
              <div className="text-right bg-surface-elevated rounded-lg px-3 py-1.5">
                <p className="text-lg font-heading font-bold text-text-primary">
                  {todayWorkout.estimated_duration_min}
                </p>
                <p className="text-text-muted text-xs uppercase tracking-wide">min</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3 text-sm text-text-secondary">
              <span className="px-2.5 py-1 bg-surface-elevated rounded-md capitalize">{todayWorkout.workout_type}</span>
              <span className="text-text-muted">•</span>
              <span>
                {todayWorkout.sections?.reduce((acc, s) => acc + s.items.length, 0) || 0} exercises
              </span>
            </div>
          </div>
        )}

        {/* Full Workout Details (shown when expanded) */}
        {showCompletedDetails && (
          <WorkoutCard 
            workout={completedDisplayWorkout}
            editable={true}
            onWorkoutChange={handleWorkoutChange}
          />
        )}

        {/* Next Workout Info */}
        {todayWorkout.next_workout_date && (
          <div className="card">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center flex-shrink-0">
                <span className="text-xl">📅</span>
              </div>
              <div className="text-left">
                <p className="text-sm text-text-muted">Next Workout</p>
                <p className="font-heading font-semibold text-text-primary">
                  {new Date(todayWorkout.next_workout_date).toLocaleDateString('en', {
                    weekday: 'long',
                    month: 'short',
                    day: 'numeric'
                  })}
                </p>
              </div>
            </div>
          </div>
        )}
        
        {/* Action Buttons */}
        <div className="flex flex-col gap-3">
          {!showCompletedDetails ? (
            <>
              <button
                onClick={() => setShowCompletedDetails(true)}
                className="btn-secondary w-full py-3 flex items-center justify-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                View Details
              </button>
              <Link 
                to="/log" 
                state={{ workout: todayWorkout }}
                className="btn-secondary w-full py-3 text-center flex items-center justify-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Log Again
              </Link>
              <Link to="/" className="btn-primary w-full py-3 text-center">
                Back to Home
              </Link>
            </>
          ) : (
            <>
              <div className="flex gap-3">
                <Link 
                  to="/log" 
                  state={{ workout: completedDisplayWorkout }}
                  className="btn-primary flex-1 text-center py-3.5"
                >
                  {completedHasChanges ? 'Log Modified Workout' : 'Log Again'}
                </Link>
                <button
                  onClick={() => {
                    if (completedHasChanges) {
                      setShowDiscardConfirm(true);
                    } else {
                      setShowCompletedDetails(false);
                    }
                  }}
                  className="btn-secondary px-4"
                  title="Hide details"
                  aria-label="Hide details"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </>
          )}
        </div>

        <ConfirmModal
          isOpen={showDiscardConfirm}
          title="Discard changes?"
          message="You have unsaved modifications to this workout. Are you sure you want to discard them?"
          confirmLabel="Discard"
          cancelLabel="Keep editing"
          onConfirm={() => {
            setShowDiscardConfirm(false);
            handleDiscardChanges();
            setShowCompletedDetails(false);
          }}
          onCancel={() => setShowDiscardConfirm(false)}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in">
      {/* Spacer for fixed action bar */}
      {displayWorkout && !showFeedback && <div className="h-[52px]" />}

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
          <button
            onClick={() => setShowFeedback(true)}
            className="btn-secondary text-sm"
          >
            Update Status
          </button>
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
          {/* Fixed Action Bar - pinned below header */}
          <div className="fixed top-[57px] left-0 right-0 z-40 bg-surface-card/95 border-b border-border backdrop-blur-sm">
            <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
              {!timerActive ? (
                <>
                  <button
                    onClick={startWorkout}
                    className="btn-primary flex-1 py-2.5 text-sm"
                  >
                    {hasChanges ? 'Start Modified Workout' : 'Start Workout'}
                  </button>
                  <button
                    onClick={() => refetch()}
                    className="btn-secondary px-3 py-2.5 ml-2"
                    title="Refresh workout"
                    aria-label="Refresh workout"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                  </button>
                </>
              ) : (
                <>
                  <p className="text-2xl font-heading font-bold text-accent tabular-nums min-w-[5ch]">
                    {formatElapsed(elapsedSeconds)}
                  </p>
                  <div className="flex items-center gap-2">
                    {timerRunning ? (
                      <button
                        onClick={pauseWorkout}
                        className="px-4 py-2 rounded-lg font-semibold text-sm bg-surface-elevated text-text-primary hover:bg-surface-elevated/80 transition-colors"
                      >
                        Pause
                      </button>
                    ) : (
                      <button
                        onClick={resumeWorkout}
                        className="px-4 py-2 rounded-lg font-semibold text-sm bg-accent text-white hover:bg-accent/90 transition-colors"
                      >
                        Resume
                      </button>
                    )}
                    <button
                      onClick={completeWorkout}
                      className="px-4 py-2 rounded-lg font-semibold text-sm bg-secondary text-white hover:bg-secondary/90 transition-colors"
                    >
                      Complete
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>

          <WorkoutCard
            workout={displayWorkout}
            editable={true}
            onWorkoutChange={handleWorkoutChange}
            trackingData={trackingData}
            onTrackingChange={handleTrackingChange}
          />
        </>
      )}

      {/* Set Tracker Modal */}
      {activeTrackerExercise && (
        <SetTracker
          exercise={activeTrackerExercise.exercise}
          setData={trackingData[activeTrackerExercise.key]}
          onUpdate={handleTrackerUpdate}
          onClose={() => setActiveTrackerExercise(null)}
        />
      )}
    </div>
  );
}
