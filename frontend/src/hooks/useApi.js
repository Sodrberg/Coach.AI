/**
 * React Query hooks for API calls
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  profileApi, 
  goalApi, 
  planApi, 
  workoutApi, 
  blockApi,
  authApi,
  exercisesApi,
  getStoredUser,
  storeUser,
  clearSession,
  getSessionId,
} from '../api/client';

// Get user ID from localStorage
export const getUserId = () => localStorage.getItem('userId');
export const setUserId = (id) => localStorage.setItem('userId', id);

// Check if user is logged in
export const isLoggedIn = () => !!getSessionId();

// Auth hooks
export function useAuth() {
  const sessionId = getSessionId();
  
  return useQuery({
    queryKey: ['auth', sessionId],
    queryFn: () => {
      if (!sessionId) {
        return null;
      }
      return authApi.me(sessionId);
    },
    retry: false,
    staleTime: 1000 * 60 * 10, // 10 minutes
    enabled: !!sessionId,
  });
}

export function useCurrentUser() {
  // Returns stored user data synchronously (for initial render)
  return getStoredUser();
}

export function useRegister() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ name, email }) => authApi.register(name, email),
    onSuccess: (data) => {
      if (data.session_id) {
        storeUser(data);
        queryClient.setQueryData(['auth', data.session_id], data);
      }
    },
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (email) => authApi.login(email),
    onSuccess: (data) => {
      if (data.session_id) {
        storeUser(data);
        queryClient.setQueryData(['auth', data.session_id], data);
      }
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => {
      const sessionId = getSessionId();
      if (sessionId) {
        return authApi.logout(sessionId);
      }
      return Promise.resolve();
    },
    onSuccess: () => {
      clearSession();
      queryClient.clear();
    },
  });
}

// Profile hooks
export function useProfile() {
  const userId = getUserId();
  return useQuery({
    queryKey: ['profile', userId],
    queryFn: () => profileApi.get(userId),
    retry: false,
    enabled: !!userId,
  });
}

export function useSaveProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: profileApi.save,
    onSuccess: (data) => {
      setUserId(data.user_id);
      queryClient.setQueryData(['profile', data.user_id], data);
    },
  });
}

// Goal hooks
export function useGoal() {
  const userId = getUserId();
  return useQuery({
    queryKey: ['goal', userId],
    queryFn: () => goalApi.get(userId),
    retry: false,
    enabled: !!userId,
  });
}

export function useSaveGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: goalApi.save,
    onSuccess: (data) => {
      queryClient.setQueryData(['goal', data.user_id], data);
    },
  });
}

// Plan hooks
export function useGeneratePlan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, goalId }) => planApi.generate(userId, goalId),
    onSuccess: (data) => {
      queryClient.setQueryData(['plan', data.high_level_plan.user_id], data);
    },
  });
}

// Workout hooks
export function useTodayWorkout() {
  const userId = getUserId();
  return useQuery({
    queryKey: ['workout', 'today', userId],
    queryFn: () => workoutApi.getToday(userId),
    retry: false,
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: !!userId,
  });
}

export function useSubmitFeedback() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: workoutApi.submitFeedback,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workout', 'today'] });
    },
  });
}

export function useLogWorkout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: workoutApi.log,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workout'] });
    },
  });
}

export function useResolvePending() {
  const queryClient = useQueryClient();
  const userId = getUserId();
  return useMutation({
    mutationFn: ({ pendingDate, resolution }) => 
      workoutApi.resolvePending(userId, pendingDate, resolution),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workout', 'today'] });
    },
  });
}

// Block hooks
export function useGenerateNextBlock() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userId) => blockApi.generateNext(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plan'] });
    },
  });
}

// Exercises hooks
export function useExercises({ search, exerciseType, bodyPart } = {}) {
  return useQuery({
    queryKey: ['exercises', search, exerciseType, bodyPart],
    queryFn: () => exercisesApi.getAll({ search, exerciseType, bodyPart }),
    staleTime: 1000 * 60 * 30, // 30 minutes - exercises don't change often
  });
}
