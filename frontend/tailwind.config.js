/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Core palette - 复古印刷美学
        ink: {
          black: '#1a1a1a',
          dark: '#2d2d2d',
        },
        paper: {
          cream: '#f5f0e6',
          aged: '#ebe5d5',
          white: '#faf8f3',
        },
        // Accent
        accent: {
          orange: '#d4652f',
          red: '#c41e3a',
        },
        // Pioneer - 理性蓝调
        pioneer: {
          ink: '#0a2540',
          blue: '#0066cc',
          light: '#e8f0f8',
        },
        // Shoegaze - 梦幻紫调
        shoegaze: {
          purple: '#6b4c9a',
          pink: '#b76e8c',
          lavender: '#e8dff0',
        },
        // Old colors (keep for compatibility)
        primary: '#CC785C',
        'primary-dark': '#B86A4F',
        sidebar: '#1F2937',
        'sidebar-hover': '#374151',
      },
      fontFamily: {
        serif: ['Noto Serif SC', 'Noto Serif', 'Georgia', 'serif'],
        mono: ['IBM Plex Mono', 'monospace'],
        sans: ['Noto Sans SC', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
      animation: {
        'fade-in-up': 'fadeInUp 0.5s ease-out forwards',
        'stamp': 'stamp 0.3s ease-out forwards',
      },
      keyframes: {
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        stamp: {
          '0%': { transform: 'scale(1.2)', opacity: '0' },
          '50%': { transform: 'scale(0.95)' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
