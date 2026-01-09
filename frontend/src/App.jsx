import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Layout from './components/Layout';
import Home from './pages/Home';
import Profile from './pages/Profile';
import Goal from './pages/Goal';
import Plan from './pages/Plan';
import Workout from './pages/Workout';
import Log from './pages/Log';
import Login from './pages/Login';
import { isLoggedIn } from './hooks/useApi';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      refetchOnWindowFocus: false,
    },
  },
});

// Protected route wrapper
function ProtectedRoute({ children }) {
  if (!isLoggedIn()) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

// Public route wrapper (redirect if already logged in)
function PublicRoute({ children }) {
  if (isLoggedIn()) {
    return <Navigate to="/" replace />;
  }
  return children;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public route - Login */}
          <Route 
            path="/login" 
            element={
              <PublicRoute>
                <Login />
              </PublicRoute>
            } 
          />
          
          {/* Protected routes - wrapped in Layout */}
          <Route 
            path="/*" 
            element={
              <ProtectedRoute>
                <Layout>
                  <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/profile" element={<Profile />} />
                    <Route path="/goal" element={<Goal />} />
                    <Route path="/plan" element={<Plan />} />
                    <Route path="/workout" element={<Workout />} />
                    <Route path="/log" element={<Log />} />
                  </Routes>
                </Layout>
              </ProtectedRoute>
            } 
          />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
