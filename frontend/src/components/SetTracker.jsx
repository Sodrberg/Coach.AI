import { useState, useEffect } from 'react';

const kindStyles = {
  strength: 'bg-strength/10 text-strength',
  endurance: 'bg-endurance/10 text-endurance',
  mobility: 'bg-recovery/10 text-recovery',
  recovery: 'bg-recovery/10 text-recovery',
};

export default function SetTracker({ exercise, setData, onUpdate, onClose }) {
  const isDuration = exercise.kind === 'endurance' || exercise.kind === 'cardio' ||
    (!exercise.sets && exercise.duration_min);

  const [sets, setSets] = useState(() => {
    if (setData?.sets?.length) return setData.sets;
    if (isDuration) {
      return [{ set_number: 1, duration_min: exercise.duration_min || 0, distance_km: exercise.distance_km || 0, done: false }];
    }
    const count = exercise.sets || 1;
    return Array.from({ length: count }, (_, i) => ({
      set_number: i + 1,
      weight_kg: exercise.weight_kg || 0,
      reps: exercise.reps || 0,
      done: false,
    }));
  });

  // Close on Escape
  useEffect(() => {
    const handleKey = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [onClose]);

  // Lock body scroll
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, []);

  const updateSet = (index, field, value) => {
    setSets(prev => prev.map((s, i) => i === index ? { ...s, [field]: value } : s));
  };

  const toggleSetDone = (index) => {
    setSets(prev => prev.map((s, i) => i === index ? { ...s, done: !s.done } : s));
  };

  const addSet = () => {
    const last = sets[sets.length - 1];
    setSets(prev => [...prev, {
      set_number: prev.length + 1,
      ...(isDuration
        ? { duration_min: last?.duration_min || 0, distance_km: last?.distance_km || 0 }
        : { weight_kg: last?.weight_kg || 0, reps: last?.reps || 0 }),
      done: false,
    }]);
  };

  const handleClose = () => {
    const allDone = sets.every(s => s.done);
    onUpdate({ completed: allDone, sets });
    onClose();
  };

  const kindStyle = kindStyles[exercise.kind] || 'bg-accent/10 text-accent';

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={handleClose} />

      {/* Panel */}
      <div className="relative w-full sm:max-w-md max-h-[85vh] bg-surface-card rounded-t-2xl sm:rounded-2xl
                      border border-border shadow-xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center gap-3">
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${kindStyle}`}>
              <span className="text-xs font-heading font-bold uppercase">
                {exercise.kind?.charAt(0) || 'E'}
              </span>
            </div>
            <h3 className="font-heading font-semibold text-text-primary">{exercise.name}</h3>
          </div>
          <button
            onClick={handleClose}
            className="p-1.5 rounded-md text-text-muted hover:text-text-secondary hover:bg-surface-elevated transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Sets list */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {isDuration ? (
            /* Duration-based exercise */
            sets.map((set, i) => (
              <div key={i} className="flex items-center gap-3 p-3 bg-surface-elevated rounded-lg border border-border">
                <button
                  onClick={() => toggleSetDone(i)}
                  className={`w-6 h-6 rounded-md border-2 flex items-center justify-center flex-shrink-0 transition-colors ${
                    set.done
                      ? 'bg-accent border-accent text-white'
                      : 'border-border hover:border-text-muted'
                  }`}
                >
                  {set.done && (
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                </button>
                <div className="flex items-center gap-2 flex-1">
                  <input
                    type="number"
                    value={set.duration_min}
                    onChange={(e) => updateSet(i, 'duration_min', parseFloat(e.target.value) || 0)}
                    className="w-16 h-8 px-2 text-sm text-center bg-surface-card border border-border
                               rounded-md text-text-primary focus:outline-none focus:ring-1 focus:ring-accent"
                  />
                  <span className="text-xs text-text-muted">min</span>
                  <input
                    type="number"
                    value={set.distance_km}
                    onChange={(e) => updateSet(i, 'distance_km', parseFloat(e.target.value) || 0)}
                    step="0.1"
                    className="w-16 h-8 px-2 text-sm text-center bg-surface-card border border-border
                               rounded-md text-text-primary focus:outline-none focus:ring-1 focus:ring-accent"
                  />
                  <span className="text-xs text-text-muted">km</span>
                </div>
              </div>
            ))
          ) : (
            /* Sets/reps-based exercise */
            <>
              {/* Column headers */}
              <div className="flex items-center gap-3 px-3 pb-1">
                <div className="w-6" />
                <span className="w-8 text-xs text-text-muted text-center">Set</span>
                <span className="flex-1 text-xs text-text-muted text-center">Weight (kg)</span>
                <span className="flex-1 text-xs text-text-muted text-center">Reps</span>
              </div>

              {sets.map((set, i) => (
                <div key={i} className="flex items-center gap-3 p-3 bg-surface-elevated rounded-lg border border-border">
                  <button
                    onClick={() => toggleSetDone(i)}
                    className={`w-6 h-6 rounded-md border-2 flex items-center justify-center flex-shrink-0 transition-colors ${
                      set.done
                        ? 'bg-accent border-accent text-white'
                        : 'border-border hover:border-text-muted'
                    }`}
                  >
                    {set.done && (
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </button>
                  <span className="w-8 text-sm text-text-muted text-center font-medium">{set.set_number}</span>
                  <input
                    type="number"
                    value={set.weight_kg}
                    onChange={(e) => updateSet(i, 'weight_kg', parseFloat(e.target.value) || 0)}
                    step="0.5"
                    className="flex-1 h-8 px-2 text-sm text-center bg-surface-card border border-border
                               rounded-md text-text-primary focus:outline-none focus:ring-1 focus:ring-accent"
                  />
                  <input
                    type="number"
                    value={set.reps}
                    onChange={(e) => updateSet(i, 'reps', parseInt(e.target.value) || 0)}
                    className="flex-1 h-8 px-2 text-sm text-center bg-surface-card border border-border
                               rounded-md text-text-primary focus:outline-none focus:ring-1 focus:ring-accent"
                  />
                </div>
              ))}
            </>
          )}

          {/* Add Set button */}
          <button
            onClick={addSet}
            className="w-full p-3 flex items-center justify-center gap-2 rounded-lg border border-dashed border-border
                       text-text-muted hover:text-accent hover:border-accent transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span className="text-sm font-medium">Add Set</span>
          </button>
        </div>
      </div>
    </div>
  );
}
