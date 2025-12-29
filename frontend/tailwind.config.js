/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'Noto Sans JP', 'sans-serif'],
      },
      colors: {
        equity: '#3b82f6',
        bond: '#10b981',
        reit: '#f59e0b',
        commodity: '#eab308',
        core: '#6366f1',
        satellite: '#f43f5e',
      },
    },
  },
  plugins: [],
}
