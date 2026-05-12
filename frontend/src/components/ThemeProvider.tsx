'use client';

import { createContext, useContext, useEffect, useState, ReactNode, useCallback, useRef } from 'react';

type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>('light');
  const isInitialized = useRef(false);
  const isUpdating = useRef(false);

  // Initialize theme from localStorage or system preference (only once on mount)
  useEffect(() => {
    if (isInitialized.current) return;
    
    const savedTheme = localStorage.getItem('theme') as Theme | null;
    
    if (savedTheme === 'light' || savedTheme === 'dark') {
      setTheme(savedTheme);
      console.log('Loaded saved theme:', savedTheme);
    } else {
      // Check system preference
      const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      const initialTheme = systemPrefersDark ? 'dark' : 'light';
      setTheme(initialTheme);
      console.log('Using system preference:', initialTheme);
    }
    
    isInitialized.current = true;
  }, []);

  // Apply theme class to html element whenever theme changes
  useEffect(() => {
    if (!isInitialized.current || isUpdating.current) return;
    
    isUpdating.current = true;
    
    const html = document.documentElement;
    
    // Remove both classes first
    html.classList.remove('light', 'dark');
    
    // Force a reflow to ensure the class change is applied
    void html.offsetHeight;
    
    // Add the new theme class
    html.classList.add(theme);
    
    // Save to localStorage
    localStorage.setItem('theme', theme);
    
    console.log('Theme applied:', theme);
    
    // Release the lock after a short delay
    setTimeout(() => {
      isUpdating.current = false;
    }, 50);
  }, [theme]);

  // Use useCallback with lock to prevent rapid toggling
  const toggleTheme = useCallback(() => {
    if (isUpdating.current) {
      console.log('Toggle ignored - update in progress');
      return;
    }
    
    setTheme(prevTheme => {
      const newTheme = prevTheme === 'light' ? 'dark' : 'light';
      console.log('Toggling from', prevTheme, 'to', newTheme);
      return newTheme;
    });
  }, []);

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
