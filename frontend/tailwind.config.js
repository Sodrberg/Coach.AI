/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        heading: ['Outfit', 'system-ui', 'sans-serif'],
        body: ['Source Sans 3', 'system-ui', 'sans-serif'],
      },
      colors: {
        // Primary accent - warm amber/gold
        accent: {
          DEFAULT: '#f59e0b',
          light: '#fbbf24',
          dark: '#d97706',
          muted: 'rgba(245, 158, 11, 0.15)',
        },
        // Secondary accent - for variety
        secondary: '#10b981',
        // Danger/error states
        danger: '#ef4444',
        // Workout type colors - cohesive jewel tones
        strength: '#a855f7',
        endurance: '#06b6d4',
        intervals: '#f97316',
        recovery: '#22c55e',
        rest: '#64748b',
        // Layered dark backgrounds
        surface: {
          base: '#0a0a0a',
          elevated: '#121215',
          card: '#1a1a1f',
          hover: '#242429',
        },
        // Border colors
        border: {
          DEFAULT: '#27272a',
          light: '#3f3f46',
          accent: 'rgba(245, 158, 11, 0.3)',
        },
        // Text colors
        text: {
          primary: '#fafafa',
          secondary: '#a1a1aa',
          muted: '#71717a',
        },
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'pulse-subtle': 'pulseSubtle 2s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseSubtle: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
        glow: {
          '0%': { boxShadow: '0 0 20px rgba(245, 158, 11, 0.1)' },
          '100%': { boxShadow: '0 0 30px rgba(245, 158, 11, 0.2)' },
        },
      },
      boxShadow: {
        'glow-sm': '0 0 15px rgba(245, 158, 11, 0.1)',
        'glow-md': '0 0 25px rgba(245, 158, 11, 0.15)',
        'glow-lg': '0 0 40px rgba(245, 158, 11, 0.2)',
        'card': '0 4px 20px rgba(0, 0, 0, 0.3)',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-subtle': 'linear-gradient(135deg, var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [],
}
