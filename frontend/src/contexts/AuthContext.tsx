import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/router';
import { authAPI, userAPI } from '@/lib/api';

interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  role: string;
  wallet_address?: string;
  biometric_enrolled: boolean;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  loginBiometric: (username: string, biometricData: string) => Promise<void>;
  register: (data: any) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('access_token');
    if (token) {
      try {
        const response = await userAPI.getMe();
        setUser(response.data);
      } catch (error) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      }
    }
    setLoading(false);
  };

  const login = async (username: string, password: string) => {
    const response = await authAPI.login({ username, password });
    localStorage.setItem('access_token', response.data.access_token);
    localStorage.setItem('refresh_token', response.data.refresh_token);
    await refreshUser();
    router.push('/dashboard');
  };

  const loginBiometric = async (username: string, biometricData: string) => {
    const response = await authAPI.loginBiometric({ username, biometric_data: biometricData });
    localStorage.setItem('access_token', response.data.access_token);
    localStorage.setItem('refresh_token', response.data.refresh_token);
    await refreshUser();
    router.push('/dashboard');
  };

  const register = async (data: any) => {
    const response = await authAPI.register(data);
    localStorage.setItem('access_token', response.data.access_token);
    localStorage.setItem('refresh_token', response.data.refresh_token);
    await refreshUser();
    router.push('/dashboard');
  };

  const logout = async () => {
    const token = localStorage.getItem('access_token');
    if (token) {
      try {
        await authAPI.logout({ token });
      } catch (error) {
        console.error('Logout error:', error);
      }
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
    router.push('/login');
  };

  const refreshUser = async () => {
    try {
      const response = await userAPI.getMe();
      setUser(response.data);
    } catch (error) {
      console.error('Failed to refresh user:', error);
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, loginBiometric, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
