/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        hebrew: ['SBL Hebrew', 'Noto Serif Hebrew', 'Ezra SIL', 'serif'],
        'hebrew-script': ['Hebrew Script', 'cursive'],
        rashi: ['Noto Rashi Hebrew', 'serif'],
        greek: ['SBL Greek', 'Gentium Plus', 'serif'],
        devanagari: ['Siddhanta', 'Sanskrit 2003', 'serif'],
      },
    },
  },
  plugins: [],
}
