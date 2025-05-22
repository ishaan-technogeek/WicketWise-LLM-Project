'use client'; // <-- MUST be at the top

import { ThemeProvider } from 'next-themes';
import { type ThemeProviderProps } from 'next-themes/dist/types'; // Optional: for types
import * as React from 'react';

export function Providers({ children, ...props }: ThemeProviderProps) {
  return (
    <ThemeProvider {...props}>
      {children}
    </ThemeProvider>
  );
}