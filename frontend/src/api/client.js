/**
 * API client for Training Coach backend
 */

const API_BASE = '/api/v1';

// Session management
export const getSessionId = () => localStorage.getItem('sessionId');
export const setSessionId = (id) => localStorage.setItem('sessionId', id);
export const clearSession = () => {
  localStorage.removeItem('sessionId');
  localStorage.removeItem('userId');
  localStorage.removeItem('userName');
  localStorage.removeItem('userEmail');
};

export const getStoredUser = () => {
  const sessionId = getSessionId();
  if (!sessionId) return null;
  return {
    sessionId,
    userId: localStorage.getItem('userId'),
    name: localStorage.getItem('userName'),
    email: localStorage.getItem('userEmail'),
  };
};

export const storeUser = (authResponse) => {
  localStorage.setItem('sessionId', authResponse.session_id);
  localStorage.setItem('userId', authResponse.user_id);
  localStorage.setItem('userName', authResponse.name);
  localStorage.setItem('userEmail', authResponse.email);
};

class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

async function request(endpoint, options = {}) {
  // Auto-attach session_id for authentication
  const sessionId = getSessionId();
  let url = `${API_BASE}${endpoint}`;
  if (sessionId) {
    const separator = url.includes('?') ? '&' : '?';
    url = `${url}${separator}session_id=${encodeURIComponent(sessionId)}`;
  }

  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  if (options.body && typeof options.body === 'object') {
    config.body = JSON.stringify(options.body);
  }

  const response = await fetch(url, config);
  
  let data;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    throw new ApiError(
      data?.message || 'An error occurred',
      response.status,
      data
    );
  }

  return data;
}

// Auth endpoints
export const authApi = {
  register: (name, email) => 
    request(`/auth/register?name=${encodeURIComponent(name)}&email=${encodeURIComponent(email)}`, { method: 'POST' }),
  login: (email) => 
    request(`/auth/login?email=${encodeURIComponent(email)}`, { method: 'POST' }),
  logout: (sessionId) => 
    request(`/auth/logout?session_id=${sessionId}`, { method: 'POST' }),
  me: (sessionId) => 
    request(`/auth/me?session_id=${sessionId}`),
};

// Profile endpoints
export const profileApi = {
  save: (profile) => request('/profile', { method: 'POST', body: profile }),
  get: (userId) => request(`/profile/${userId}`),
};

// Goal endpoints
export const goalApi = {
  save: (goal) => request('/goal', { method: 'POST', body: goal }),
  get: (userId) => request(`/goal/${userId}`),
};

// Plan endpoints
export const planApi = {
  generate: (userId, goalId) => 
    request(`/plan/generate?user_id=${userId}&goal_id=${goalId}`, { method: 'POST' }),
};

// Workout endpoints
export const workoutApi = {
  getToday: (userId) => request(`/workout/today?user_id=${userId}`),
  getByDate: (userId, date) => request(`/workout/by-date?user_id=${userId}&date=${date}`),
  submitFeedback: (feedback) => request('/workout/feedback', { method: 'POST', body: feedback }),
  log: (log) => request('/workout/log', { method: 'POST', body: log }),
  resolvePending: (userId, pendingDate, resolution) => 
    request(`/workout/resolve-pending?user_id=${userId}&pending_date=${pendingDate}&resolution=${resolution}`, { method: 'POST' }),
  swapToToday: (userId) => 
    request(`/workout/swap-to-today?user_id=${userId}`, { method: 'POST' }),
  saveCustom: (workout) => 
    request('/workout/custom', { method: 'POST', body: workout }),
  move: (userId, fromDate, toDate) =>
    request(`/workout/move?user_id=${userId}&from_date=${fromDate}&to_date=${toDate}`, { method: 'POST' }),
};

// Block endpoints
export const blockApi = {
  generateNext: (userId) => 
    request(`/block/generate-next?user_id=${userId}`, { method: 'POST' }),
};

// Exercises endpoints
export const exercisesApi = {
  getAll: ({ search, exerciseType, bodyPart } = {}) => {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (exerciseType) params.append('exercise_type', exerciseType);
    if (bodyPart) params.append('body_part', bodyPart);
    const queryString = params.toString();
    return request(`/exercises${queryString ? `?${queryString}` : ''}`);
  },
};

// Onboarding endpoints
export const onboardApi = {
  quickOnboard: (data) => request('/onboard/quick', { method: 'POST', body: data }),
};

// Health check
export const healthApi = {
  check: () => request('/health'),
};

export { ApiError };
