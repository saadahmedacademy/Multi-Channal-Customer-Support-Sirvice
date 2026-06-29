'use client';

import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';

interface AuthState {
  isAdmin: boolean;
  isAdminMode: boolean;
  loading: boolean;
  enableAdmin: (key: string) => Promise<boolean>;
  disableAdmin: () => Promise<void>;
}

const AuthContext = createContext<AuthState>({
  isAdmin: false,
  isAdminMode: false,
  loading: true,
  enableAdmin: async () => false,
  disableAdmin: async () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/auth/check')
      .then(r => r.json())
      .then(data => {
        setIsAdmin(data.isAdmin);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const enableAdmin = useCallback(async (key: string): Promise<boolean> => {
    try {
      const res = await fetch('/api/auth/set-key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key }),
      });
      const data = await res.json();
      if (data.valid) {
        setIsAdmin(data.isAdmin);
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }, []);

  const disableAdmin = useCallback(async () => {
    await fetch('/api/auth/clear-key', { method: 'POST' });
    setIsAdmin(false);
  }, []);

  return (
    <AuthContext.Provider value={{ isAdmin, isAdminMode: isAdmin, loading, enableAdmin, disableAdmin }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
