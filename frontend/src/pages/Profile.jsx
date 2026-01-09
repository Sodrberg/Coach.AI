import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { useProfile, useSaveProfile, getUserId } from '../hooks/useApi';
import LoadingSpinner from '../components/LoadingSpinner';

const fitnessLevels = ['beginner', 'intermediate', 'advanced'];
const equipmentOptions = [
  'barbell', 'dumbbells', 'kettlebells', 'pull_up_bar', 
  'resistance_bands', 'gym', 'ski_erg', 'rowing_machine', 'none'
];
const daysOfWeek = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];

export default function Profile() {
  const navigate = useNavigate();
  const { data: profile, isLoading } = useProfile();
  const saveProfile = useSaveProfile();
  
  const { register, handleSubmit, formState: { errors }, watch } = useForm({
    defaultValues: profile || {
      user_id: getUserId(),
      age: 30,
      weight_kg: 70,
      height_cm: 175,
      fitness_level: 'intermediate',
      training_history_years: 2,
      available_equipment: ['gym'],
      training_days_per_week: 4,
      preferred_training_days: [],
    },
  });

  const onSubmit = (data) => {
    if (typeof data.available_equipment === 'string') {
      data.available_equipment = [data.available_equipment];
    }
    if (typeof data.preferred_training_days === 'string') {
      data.preferred_training_days = [data.preferred_training_days];
    }
    
    data.user_id = getUserId();
    
    saveProfile.mutate(data, {
      onSuccess: () => {
        navigate('/goal');
      },
    });
  };

  if (isLoading) {
    return <LoadingSpinner message="Loading profile..." />;
  }

  return (
    <div className="space-y-6 animate-in">
      <div className="mb-8">
        <h1 className="text-2xl font-heading font-bold text-text-primary">Your Profile</h1>
        <p className="text-text-secondary mt-2">
          Tell us about yourself so we can create the perfect training plan.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Basic Info */}
        <div className="card">
          <h2 className="section-header">Basic Information</h2>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Age</label>
              <input
                type="number"
                {...register('age', { required: true, min: 13, max: 100 })}
                className="input"
              />
              {errors.age && <span className="text-danger text-sm mt-1 block">Valid age required</span>}
            </div>

            <div>
              <label className="label">Weight (kg)</label>
              <input
                type="number"
                step="0.1"
                {...register('weight_kg', { required: true, min: 30 })}
                className="input"
              />
            </div>

            <div>
              <label className="label">Height (cm)</label>
              <input
                type="number"
                {...register('height_cm', { required: true, min: 100, max: 250 })}
                className="input"
              />
            </div>

            <div>
              <label className="label">Gender (optional)</label>
              <select {...register('gender')} className="input">
                <option value="">Prefer not to say</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
        </div>

        {/* Training Experience */}
        <div className="card">
          <h2 className="section-header">Training Experience</h2>

          <div className="space-y-5">
            <div>
              <label className="label">Fitness Level</label>
              <div className="grid grid-cols-3 gap-3">
                {fitnessLevels.map((level) => (
                  <label
                    key={level}
                    className={`selection-card text-center ${
                      watch('fitness_level') === level ? 'selection-card-active' : ''
                    }`}
                  >
                    <input
                      type="radio"
                      {...register('fitness_level')}
                      value={level}
                      className="sr-only"
                    />
                    <span className="font-heading font-medium capitalize">{level}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="label">Years of Training Experience</label>
              <input
                type="number"
                {...register('training_history_years', { required: true, min: 0 })}
                className="input"
              />
            </div>

            <div>
              <label className="label">Any Injuries or Limitations?</label>
              <textarea
                {...register('injuries_or_limitations')}
                placeholder="E.g., Lower back issues, recovering from knee surgery..."
                className="input min-h-[100px] resize-none"
              />
            </div>
          </div>
        </div>

        {/* Equipment & Schedule */}
        <div className="card">
          <h2 className="section-header">Equipment & Schedule</h2>

          <div className="space-y-5">
            <div>
              <label className="label">Available Equipment</label>
              <div className="grid grid-cols-3 gap-2">
                {equipmentOptions.map((equipment) => (
                  <label
                    key={equipment}
                    className="flex items-center gap-3 p-3 rounded-lg border border-border 
                             hover:bg-surface-hover cursor-pointer transition-colors group"
                  >
                    <input
                      type="checkbox"
                      {...register('available_equipment')}
                      value={equipment}
                      className="w-4 h-4 rounded border-border text-accent 
                               focus:ring-accent focus:ring-offset-0 bg-surface-elevated"
                    />
                    <span className="text-sm text-text-secondary group-hover:text-text-primary 
                                   capitalize transition-colors">
                      {equipment.replace('_', ' ')}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="label">Training Days Per Week</label>
              <input
                type="number"
                {...register('training_days_per_week', { required: true, min: 1, max: 7 })}
                className="input w-32"
                min={1}
                max={7}
              />
            </div>

            <div>
              <label className="label">Preferred Training Days (optional)</label>
              <div className="flex flex-wrap gap-2">
                {daysOfWeek.map((day) => (
                  <label
                    key={day}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border 
                             hover:bg-surface-hover cursor-pointer transition-colors"
                  >
                    <input
                      type="checkbox"
                      {...register('preferred_training_days')}
                      value={day}
                      className="w-4 h-4 rounded border-border text-accent 
                               focus:ring-accent focus:ring-offset-0 bg-surface-elevated"
                    />
                    <span className="text-sm text-text-secondary capitalize">{day.slice(0, 3)}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={saveProfile.isPending}
          className="btn-primary w-full py-4 text-base disabled:opacity-50"
        >
          {saveProfile.isPending ? 'Saving...' : 'Continue to Goals'}
        </button>

        {saveProfile.isError && (
          <p className="text-danger text-center text-sm">
            Failed to save profile. Please try again.
          </p>
        )}
      </form>
    </div>
  );
}
