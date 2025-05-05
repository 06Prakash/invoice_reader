import { createContext, useState } from 'react';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem('jwt_token') || '');
  const [userRole, setUserRole] = useState(
    localStorage.getItem('special_admin') === 'true' ? 'special_admin' : 'user'
  );

  const login = (tokenData) => {
    localStorage.setItem('jwt_token', tokenData.access_token);
    localStorage.setItem('refresh_token', tokenData.refresh_token);
    localStorage.setItem('special_admin', tokenData.special_admin);
    setToken(tokenData.access_token);
    setUserRole(tokenData.special_admin ? 'special_admin' : 'user');
  };

  const logout = () => {
    localStorage.removeItem('jwt_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('special_admin');
    setToken('');
    setUserRole('user');
  };

  return (
    <AuthContext.Provider value={{ token, userRole, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};