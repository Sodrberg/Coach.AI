import { useState } from 'react';
import ExerciseItem from './ExerciseItem';
import ExercisePicker from './ExercisePicker';

const typeStyles = {
  strength: 'badge-strength',
  endurance: 'badge-endurance',
  intervals: 'badge-intervals',
  recovery: 'badge-recovery',
  rest: 'badge-rest',
};

export default function WorkoutCard({ workout, editable = false, onWorkoutChange }) {
  const [expandedSections, setExpandedSections] = useState({ main: true });
  const [pickerOpen, setPickerOpen] = useState(false);
  const [targetSection, setTargetSection] = useState(null);

  const toggleSection = (sectionName) => {
    setExpandedSections((prev) => ({
      ...prev,
      [sectionName]: !prev[sectionName],
    }));
  };

  // Handle exercise update within a section
  const handleExerciseUpdate = (sectionIndex, exerciseIndex, updatedExercise) => {
    if (!onWorkoutChange) return;
    
    const newSections = [...workout.sections];
    newSections[sectionIndex] = {
      ...newSections[sectionIndex],
      items: newSections[sectionIndex].items.map((item, idx) =>
        idx === exerciseIndex ? updatedExercise : item
      ),
    };
    
    onWorkoutChange({
      ...workout,
      sections: newSections,
    });
  };

  // Handle exercise removal
  const handleExerciseRemove = (sectionIndex, exerciseIndex) => {
    if (!onWorkoutChange) return;
    
    const newSections = [...workout.sections];
    newSections[sectionIndex] = {
      ...newSections[sectionIndex],
      items: newSections[sectionIndex].items.filter((_, idx) => idx !== exerciseIndex),
    };
    
    onWorkoutChange({
      ...workout,
      sections: newSections,
    });
  };

  // Handle adding new exercise from picker
  const handleAddExercise = (newExercise, sectionName) => {
    if (!onWorkoutChange) return;
    
    const sectionIndex = workout.sections.findIndex((s) => s.name === sectionName);
    if (sectionIndex === -1) return;
    
    const newSections = [...workout.sections];
    newSections[sectionIndex] = {
      ...newSections[sectionIndex],
      items: [...newSections[sectionIndex].items, newExercise],
    };
    
    onWorkoutChange({
      ...workout,
      sections: newSections,
    });
  };

  // Open exercise picker for a specific section
  const openPickerForSection = (sectionName) => {
    setTargetSection(sectionName);
    setPickerOpen(true);
  };

  const badgeClass = typeStyles[workout.workout_type] || 'badge-rest';

  return (
    <>
      <div className="card">
        {/* Header */}
        <div className="flex items-start justify-between mb-5">
          <div>
            <h2 className="text-xl font-heading font-bold text-text-primary">{workout.title}</h2>
            <div className="flex items-center gap-3 mt-3">
              <span className={badgeClass}>{workout.workout_type}</span>
              <span className="text-sm text-text-secondary">
                {workout.estimated_duration_min} min
              </span>
              <span className="text-sm text-text-muted">•</span>
              <span className="text-sm text-text-secondary">
                {workout.intensity_target}
              </span>
            </div>
          </div>
        </div>

        {/* Rationale */}
        {workout.rationale && workout.rationale.length > 0 && (
          <div className="mb-5 p-4 bg-surface-elevated rounded-lg border border-border">
            <p className="text-sm text-text-secondary leading-relaxed">
              {workout.rationale[0]}
            </p>
          </div>
        )}

        {/* Sections */}
        <div className="space-y-3">
          {workout.sections.map((section, sectionIndex) => (
            <div key={section.name} className="border border-border rounded-lg overflow-hidden">
              <button
                onClick={() => toggleSection(section.name)}
                className="w-full flex items-center justify-between p-4 bg-surface-elevated 
                         hover:bg-surface-hover transition-colors"
              >
                <span className="font-heading font-semibold capitalize text-text-primary">
                  {section.name}
                </span>
                <div className="flex items-center gap-3">
                  <span className="text-sm text-text-muted">
                    {section.items.length} exercises
                  </span>
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
                      editable={editable}
                      onUpdate={(updated) => handleExerciseUpdate(sectionIndex, exerciseIndex, updated)}
                      onRemove={() => handleExerciseRemove(sectionIndex, exerciseIndex)}
                    />
                  ))}
                  
                  {/* Add Exercise Button */}
                  {editable && (
                    <button
                      onClick={() => openPickerForSection(section.name)}
                      className="w-full p-4 flex items-center justify-center gap-2 
                                 text-text-muted hover:text-accent hover:bg-surface-elevated
                                 transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                      <span className="text-sm font-medium">Add Exercise</span>
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}
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
    </>
  );
}
