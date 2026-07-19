/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        mindflow: {
          bg: '#0f172a',
          surface: '#1e293b',
          border: '#334155',
          accent: '#38bdf8',
          success: '#22c55e',
          warning: '#f59e0b',
          danger: '#ef4444',
        },
      },
    },
  },
  plugins: [],
}
