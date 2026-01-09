import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useLogout, useCurrentUser } from '../hooks/useApi';

const navItems = [
  { path: '/', label: 'Home' },
  { path: '/plan', label: 'Plan' },
  { path: '/workout', label: 'Train' },
  { path: '/profile', label: 'Profile' },
];

export default function Layout({ children }) {
  const location = useLocation();
  const navigate = useNavigate();
  const logoutMutation = useLogout();
  const user = useCurrentUser();

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
              >
                Log out
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <div className="max-w-4xl mx-auto px-4 py-8">
          {children}
        </div>
      </main>

      {/* Bottom navigation */}
      <nav className="sticky bottom-0 bg-surface-elevated/95 backdrop-blur-nav border-t border-border">
        <div className="max-w-4xl mx-auto">
          <div className="flex justify-around">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`relative flex flex-col items-center py-4 px-6 transition-all duration-200 ${
                    isActive
                      ? 'text-accent'
                      : 'text-text-muted hover:text-text-secondary'
                  }`}
                >
                  {/* Active indicator */}
                  {isActive && (
                    <span className="absolute top-0 left-1/2 -translate-x-1/2 w-8 h-0.5 bg-accent rounded-full" />
                  )}
                  <span className={`text-sm font-heading font-medium ${isActive ? 'font-semibold' : ''}`}>
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
