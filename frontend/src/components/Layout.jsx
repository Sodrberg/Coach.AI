import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useLogout, useCurrentUser } from '../hooks/useApi';
import { useRef, useEffect, useState } from 'react';

const navItems = [
  {
    path: '/',
    label: 'Home',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
    ),
  },
  {
    path: '/plan',
    label: 'Plan',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    ),
  },
  {
    path: '/workout',
    label: 'Train',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
  },
  {
    path: '/profile',
    label: 'Profile',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
      </svg>
    ),
  },
];

export default function Layout({ children }) {
  const location = useLocation();
  const navigate = useNavigate();
  const logoutMutation = useLogout();
  const user = useCurrentUser();
  const [isTransitioning, setIsTransitioning] = useState(false);
  const prevPathRef = useRef(location.pathname);

  useEffect(() => {
    if (prevPathRef.current !== location.pathname) {
      setIsTransitioning(true);
      prevPathRef.current = location.pathname;
      const timer = setTimeout(() => setIsTransitioning(false), 150);
      return () => clearTimeout(timer);
    }
  }, [location.pathname]);

  const handleLogout = async () => {
    await logoutMutation.mutateAsync();
    navigate('/login');
  };

  return (
    <div className="min-h-screen flex flex-col bg-surface-base">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-surface-base/80 backdrop-blur-nav border-b border-border">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center gap-3 group">
              <div className="w-9 h-9 rounded-lg bg-accent/10 flex items-center justify-center group-hover:bg-accent/20 transition-colors">
                <span className="text-accent font-heading font-bold text-lg">TC</span>
              </div>
              <span className="text-lg font-heading font-semibold text-text-primary hidden sm:block">
                Training Coach
              </span>
            </Link>

            {/* User menu */}
            <div className="flex items-center gap-4">
              {user?.name && (
                <span className="text-sm text-text-secondary hidden sm:inline font-medium">
                  {user.name}
                </span>
              )}
              <button
                onClick={handleLogout}
                className="text-text-muted hover:text-text-primary text-sm font-medium
                         transition-colors duration-200 px-3 py-1.5 rounded-lg
                         hover:bg-surface-card"
                aria-label="Log out"
              >
                Log out
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <div className={`max-w-4xl mx-auto px-4 py-8 page-transition ${isTransitioning ? 'page-transition-enter' : ''}`}>
          {children}
        </div>
      </main>

      {/* Bottom navigation */}
      <nav className="sticky bottom-0 bg-surface-elevated/95 backdrop-blur-nav border-t border-border" role="navigation" aria-label="Main navigation">
        <div className="max-w-4xl mx-auto">
          <div className="flex justify-around">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`relative flex flex-col items-center py-3 px-6 transition-all duration-200 ${
                    isActive
                      ? 'text-accent'
                      : 'text-text-muted hover:text-text-secondary'
                  }`}
                  aria-label={item.label}
                  aria-current={isActive ? 'page' : undefined}
                >
                  {/* Active indicator */}
                  {isActive && (
                    <span className="absolute top-0 left-1/2 -translate-x-1/2 w-8 h-0.5 bg-accent rounded-full" />
                  )}
                  {item.icon}
                  <span className={`text-xs font-heading font-medium mt-1 ${isActive ? 'font-semibold' : ''}`}>
                    {item.label}
                  </span>
                </Link>
              );
            })}
          </div>
        </div>
      </nav>
    </div>
  );
}
