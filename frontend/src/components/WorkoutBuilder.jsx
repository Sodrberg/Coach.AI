import { useState, useEffect } from 'react';
import { useSaveCustomWorkout, getUserId } from '../hooks/useApi';
import ExercisePicker from './ExercisePicker';
import ExerciseItem from './ExerciseItem';

const intensityOptions = [
  { value: 'light', label: 'Light' },
  { value: 'moderate', label: 'Moderate' },
  { value: 'hard', label: 'Hard' },
];

const defaultSections = [
  { name: 'warmup', items: [] },
  { name: 'main', items: [] },
  { name: 'cooldown', items: [] },
];

// Helper to determine workout type from exercises
function inferWorkoutType(sections) {
  const allExercises = sections.flatMap((s) => s.items);
  if (allExercises.length === 0) return 'strength';

  // Count exercise kinds
  const kindCounts = {};
  allExercises.forEach((ex) => {
    const kind = ex.kind || 'strength';
    kindCounts[kind] = (kindCounts[kind] || 0) + 1;
  });

  // Find most common kind
  let maxKind = 'strength';
  let maxCount = 0;
  Object.entries(kindCounts).forEach(([kind, count]) => {
    if (count > maxCount) {
      maxKind = kind;
      maxCount = count;
    }
  });

  return maxKind;
}

// Helper to estimate duration from exercises
function estimateDuration(sections) {
  const totalExercises = sections.reduce((acc, s) => acc + s.items.length, 0);
  if (totalExercises === 0) return 30;
  // Estimate ~4 minutes per exercise (including rest)
  return Math.max(15, Math.min(120, totalExercises * 4));
}

