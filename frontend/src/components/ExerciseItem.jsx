import { useState } from 'react';

const kindStyles = {
  strength: 'bg-strength/10 text-strength',
  endurance: 'bg-endurance/10 text-endurance',
  mobility: 'bg-recovery/10 text-recovery',
  recovery: 'bg-recovery/10 text-recovery',
};

// Stepper component for adjusting numeric values
function Stepper({ value, onChange, min = 1, max = 99, label }) {
  return (
    <div className="flex items-center gap-1">
      <button
        type="button"
        onClick={() => onChange(Math.max(min, value - 1))}
        disabled={value <= min}
        className="w-7 h-7 rounded-md bg-surface-elevated border border-border 
                   flex items-center justify-center text-text-secondary
                   hover:bg-surface-hover hover:text-text-primary
                   disabled:opacity-40 disabled:cursor-not-allowed
                   transition-colors"
      >
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
        </svg>
      </button>
      <div className="min-w-[3.5rem] text-center">
        <span className="text-sm font-medium text-text-primary">{value}</span>
        <span className="text-xs text-text-muted ml-1">{label}</span>
      </div>
      <button
        type="button"
        onClick={() => onChange(Math.min(max, value + 1))}
        disabled={value >= max}
        className="w-7 h-7 rounded-md bg-surface-elevated border border-border 
                   flex items-center justify-center text-text-secondary
                   hover:bg-surface-hover hover:text-text-primary
                   disabled:opacity-40 disabled:cursor-not-allowed
                   transition-colors"
      >
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
      </button>
    </div>
  );
}

// Time input component
function TimeInput({ value, onChange, label }) {
  return (
    <div className="flex items-center gap-2">
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(Math.max(1, parseInt(e.target.value) || 1))}
        min="1"
        max="180"
        className="w-16 h-8 px-2 text-sm text-center bg-surface-elevated border border-border 
                   rounded-md text-text-primary focus:outline-none focus:ring-1 focus:ring-accent"
      />
      <span className="text-xs text-text-muted">{label}</span>
    </div>
  );
}

export default function ExerciseItem({ exercise, editable = false, onUpdate, onRemove }) {
  const [showCues, setShowCues] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  const kindStyle = kindStyles[exercise.kind] || 'bg-accent/10 text-accent';

  // Handle value changes
  const handleChange = (field, value) => {
    if (onUpdate) {
      onUpdate({ ...exercise, [field]: value });
    }
  };

  // Format the prescription
  const getPrescription = () => {
    const parts = [];
    
    if (exercise.sets && exercise.reps) {
      parts.push(`${exercise.sets} × ${exercise.reps}`);
    }
    if (exercise.weight_kg) {
      parts.push(`${exercise.weight_kg} kg`);
    }
    if (exercise.duration_min) {
      parts.push(`${exercise.duration_min} min`);
    }
    if (exercise.distance_km) {
      parts.push(`${exercise.distance_km} km`);
    }
    if (exercise.rest_sec) {
      parts.push(`${exercise.rest_sec}s rest`);
    }
    
    return parts.join(' • ');
  };

  // Determine what can be edited based on exercise properties
  const hasSetsReps = exercise.sets !== undefined || exercise.reps !== undefined;
  const hasDuration = exercise.duration_min !== undefined;

  return (
    <div className="p-4 bg-surface-card">
      <div className="flex items-start gap-4">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${kindStyle}`}>
          <span className="text-sm font-heading font-bold uppercase">
            {exercise.kind?.charAt(0) || 'E'}
          </span>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <h4 className="font-heading font-medium text-text-primary">{exercise.name}</h4>
            {editable && (
              <div className="flex items-center gap-1 flex-shrink-0">
                <button
                  type="button"
                  onClick={() => setIsEditing(!isEditing)}
                  className={`p-1.5 rounded-md transition-colors ${
                    isEditing 
                      ? 'bg-accent/20 text-accent' 
                      : 'text-text-muted hover:text-text-secondary hover:bg-surface-elevated'
                  }`}
                  title={isEditing ? 'Done editing' : 'Edit exercise'}
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                          d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
                {onRemove && (
                  <button
                    type="button"
                    onClick={() => onRemove(exercise)}
                    className="p-1.5 rounded-md text-text-muted hover:text-red-400 hover:bg-red-400/10 transition-colors"
                    title="Remove exercise"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>
            )}
          </div>
          
          {/* Prescription display (when not editing) */}
          {!isEditing && (
            <p className="text-sm text-text-secondary mt-1">
              {getPrescription()}
            </p>
          )}
          
          {/* Edit controls */}
          {isEditing && editable && (
            <div className="mt-3 flex flex-wrap gap-4">
              {hasSetsReps && (
                <>
                  {exercise.sets !== undefined && (
                    <Stepper
                      value={exercise.sets}
                      onChange={(val) => handleChange('sets', val)}
                      min={1}
                      max={10}
                      label="sets"
                    />
                  )}
                  {exercise.reps !== undefined && (
                    <Stepper
                      value={exercise.reps}
                      onChange={(val) => handleChange('reps', val)}
                      min={1}
                      max={50}
                      label="reps"
                    />
                  )}
                </>
              )}
              {hasDuration && (
                <TimeInput
                  value={exercise.duration_min}
                  onChange={(val) => handleChange('duration_min', val)}
                  label="min"
                />
              )}
              {exercise.rest_sec !== undefined && (
                <Stepper
                  value={exercise.rest_sec}
                  onChange={(val) => handleChange('rest_sec', val)}
                  min={0}
                  max={300}
                  label="sec rest"
                />
              )}
            </div>
          )}
          
          {exercise.cues && (
            <button
              onClick={() => setShowCues(!showCues)}
              className="text-xs text-accent hover:text-accent-light mt-2 font-medium transition-colors"
            >
              {showCues ? 'Hide tips' : 'Show tips'}
            </button>
          )}
          
          {showCues && exercise.cues && (
            <div className="mt-3 p-3 bg-surface-elevated rounded-lg border border-border">
              <p className="text-sm text-text-secondary leading-relaxed">
                <span className="text-accent mr-1">💡</span> {exercise.cues}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
