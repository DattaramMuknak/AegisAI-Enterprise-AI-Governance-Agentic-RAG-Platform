import { createContext, useContext, useState, useCallback } from 'react';
import { authAPI } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('aegis_token'));
  const [role, setRole]   = useState(() => localStorage.getItem('aegis_role') || 'viewer');

  const login = useCallback(async (email, password) => {
    const { data } = await authAPI.login(email, password);
    localStorage.setItem('aegis_token', data.access_token);
    localStorage.setItem('aegis_role', data.role);
    setToken(data.access_token);
    setRole(data.role);
    return data;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('aegis_token');
    localStorage.removeItem('aegis_role');
    setToken(null);
    setRole('viewer');
  }, []);

  return (
    <AuthContext.Provider value={{ token, role, isAuth: !!token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
