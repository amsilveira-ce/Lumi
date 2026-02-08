/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'elder-blue': {
          50: '#e0f2fe',
          100: '#bae6fd',
          500: '#0ea5e9',
          600: '#0284c7',
        },
        'elder-green': {
          50: '#dcfce7',
          100: '#bbf7d0',
          500: '#22c55e',
          600: '#16a34a',
        },
      },
      fontSize: {
        'elder-xs': '0.875rem',
        'elder-sm': '1rem',
        'elder-base': '1.125rem',
        'elder-lg': '1.25rem',
        'elder-xl': '1.5rem',
        'elder-2xl': '1.875rem',
        'elder-3xl': '2.25rem',
        'elder-4xl': '3rem',
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
      },
      minHeight: {
        '12': '3rem',
        '16': '4rem',
        '20': '5rem',
      },
    },
  },
  plugins: [],
}
