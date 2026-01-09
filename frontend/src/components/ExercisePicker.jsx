import { useState, useMemo, useEffect } from 'react';
import { useExercises } from '../hooks/useApi';

const exerciseTypes = [
  { value: '', label: 'All Types' },
  { value: 'strength', label: 'Strength' },
  { value: 'cardio', label: 'Cardio' },
  { value: 'mobility', label: 'Mobility' },
  { value: 'gymnastics', label: 'Gymnastics' },
];

const bodyParts = [
  { value: '', label: 'All Body Parts' },
  { value: 'legs', label: 'Legs' },
  { value: 'back', label: 'Back' },
  { value: 'chest', label: 'Chest' },
  { value: 'arms', label: 'Arms' },
  { value: 'core', label: 'Core' },
  { value: 'shoulders', label: 'Shoulders' },
  { value: 'full_body', label: 'Full Body' },
];

const typeColors = {
  strength: 'bg-strength/10 text-strength border-strength/30',
  cardio: 'bg-endurance/10 text-endurance border-endurance/30',
  mobility: 'bg-recovery/10 text-recovery border-recovery/30',
  gymnastics: 'bg-accent/10 text-accent border-accent/30',
};

export default function ExercisePicker({ isOpen, onClose, onSelectExercise, targetSection }) {
  const [search, setSearch] = useState('');
  const [exerciseType, setExerciseType] = useState('');
  const [bodyPart, setBodyPart] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  const { data, isLoading } = useExercises({
    search: debouncedSearch || undefined,
    exerciseType: exerciseType || undefined,
    bodyPart: bodyPart || undefined,
  });

  const exercises = data?.exercises || [];

  // Reset filters when modal closes
  useEffect(() => {
    if (!isOpen) {
      setSearch('');
      setExerciseType('');
      setBodyPart('');
    }
  }, [isOpen]);

  // Handle exercise selection
  const handleSelect = (exercise) => {
    // Convert from database format to workout format
    const workoutExercise = {
      name: exercise.name,
      kind: exercise.exerciseType === 'cardio' ? 'endurance' : exercise.exerciseType,
      // Set default values based on tracking options
      ...(exercise.trackingOptions?.includes('reps') && { sets: 3, reps: 10 }),
      ...(exercise.trackingOptions?.includes('time') && !exercise.trackingOptions?.includes('reps') && { duration_min: 5 }),
      rest_sec: 60,
      cues: exercise.instructions,
    };
    
    onSelectExercise(workoutExercise, targetSection);
    onClose();
  };

  // Close on escape key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative w-full sm:max-w-lg max-h-[85vh] bg-surface-card rounded-t-2xl sm:rounded-2xl 
                      border border-border shadow-2xl flex flex-col animate-in-up">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div>
            <h2 className="text-lg font-heading font-semibold text-text-primary">
              Add Exercise
            </h2>
            {targetSection && (
              <p className="text-sm text-text-muted mt-0.5">
                Adding to <span className="capitalize">{targetSection}</span>
              </p>
            )}
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

        {/* Search & Filters */}
        <div className="p-4 space-y-3 border-b border-border">
          {/* Search input */}
          <div className="relative">
            <svg 
              className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" 
              fill="none" 
              viewBox="0 0 24 24" 
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search exercises..."
              className="w-full pl-10 pr-4 py-2.5 bg-surface-elevated border border-border rounded-lg 
                         text-text-primary placeholder-text-muted text-sm
                         focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent"
              autoFocus
            />
          </div>

          {/* Filters */}
          <div className="flex gap-2">
            <select
              value={exerciseType}
              onChange={(e) => setExerciseType(e.target.value)}
              className="flex-1 px-3 py-2 bg-surface-elevated border border-border rounded-lg 
                         text-text-primary text-sm focus:outline-none focus:ring-2 
                         focus:ring-accent/50 focus:border-accent"
            >
              {exerciseTypes.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
            <select
              value={bodyPart}
              onChange={(e) => setBodyPart(e.target.value)}
              className="flex-1 px-3 py-2 bg-surface-elevated border border-border rounded-lg 
                         text-text-primary text-sm focus:outline-none focus:ring-2 
                         focus:ring-accent/50 focus:border-accent"
            >
              {bodyParts.map((part) => (
                <option key={part.value} value={part.value}>
                  {part.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Exercise List */}
        <div className="flex-1 overflow-y-auto p-2">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
            </div>
          ) : exercises.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-text-muted">No exercises found</p>
              {search && (
                <p className="text-sm text-text-muted mt-1">
                  Try adjusting your search or filters
                </p>
              )}
            </div>
          ) : (
            <div className="space-y-1">
              {exercises.slice(0, 50).map((exercise) => (
                <button
                  key={exercise.id}
                  onClick={() => handleSelect(exercise)}
                  className="w-full p-3 rounded-lg text-left hover:bg-surface-elevated 
                             transition-colors group"
                >
                  <div className="flex items-start gap-3">
                    <div className={`w-8 h-8 rounded-md flex items-center justify-center flex-shrink-0 
                                    ${typeColors[exercise.exerciseType] || 'bg-accent/10 text-accent'}`}>
                      <span className="text-xs font-bold uppercase">
                        {exercise.exerciseType?.charAt(0) || 'E'}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-text-primary group-hover:text-accent 
                                     transition-colors truncate">
                        {exercise.name}
                      </h4>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-text-muted capitalize">
                          {exercise.bodyPart?.replace('_', ' ')}
                        </span>
                        <span className="text-text-muted">•</span>
                        <span className="text-xs text-text-muted capitalize">
                          {exercise.primaryMuscle}
                        </span>
                      </div>
                    </div>
                    <svg 
                      className="w-4 h-4 text-text-muted group-hover:text-accent transition-colors flex-shrink-0 mt-1" 
                      fill="none" 
                      viewBox="0 0 24 24" 
                      stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                  </div>
                </button>
              ))}
              {exercises.length > 50 && (
                <p className="text-center text-sm text-text-muted py-4">
                  Showing first 50 results. Use search to find specific exercises.
                </p>
              )}
            </div>
          )}
        </div>

        {/* Footer with count */}
        <div className="p-3 border-t border-border bg-surface-elevated/50">
          <p className="text-xs text-text-muted text-center">
            {data?.total || 0} exercises available
          </p>
        </div>
      </div>
    </div>
  );
}
