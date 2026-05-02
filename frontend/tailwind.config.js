/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        syne: ['Syne', 'sans-serif'],
        newsreader: ['Newsreader', 'serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        noir: {
          950: '#0A0A0B',
          900: '#111114',
          850: '#151518',
          800: '#1A1A1F',
          700: '#232329',
          600: '#2E2E36',
          500: '#5A5A66',
          400: '#7A7A87',
          300: '#A8A3B3',
          200: '#D4D0DC',
          100: '#EDEAF2',
          50: '#FFFFFF',
        },
        amber: {
          900: '#2A200E',
          700: '#8A6B2E',
          600: '#B8903D',
          500: '#D4A853',
          400: '#E0BE78',
          300: '#EDD5A0',
        },
        jade: {
          900: '#0D1F18',
          700: '#1F4D3C',
          600: '#2D6B54',
          500: '#3B8C6E',
          400: '#4DA882',
          300: '#6BBF9A',
        },
        crimson: {
          900: '#1F0B09',
          600: '#962D22',
          500: '#C0392B',
          400: '#D94F42',
        },
      },
    },
  },
  plugins: [],
}
