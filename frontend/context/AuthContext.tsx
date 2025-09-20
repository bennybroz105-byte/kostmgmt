'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { jwtDecode } from 'jwt-decode';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Check for token on initial load
    const token = localStorage.getItem('jwt_token');
    if (token) {
      const decoded = jwtDecode(token);
      // Here you would also fetch user details from an API
      // e.g., GET /users/me
      // For now, we'll rely on the JWT payload
      setUser({ token, ...decoded });
    }
  }, []);

  const login = (token) => {
    const decoded = jwtDecode(token);
    localStorage.setItem('jwt_token', token);
    setUser({ token, ...decoded });
  };

  const logout = () => {
    localStorage.removeItem('jwt_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
