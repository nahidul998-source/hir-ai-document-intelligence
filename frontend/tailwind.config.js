/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Sleek dark-mode oriented palette as per design instructions
        brand: {
          50: '#f5f7fa',
          100: '#e4e8f0',
          200: '#c8d1e0',
          300: '#a2b1cc',
          400: '#758cb3',
          500: '#536e99',
          600: '#40567a',
          700: '#344563',
          800: '#2c3952',
          900: '#1a2233',
        }
      }
    },
  },
  plugins: [],
}
