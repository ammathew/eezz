import { createContext, useState, useContext, useEffect } from 'react';
import { authApi } from '../services/authApi';

const AuthContext = createContext();

export { AuthContext };

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [accessToken, setAccessToken] = useState(
    localStorage.getItem('accessToken')
  );
  const [refreshToken, setRefreshToken] = useState(
    localStorage.getItem('refreshToken')
  );

  // Load user on mount if token exists
  useEffect(() => {
    const loadUser = async () => {
      if (accessToken) {
        try {
          const userData = await authApi.getCurrentUser(accessToken);
          setUser(userData);
        } catch (error) {
          console.error('Failed to load user:', error);
          // Token might be expired, try to refresh
          if (refreshToken) {
            try {
              const tokens = await authApi.refreshToken(refreshToken);
              setAccessToken(tokens.access);
              localStorage.setItem('accessToken', tokens.access);
              const userData = await authApi.getCurrentUser(tokens.access);
              setUser(userData);
            } catch (refreshError) {
              // Refresh failed, clear everything
              logout();
            }
          } else {
            logout();
          }
        }
      }
      setLoading(false);
    };

    loadUser();
  }, []);

  const login = async (email, password) => {
    try {
      const response = await authApi.login(email, password);
      const { access, refresh, user: userData } = response;

      setAccessToken(access);
      setRefreshToken(refresh);
      setUser(userData);

      localStorage.setItem('accessToken', access);
      localStorage.setItem('refreshToken', refresh);

      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      let errorMessage = 'Login failed';
      try {
        const errorData = JSON.parse(error.message);
        errorMessage =
          errorData.non_field_errors?.[0] ||
          errorData.detail ||
          'Invalid credentials';
      } catch (e) {
        errorMessage = error.message;
      }
      return { success: false, error: errorMessage };
    }
  };

  const register = async (email, password1, password2) => {
    try {
      const response = await authApi.register(email, password1, password2);
      const { access, refresh, user: userData } = response;

      setAccessToken(access);
      setRefreshToken(refresh);
      setUser(userData);

      localStorage.setItem('accessToken', access);
      localStorage.setItem('refreshToken', refresh);

      return { success: true };
    } catch (error) {
      console.error('Registration error:', error);
      let errorMessage = 'Registration failed';
      try {
        const errorData = JSON.parse(error.message);
        errorMessage =
          errorData.email?.[0] ||
          errorData.password1?.[0] ||
          errorData.non_field_errors?.[0] ||
          'Registration failed';
      } catch (e) {
        errorMessage = error.message;
      }
      return { success: false, error: errorMessage };
    }
  };

  const logout = async () => {
    try {
      if (accessToken) {
        await authApi.logout(accessToken);
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      setAccessToken(null);
      setRefreshToken(null);
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('originalAdminUser'); // Clear old hijack mode (deprecated)
      sessionStorage.removeItem('hijackToken'); // Clear hijack session
      sessionStorage.removeItem('adminEmail');
      sessionStorage.removeItem('hijackExpiresAt');
    }
  };

  const value = {
    user,
    setUser,
    accessToken,
    setAccessToken,
    refreshToken,
    setRefreshToken,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
