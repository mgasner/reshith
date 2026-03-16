/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        hebrew: ['SBL Hebrew', 'Ezra SIL', 'serif'],
        greek: ['SBL Greek', 'Gentium Plus', 'serif'],
        devanagari: ['Siddhanta', 'Sanskrit 2003', 'serif'],
      },
    },
  },
  plugins: [],
}
