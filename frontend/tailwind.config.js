/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        darkbg: '#09090B',
        dark2: '#111113',
        elevated: '#18181B',
        charcoal: '#27272A',
        primaryText: '#FAFAF5',
        secondaryText: '#A1A1AA',
        mutedText: '#71717A',
        amber: {
          50: '#FFFBEB',
          100: '#FEF3C7', // Pale Amber
          200: '#FDE68A',
          300: '#FCD34D',
          400: '#FBBF24',
          500: '#F59E0B', // Bright Amber
          600: '#D97706', // Primary Accent
          700: '#B45309',
          800: '#92400E',
          900: '#78350F',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['Manrope', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'monospace'],
      },
      boxShadow: {
        'glass-panel': '0 20px 60px rgba(0, 0, 0, 0.55), inset 0 1px 0 rgba(255, 255, 255, 0.12)',
        'glass-card': '0 12px 36px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.08)',
        'amber-glow-sm': '0 0 15px rgba(217, 119, 6, 0.25)',
        'amber-glow': '0 0 30px rgba(217, 119, 6, 0.32)',
        'amber-glow-lg': '0 0 60px rgba(245, 158, 11, 0.40)',
      },
      borderRadius: {
        'card': '24px',
        'control': '14px',
      },
      transitionDuration: {
        'fast': '160ms',
        'normal': '220ms',
        'slow': '320ms',
      },
    },
  },
  plugins: [],
}
