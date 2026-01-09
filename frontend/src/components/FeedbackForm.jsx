import { useState } from 'react';
import { useSubmitFeedback, getUserId } from '../hooks/useApi';

const feedbackOptions = [
  { status: 'great', label: "I feel great!", icon: '💪' },
  { status: 'sore', label: "I'm sore", icon: '😣' },
  { status: 'tired', label: "I'm tired", icon: '😴' },
  { status: 'pain', label: 'I have pain', icon: '🤕' },
];

const bodyParts = [
  'shoulder', 'back', 'knee', 'hip', 'ankle', 'wrist', 'elbow', 'neck', 'chest', 'core'
];

export default function FeedbackForm({ onComplete }) {
  const [selectedStatus, setSelectedStatus] = useState(null);
  const [bodyPart, setBodyPart] = useState('');
  const [severity, setSeverity] = useState(3);
  
  const submitFeedback = useSubmitFeedback();

  const handleSubmit = () => {
    const feedback = {
      user_id: getUserId(),
      status: selectedStatus,
      body_part: selectedStatus === 'pain' || selectedStatus === 'sore' ? bodyPart : null,
      severity: selectedStatus === 'pain' || selectedStatus === 'sore' ? severity : null,
      timestamp: new Date().toISOString(),
    };

    submitFeedback.mutate(feedback, {
      onSuccess: (data) => {
        onComplete?.(data);
      },
    });
  };

  const needsDetails = selectedStatus === 'pain' || selectedStatus === 'sore';

  return (
    <div className="card">
      <h3 className="section-header">
        How are you feeling today?
      </h3>

      {/* Feedback buttons */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        {feedbackOptions.map((option) => (
          <button
            key={option.status}
            onClick={() => setSelectedStatus(option.status)}
            className={`selection-card text-center ${
              selectedStatus === option.status ? 'selection-card-active' : ''
            }`}
          >
            <span className="text-3xl block mb-2">{option.icon}</span>
            <span className="text-sm font-heading font-medium">{option.label}</span>
          </button>
        ))}
      </div>

      {/* Additional details for pain/sore */}
      {needsDetails && (
        <div className="space-y-5 pt-5 border-t border-border animate-in">
          <div>
            <label className="label">Where?</label>
            <select
              value={bodyPart}
              onChange={(e) => setBodyPart(e.target.value)}
              className="input"
            >
              <option value="">Select body part...</option>
              {bodyParts.map((part) => (
                <option key={part} value={part}>
                  {part.charAt(0).toUpperCase() + part.slice(1)}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="label">Severity (1-5)</label>
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5].map((num) => (
                <button
                  key={num}
                  type="button"
                  onClick={() => setSeverity(num)}
                  className={`flex-1 py-2.5 rounded-lg font-heading font-semibold transition-all ${
                    severity === num
                      ? 'bg-accent text-surface-base shadow-sm'
                      : 'bg-surface-elevated text-text-muted hover:bg-surface-hover'
                  }`}
                >
                  {num}
                </button>
              ))}
            </div>
            <p className="text-xs text-text-muted mt-2">
              1 = Mild discomfort, 5 = Severe pain
            </p>
          </div>
        </div>
      )}

      {/* Submit button */}
      {selectedStatus && (
        <button
          onClick={handleSubmit}
          disabled={submitFeedback.isPending || (needsDetails && !bodyPart)}
          className="btn-primary w-full mt-5 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {submitFeedback.isPending ? 'Submitting...' : 'Continue to Workout'}
        </button>
      )}

      {submitFeedback.isError && (
        <p className="text-danger text-sm mt-3 text-center">
          Failed to submit feedback. Please try again.
        </p>
      )}
    </div>
  );
}
