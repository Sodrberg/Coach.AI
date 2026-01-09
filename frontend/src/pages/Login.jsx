import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { useRegister, useLogin } from '../hooks/useApi';

export default function Login() {
  const navigate = useNavigate();
  const [isNewUser, setIsNewUser] = useState(true);
  const registerMutation = useRegister();
  const loginMutation = useLogin();

  const { register, handleSubmit, formState: { errors } } = useForm({
    defaultValues: {
      name: '',
      email: '',
    },
  });

  const onSubmit = async (data) => {
    try {
      if (isNewUser) {
        const result = await registerMutation.mutateAsync({
          name: data.name,
          email: data.email,
        });
        if (result.session_id) {
          navigate('/');
        }
      } else {
        const result = await loginMutation.mutateAsync(data.email);
        if (result.session_id) {
          navigate('/');
        }
      }
    } catch (error) {
      console.error('Auth error:', error);
    }
  };

  const isPending = registerMutation.isPending || loginMutation.isPending;
  const error = registerMutation.error || loginMutation.error;

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 bg-surface-base relative overflow-hidden">
      {/* Atmospheric background */}
      <div className="absolute inset-0 bg-radial-gradient" />
      <div className="absolute inset-0 bg-grid-pattern opacity-50" />
      
      {/* Subtle glow orb */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-accent/5 rounded-full blur-3xl" />

      {/* Content */}
      <div className="relative z-10 w-full max-w-md animate-in-up">
        {/* Logo/Brand */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-surface-card border border-border mb-6 shadow-glow-sm">
            <span className="text-accent font-heading font-bold text-2xl">TC</span>
          </div>
          <h1 className="text-3xl font-heading font-bold text-text-primary mb-2">
            Training Coach
          </h1>
          <p className="text-text-secondary">
            AI-powered personalized training plans
          </p>
        </div>

        {/* Auth Card */}
        <div className="card">
          {/* Toggle */}
          <div className="flex gap-2 p-1 bg-surface-elevated rounded-lg mb-6">
            <button
              type="button"
              onClick={() => setIsNewUser(true)}
              className={`flex-1 py-2.5 rounded-md font-heading font-medium text-sm transition-all duration-200 ${
                isNewUser
                  ? 'bg-accent text-surface-base shadow-sm'
                  : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              New User
            </button>
            <button
              type="button"
              onClick={() => setIsNewUser(false)}
              className={`flex-1 py-2.5 rounded-md font-heading font-medium text-sm transition-all duration-200 ${
                !isNewUser
                  ? 'bg-accent text-surface-base shadow-sm'
                  : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              Sign In
            </button>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            {/* Name field - only for new users */}
            {isNewUser && (
              <div className="animate-in">
                <label className="label">
                  Your Name
                </label>
                <input
                  type="text"
                  {...register('name', { required: isNewUser })}
                  placeholder="Enter your name"
                  className="input"
                  autoComplete="name"
                />
                {errors.name && (
                  <p className="text-danger text-sm mt-2">Name is required</p>
                )}
              </div>
            )}

            {/* Email field */}
            <div>
              <label className="label">
                Email Address
              </label>
              <input
                type="email"
                {...register('email', { 
                  required: true,
                  pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/
                })}
                placeholder="your@email.com"
                className="input"
                autoComplete="email"
              />
              {errors.email && (
                <p className="text-danger text-sm mt-2">Valid email is required</p>
              )}
            </div>

            {/* Error message */}
            {error && (
              <div className="p-4 rounded-lg bg-danger/10 border border-danger/30">
                <p className="text-danger text-sm">
                  {error.data?.message || error.message || 'Authentication failed'}
                </p>
              </div>
            )}

            {/* Submit button */}
            <button
              type="submit"
              disabled={isPending}
              className="btn-primary w-full py-3.5 text-base disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isPending ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-surface-base/30 border-t-surface-base rounded-full animate-spin" />
                  {isNewUser ? 'Creating Account...' : 'Signing In...'}
                </span>
              ) : (
                isNewUser ? 'Get Started' : 'Sign In'
              )}
            </button>
          </form>

          {/* Info */}
          <p className="text-center text-sm text-text-muted mt-6">
            {isNewUser ? (
              <>No password needed. We'll remember you by your email.</>
            ) : (
              <>Enter the email you registered with.</>
            )}
          </p>
        </div>

        {/* Footer */}
        <p className="text-text-muted text-sm mt-8 text-center">
          Your data stays private and secure
        </p>
      </div>
    </div>
  );
}
