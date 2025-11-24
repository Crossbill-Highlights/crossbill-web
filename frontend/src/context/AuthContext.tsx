import { useNavigate } from '@tanstack/react-router';
import { createContext, ReactNode, useCallback, useContext, useEffect, useState } from 'react';
import { useLoginApiV1AuthLoginPost } from '../api/generated/auth/auth';
import type { UserDetailsResponse } from '../api/generated/model';
import { getMeApiV1UsersMeGet } from '@/api/generated/users/users.ts';

const AUTH_TOKEN_KEY = 'auth_token';

interface AuthContextType {
  token: string | null;
  user: UserDetailsResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(AUTH_TOKEN_KEY));
  const [user, setUser] = useState<UserDetailsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  const loginMutation = useLoginApiV1AuthLoginPost();

  const logout = useCallback(() => {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    setToken(null);
    setUser(null);
    navigate({ to: '/login' });
  }, [navigate]);

  const refreshUser = useCallback(async () => {
    try {
      const userData = await getMeApiV1UsersMeGet();
      setUser(userData);
    } catch {
      // If refresh fails, user might be logged out
      logout();
    }
  }, [logout]);

  // Validate token and fetch user on mount
  useEffect(() => {
    const validateToken = async () => {
      const storedToken = localStorage.getItem(AUTH_TOKEN_KEY);
      if (!storedToken) {
        setIsLoading(false);
        return;
      }

      try {
        const userData = await getMeApiV1UsersMeGet();
        setUser(userData);
        setToken(storedToken);
      } catch {
        // Token is invalid, clear it
        localStorage.removeItem(AUTH_TOKEN_KEY);
        setToken(null);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    validateToken();
  }, []);

  const login = async (username: string, password: string) => {
    const response = await loginMutation.mutateAsync({
      data: { username, password },
    });

    localStorage.setItem(AUTH_TOKEN_KEY, response.access_token);
    setToken(response.access_token);

    // Fetch user details after login
    const userData = await getMeApiV1UsersMeGet();
    setUser(userData);
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        isAuthenticated: !!token && !!user,
        isLoading,
        login,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
