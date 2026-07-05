import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: ['class'],
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './lib/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        card: 'hsl(var(--card))',
        cardForeground: 'hsl(var(--card-foreground))',
        border: 'hsl(var(--border))',
        muted: 'hsl(var(--muted))',
        mutedForeground: 'hsl(var(--muted-foreground))',
        accent: 'hsl(var(--accent))',
        accentForeground: 'hsl(var(--accent-foreground))',
        primary: 'hsl(var(--primary))',
        primaryForeground: 'hsl(var(--primary-foreground))',
        secondary: 'hsl(var(--secondary))',
        secondaryForeground: 'hsl(var(--secondary-foreground))',
        danger: 'hsl(var(--danger))',
      },
      boxShadow: {
        glow: '0 20px 80px rgba(14, 165, 233, 0.16)',
      },
      backgroundImage: {
        'mesh-light': 'radial-gradient(circle at top left, rgba(14,165,233,0.18), transparent 35%), radial-gradient(circle at top right, rgba(250,204,21,0.18), transparent 30%), linear-gradient(180deg, rgba(248,250,252,1) 0%, rgba(241,245,249,1) 100%)',
        'mesh-dark': 'radial-gradient(circle at top left, rgba(14,165,233,0.18), transparent 35%), radial-gradient(circle at top right, rgba(34,197,94,0.12), transparent 30%), linear-gradient(180deg, rgba(2,6,23,1) 0%, rgba(15,23,42,1) 100%)',
      },
    },
  },
  plugins: [],
};

export default config;
