/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        canvas: '#0D1420',
        surface: '#131D2E',
        card: '#1A2640',
        border: '#26314A',
        cyan: '#4FD8E8',
        violet: '#8B7FF0',
        pink: '#F535AA',
        muted: '#8793AC',
        text: '#E8EDF5',
        text2: '#C4CEDC',
        teal: '#3CEDB0',
        rose: '#F07070',
      },
      fontFamily: {
        display: ['"DM Serif Display"', 'Georgia', 'serif'],
        body: ['"Space Grotesk"', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
