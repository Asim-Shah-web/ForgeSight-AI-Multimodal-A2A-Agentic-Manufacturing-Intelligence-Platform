import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { getCurrentUser, login as loginRequest } from '@/api/endpoints/auth';
import { registerUnauthorizedHandler, setAuthToken } from '@/api/client';
import { UserResponse } from '@/types/auth';

interface AuthContextValue {
  user: UserResponse | null;
  isAuthenticated: boolean;
  isInitializing: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);

  const logout = useCallback(() => {
    setAuthToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    registerUnauthorizedHandler(logout);
    // No persisted session on hard refresh, by design (see Phase 12 Step 12.1
    // note: the token lives in memory only, never localStorage).
    setIsInitializing(false);
  }, [logout]);

  const login = useCallback(async (username: string, password: string) => {
    const tokenResponse = await loginRequest(username, password);
    setAuthToken(tokenResponse.access_token);
    const currentUser = await getCurrentUser();
    setUser(currentUser);
  }, []);

  const value: AuthContextValue = {
    user,
    isAuthenticated: user !== null,
    isInitializing,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}