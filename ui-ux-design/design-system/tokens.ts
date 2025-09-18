/**
 * Design System Tokens - TypeScript Export
 * Auto-generated from tokens.json
 *
 * Usage:
 * import { tokens } from '@/design-system/tokens';
 *
 * const primaryColor = tokens.colors.primary[500];
 * const spacing = tokens.spacing[4];
 */

export const tokens = {
  colors: {
    primary: {
      50: '#eff6ff',
      100: '#dbeafe',
      200: '#bfdbfe',
      300: '#93c5fd',
      400: '#60a5fa',
      500: '#3b82f6',
      600: '#2563eb',
      700: '#1d4ed8',
      800: '#1e40af',
      900: '#1e3a8a',
    },
    secondary: {
      50: '#faf5ff',
      100: '#f3e8ff',
      200: '#e9d5ff',
      300: '#d8b4fe',
      400: '#c084fc',
      500: '#a855f7',
      600: '#9333ea',
      700: '#7e22ce',
      800: '#6b21a8',
      900: '#581c87',
    },
    success: {
      50: '#f0fdf4',
      100: '#dcfce7',
      200: '#bbf7d0',
      300: '#86efac',
      400: '#4ade80',
      500: '#22c55e',
      600: '#16a34a',
      700: '#15803d',
      800: '#166534',
      900: '#14532d',
    },
    warning: {
      50: '#fffbeb',
      100: '#fef3c7',
      200: '#fde68a',
      300: '#fcd34d',
      400: '#fbbf24',
      500: '#f59e0b',
      600: '#d97706',
      700: '#b45309',
      800: '#92400e',
      900: '#78350f',
    },
    error: {
      50: '#fef2f2',
      100: '#fee2e2',
      200: '#fecaca',
      300: '#fca5a5',
      400: '#f87171',
      500: '#ef4444',
      600: '#dc2626',
      700: '#b91c1c',
      800: '#991b1b',
      900: '#7f1d1d',
    },
    gray: {
      50: '#f9fafb',
      100: '#f3f4f6',
      200: '#e5e7eb',
      300: '#d1d5db',
      400: '#9ca3af',
      500: '#6b7280',
      600: '#4b5563',
      700: '#374151',
      800: '#1f2937',
      900: '#111827',
    },
    agent: {
      supervisor: '#8b5cf6',
      master: '#ef4444',
      backend: '#3b82f6',
      database: '#10b981',
      frontend: '#f59e0b',
      testing: '#06b6d4',
      deployment: '#6366f1',
      queue: '#ec4899',
      instagram: '#e11d48',
    },
    status: {
      online: '#10b981',
      offline: '#6b7280',
      busy: '#f59e0b',
      error: '#ef4444',
    },
  },
  spacing: {
    0: '0px',
    1: '0.25rem',
    2: '0.5rem',
    3: '0.75rem',
    4: '1rem',
    5: '1.25rem',
    6: '1.5rem',
    8: '2rem',
    10: '2.5rem',
    12: '3rem',
    16: '4rem',
    20: '5rem',
    24: '6rem',
    32: '8rem',
    40: '10rem',
    48: '12rem',
    56: '14rem',
    64: '16rem',
  },
  typography: {
    fontFamily: {
      sans: ['Inter', 'system-ui', 'sans-serif'].join(', '),
      mono: ['JetBrains Mono', 'monospace'].join(', '),
    },
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      '2xl': '1.5rem',
      '3xl': '1.875rem',
      '4xl': '2.25rem',
      '5xl': '3rem',
    },
    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
    lineHeight: {
      tight: 1.25,
      normal: 1.5,
      relaxed: 1.75,
    },
  },
  borderRadius: {
    none: '0px',
    sm: '0.125rem',
    base: '0.25rem',
    md: '0.375rem',
    lg: '0.5rem',
    xl: '0.75rem',
    '2xl': '1rem',
    full: '9999px',
  },
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    base: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
    '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
  },
  transitions: {
    fast: '150ms',
    base: '250ms',
    slow: '500ms',
  },
  zIndex: {
    base: 0,
    dropdown: 1000,
    sticky: 1100,
    modal: 1200,
    popover: 1300,
    tooltip: 1400,
    notification: 1500,
  },
  breakpoints: {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  },
} as const;

// Type exports for TypeScript
export type Colors = typeof tokens.colors;
export type Spacing = typeof tokens.spacing;
export type Typography = typeof tokens.typography;
export type BorderRadius = typeof tokens.borderRadius;
export type Shadows = typeof tokens.shadows;
export type Transitions = typeof tokens.transitions;
export type ZIndex = typeof tokens.zIndex;
export type Breakpoints = typeof tokens.breakpoints;

// Utility function to get CSS variables
export const getCSSVariable = (path: string): string => {
  return `var(--${path.replace(/\./g, '-')})`;
};

// Generate CSS custom properties
export const generateCSSVariables = (): string => {
  const cssVars: string[] = [':root {'];

  const processObject = (obj: any, prefix = '') => {
    Object.entries(obj).forEach(([key, value]) => {
      const varName = prefix ? `${prefix}-${key}` : key;

      if (typeof value === 'object' && !Array.isArray(value)) {
        processObject(value, varName);
      } else if (Array.isArray(value)) {
        cssVars.push(`  --${varName}: ${value.join(', ')};`);
      } else {
        cssVars.push(`  --${varName}: ${value};`);
      }
    });
  };

  processObject(tokens);
  cssVars.push('}');

  return cssVars.join('\n');
};

// Semantic color mappings
export const semanticColors = {
  background: {
    primary: tokens.colors.gray[50],
    secondary: tokens.colors.gray[100],
    tertiary: tokens.colors.gray[200],
    inverse: tokens.colors.gray[900],
  },
  text: {
    primary: tokens.colors.gray[900],
    secondary: tokens.colors.gray[700],
    tertiary: tokens.colors.gray[500],
    inverse: tokens.colors.gray[50],
  },
  border: {
    light: tokens.colors.gray[200],
    default: tokens.colors.gray[300],
    dark: tokens.colors.gray[400],
  },
  focus: {
    ring: tokens.colors.primary[500],
    border: tokens.colors.primary[600],
  },
};

export default tokens;