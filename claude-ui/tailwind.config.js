/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        agent: {
          supervisor: '#8b5cf6',
          master: '#ef4444',
          backend: '#3b82f6',
          database: '#10b981',
          frontend: '#f59e0b',
          testing: '#06b6d4',
          deployment: '#6366f1',
          queue: '#ec4899',
          instagram: '#e11d48',
        },
        status: {
          online: '#10b981',
          offline: '#6b7280',
          busy: '#f59e0b',
          error: '#ef4444',
        },
      },
    },
  },
  plugins: [],
}