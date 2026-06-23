/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: '#0a0e1a',
          secondary: '#0f1629',
          card: '#141d35',
        },
        accent: {
          cyan: '#00d4ff',
          green: '#00ff88',
          red: '#ff3366',
          orange: '#ff6600',
          yellow: '#ffcc00',
        },
        border: '#1e3a5f',
      },
      fontFamily: {
        mono: ['"IBM Plex Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
}
