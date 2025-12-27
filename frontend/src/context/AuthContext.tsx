import { getMeApiV1UsersMeGet } from '@/api/generated/users/users.ts';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from '@tanstack/react-router';
import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react';
import { AXIOS_INSTANCE } from '../api/axios-instance';
import { useLoginApiV1AuthLoginPost } from '../api/generated/auth/auth';
import type { UserDetailsResponse } from '../api/generated/model';
import { getRegisterApiV1UsersRegisterPostMutationOptions } from '../api/generated/users/users';
import { clearTokens, getAccessToken, setAccessToken } from '../api/token-manager';

// Legacy localStorage key for migration cleanup
const LEGACY_AUTH_TOKEN_KEY = 'auth_token';

interface AuthContextType {
  user: UserDetailsResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserDetailsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const refreshTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const loginMutation = useLoginApiV1AuthLoginPost();
  const registerMutation = useMutation(getRegisterApiV1UsersRegisterPostMutationOptions());

  // Clear scheduled refresh
  const clearRefreshTimeout = useCallback(() => {
    if (refreshTimeoutRef.current) {
      clearTimeout(refreshTimeoutRef.current);
      refreshTimeoutRef.current = null;
    }
  }, []);

  // Schedule token refresh at 75% of token lifetime (or 1 min before expiry)
  const scheduleTokenRefresh = useCallback(
    (expiresIn: number) => {
      clearRefreshTimeout();

      // Refresh at 75% of token lifetime or 1 minute before expiry, whichever is earlier
      const refreshTime = Math.min(expiresIn * 0.75, expiresIn - 60) * 1000;
      if (refreshTime <= 0) return;

      refreshTimeoutRef.current = setTimeout(async () => {
        try {
          await silentRefresh();
        } catch {
          // If refresh fails, user will need to re-authenticate
          clearTokens();
          setUser(null);
        }
      }, refreshTime);
    },
    [clearRefreshTimeout]
  );

  // Silent refresh using httpOnly cookie
  const silentRefresh = useCallback(async (): Promise<boolean> => {
    try {
      const response = await AXIOS_INSTANCE.post<{
        access_token: string;
        refresh_token: string;
        expires_in: number;
      }>('/api/v1/auth/refresh', null, {
        withCredentials: true,
      });

      setAccessToken(response.data.access_token, response.data.expires_in);
      scheduleTokenRefresh(response.data.expires_in);
      return true;
    } catch {
      clearTokens();
      return false;
    }
  }, [scheduleTokenRefresh]);

  const logout = useCallback(async () => {
    clearRefreshTimeout();

    try {
      // Call logout endpoint to clear httpOnly cookie
      await AXIOS_INSTANCE.post('/api/v1/auth/logout', null, {
        withCredentials: true,
      });
    } catch {
      // Ignore errors, proceed with client-side cleanup
    }

    clearTokens();
    setUser(null);
    queryClient.clear();
    navigate({ to: '/login' });
  }, [navigate, queryClient, clearRefreshTimeout]);

  const refreshUser = useCallback(async () => {
    try {
      const userData = await getMeApiV1UsersMeGet();
      setUser(userData);
    } catch {
      // If refresh fails, user might be logged out
      await logout();
    }
  }, [logout]);

  // On mount: clean up legacy localStorage and try to restore session via refresh
  useEffect(() => {
    const initAuth = async () => {
      // Clean up legacy localStorage token (migration)
      localStorage.removeItem(LEGACY_AUTH_TOKEN_KEY);

      // Try to restore session from httpOnly cookie
      const success = await silentRefresh();
      if (success) {
        try {
          const userData = await getMeApiV1UsersMeGet();
          setUser(userData);
        } catch {
          // Token was refreshed but user fetch failed
          clearTokens();
        }
      }

      setIsLoading(false);
    };

    initAuth();

    // Cleanup on unmount
    return () => {
      clearRefreshTimeout();
    };
  }, [silentRefresh, clearRefreshTimeout]);

  const login = async (email: string, password: string) => {
    const response = await loginMutation.mutateAsync({
      data: { username: email, password },
    });

    // Store token in memory only
    setAccessToken(response.access_token, response.expires_in);
    scheduleTokenRefresh(response.expires_in);

    // Fetch user details after login
    const userData = await getMeApiV1UsersMeGet();
    setUser(userData);
  };

  const register = async (email: string, password: string) => {
    const response = await registerMutation.mutateAsync({
      data: { email, password },
    });

    // Store token in memory only
    setAccessToken(response.access_token, response.expires_in);
    scheduleTokenRefresh(response.expires_in);

    // Fetch user details after registration
    const userData = await getMeApiV1UsersMeGet();
    setUser(userData);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!getAccessToken() && !!user,
        isLoading,
        login,
        register,
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