// Completion Modal Component
function CompletionModal({ onSave, onCancel, isSaving }) {
  const [title, setTitle] = useState('');
  const [intensity, setIntensity] = useState('moderate');

  const canSave = title.trim().length > 0;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (canSave) {
      onSave(title.trim(), intensity);
    }
  };

  return (
    <div className="fixed inset-0 z-[110] flex items-end sm:items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onCancel}
      />

      {/* Modal */}
      <div className="relative w-full sm:max-w-md bg-surface-card rounded-t-2xl sm:rounded-2xl 
                      border border-border shadow-2xl animate-in-up">
        {/* Header */}
        <div className="p-5 border-b border-border">
          <h2 className="text-xl font-heading font-bold text-text-primary">
            Complete Workout
          </h2>
          <p className="text-sm text-text-muted mt-1">
            Add a title and select intensity
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-5 space-y-5">
          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Workout Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Upper Body Strength"
              autoFocus
              className="w-full px-4 py-3 bg-surface-elevated border border-border rounded-lg 
                         text-text-primary placeholder-text-muted
                         focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent"
            />
          </div>

          {/* Intensity */}
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Intensity
            </label>
            <div className="flex gap-2">
              {intensityOptions.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setIntensity(opt.value)}
                  className={`flex-1 py-2.5 rounded-lg border text-sm font-medium transition-colors ${
                    intensity === opt.value
                      ? 'bg-accent/10 border-accent text-accent'
                      : 'bg-surface-elevated border-border text-text-secondary hover:border-accent/50'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 py-3 rounded-lg border border-border text-text-secondary 
                         hover:bg-surface-elevated transition-colors font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!canSave || isSaving}
              className="flex-1 py-3 rounded-lg bg-accent text-white font-medium
                         hover:bg-accent-dark transition-colors
                         disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSaving ? 'Saving...' : 'Save Workout'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function WorkoutBuilder({ onComplete, onCancel }) {
  const [sections, setSections] = useState(defaultSections);
  const [expandedSections, setExpandedSections] = useState({ warmup: true, main: true, cooldown: true });
  const [pickerOpen, setPickerOpen] = useState(false);
  const [targetSection, setTargetSection] = useState(null);
  const [showCompletionModal, setShowCompletionModal] = useState(false);

  const saveMutation = useSaveCustomWorkout();

  // Prevent body scroll
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = '';
    };
  }, []);

  const toggleSection = (sectionName) => {
    setExpandedSections((prev) => ({
      ...prev,
      [sectionName]: !prev[sectionName],
    }));
  };

  const handleAddExercise = (newExercise, sectionName) => {
    setSections((prev) =>
      prev.map((section) =>
        section.name === sectionName
          ? { ...section, items: [...section.items, newExercise] }
          : section
      )
    );
  };

  const handleUpdateExercise = (sectionIndex, exerciseIndex, updatedExercise) => {
    setSections((prev) =>
      prev.map((section, sIdx) =>
        sIdx === sectionIndex
          ? {
              ...section,
              items: section.items.map((item, eIdx) =>
                eIdx === exerciseIndex ? updatedExercise : item
              ),
            }
          : section
      )
    );
  };

  const handleRemoveExercise = (sectionIndex, exerciseIndex) => {
    setSections((prev) =>
      prev.map((section, sIdx) =>
        sIdx === sectionIndex
          ? {
              ...section,
              items: section.items.filter((_, eIdx) => eIdx !== exerciseIndex),
            }
          : section
      )
    );
  };

  const openPickerForSection = (sectionName) => {
    setTargetSection(sectionName);
    setPickerOpen(true);
  };

  const totalExercises = sections.reduce((acc, s) => acc + s.items.length, 0);
  const canComplete = totalExercises > 0;

  const handleSave = async (title, intensity) => {
    const userId = getUserId();
    const workoutType = inferWorkoutType(sections);
    const duration = estimateDuration(sections);

    const workout = {
      user_id: userId,
      title: title,
      workout_type: workoutType,
      estimated_duration_min: duration,
      intensity_target: intensity,
      sections: sections.filter((s) => s.items.length > 0),
    };

    try {
      const savedWorkout = await saveMutation.mutateAsync(workout);
      setShowCompletionModal(false);
      onComplete?.(savedWorkout);
    } catch (error) {
      console.error('Failed to save workout:', error);
    }
  };

  // #region agent log
  fetch('http://127.0.0.1:7242/ingest/ec7cf0ec-5098-4120-a457-e76f87ea854b',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'WorkoutBuilder.jsx:248',message:'WorkoutBuilder render',data:{hasOnComplete:!!onComplete,hasOnCancel:!!onCancel},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'A'})}).catch(()=>{});
  // #endregion

  return (
    <div className="fixed inset-0 z-[100] bg-surface-base flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border bg-surface-card">
        <button
          onClick={onCancel}
          className="p-2 -ml-2 rounded-lg text-text-muted hover:text-text-primary 
                     hover:bg-surface-elevated transition-colors"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 className="text-lg font-heading font-bold text-text-primary">Create Workout</h1>
        <div className="w-9" /> {/* Spacer for centering */}
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-4 space-y-4 max-w-2xl mx-auto pb-24">
          {/* Disclaimer banner */}
          <div className="p-4 rounded-xl bg-surface-elevated border border-border-light flex gap-4">
            <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center flex-shrink-0">
              <span className="text-accent text-lg">ℹ️</span>
            </div>
            <div>
              <p className="text-sm text-text-secondary leading-relaxed">
                This is a <span className="font-medium text-text-primary">standalone workout</span> and 
                won't affect your scheduled training plan.
              </p>
            </div>
          </div>

          {/* Sections */}
          <div className="space-y-3">
            <h2 className="font-heading font-semibold text-text-primary">
              Add Exercises
              {totalExercises > 0 && (
                <span className="ml-2 text-sm font-normal text-text-muted">
                  ({totalExercises} added)
                </span>
              )}
            </h2>

            {sections.map((section, sectionIndex) => (
              <div key={section.name} className="border border-border rounded-xl overflow-hidden">
                <button
                  onClick={() => toggleSection(section.name)}
                  className="w-full flex items-center justify-between p-4 bg-surface-card 
                             hover:bg-surface-elevated transition-colors"
                >
                  <span className="font-heading font-semibold capitalize text-text-primary">
                    {section.name}
                  </span>
                  <div className="flex items-center gap-3">
                    {section.items.length > 0 && (
                      <span className="text-sm text-text-muted">
                        {section.items.length} exercise{section.items.length !== 1 ? 's' : ''}
                      </span>
                    )}
                    <svg
                      className={`w-4 h-4 text-text-muted transition-transform duration-200 ${
                        expandedSections[section.name] ? 'rotate-180' : ''
                      }`}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </button>

                {expandedSections[section.name] && (
                  <div className="divide-y divide-border">
                    {section.items.map((item, exerciseIndex) => (
                      <ExerciseItem
                        key={exerciseIndex}
                        exercise={item}
                        editable={true}
                        onUpdate={(updated) => handleUpdateExercise(sectionIndex, exerciseIndex, updated)}
                        onRemove={() => handleRemoveExercise(sectionIndex, exerciseIndex)}
                      />
                    ))}

                    {/* Add Exercise Button */}
                    <button
                      onClick={() => openPickerForSection(section.name)}
                      className="w-full p-4 flex items-center justify-center gap-2 
                                 text-accent hover:bg-surface-elevated
                                 transition-colors"
                    >
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                      <span className="font-medium">Add Exercise</span>
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Helper text when no exercises */}
          {totalExercises === 0 && (
            <p className="text-sm text-text-muted text-center py-4">
              Tap on a section above to start adding exercises
            </p>
          )}

          {/* Error display */}
          {saveMutation.isError && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30">
              <p className="text-sm text-red-400">
                {saveMutation.error?.message || 'Failed to save workout. Please try again.'}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Fixed bottom button */}
      <div className="fixed bottom-0 left-0 right-0 p-4 bg-surface-card border-t border-border">
        <div className="max-w-2xl mx-auto">
          <button
            onClick={() => setShowCompletionModal(true)}
            disabled={!canComplete}
            className="w-full py-4 rounded-xl bg-accent text-white font-heading font-semibold
                       hover:bg-accent-dark transition-colors
                       disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Complete Workout
          </button>
        </div>
      </div>

      {/* Exercise Picker Modal */}
      <ExercisePicker
        isOpen={pickerOpen}
        onClose={() => {
          setPickerOpen(false);
          setTargetSection(null);
        }}
        onSelectExercise={handleAddExercise}
        targetSection={targetSection}
      />

      {/* Completion Modal */}
      {showCompletionModal && (
        <CompletionModal
          onSave={handleSave}
          onCancel={() => setShowCompletionModal(false)}
          isSaving={saveMutation.isPending}
        />
      )}
    </div>
  );
}
