// Authentication API Service
const API_BASE_URL = 'http://localhost:5000/api/auth';

class AuthService {
  /**
   * Register a new user
   */
  async register(userData) {
    try {
      const response = await fetch(`${API_BASE_URL}/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Registration failed');
      }

      return { success: true, data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Login user
   */
  async login(email, password) {
    try {
      const response = await fetch(`${API_BASE_URL}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Login failed');
      }

      // Store token in localStorage
      if (data.success && data.session) {
        localStorage.setItem('token', data.session.token);
        localStorage.setItem('user', JSON.stringify(data.session));
      }

      return { success: true, data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Logout user
   */
  async logout() {
    try {
      const token = this.getToken();
      
      if (token) {
        const response = await fetch(`${API_BASE_URL}/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        const data = await response.json();
      }

      // Clear local storage regardless of API response
      localStorage.removeItem('token');
      localStorage.removeItem('user');

      return { success: true };
    } catch (error) {
      // Clear local storage even if API call fails
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      return { success: true };
    }
  }

  /**
   * Validate current session
   */
  async validateSession() {
    try {
      const token = this.getToken();
      
      if (!token) {
        return { success: false, error: 'No token found' };
      }

      const response = await fetch(`${API_BASE_URL}/validate`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Session validation failed');
      }

      return { success: true, data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Get stored token
   */
  getToken() {
    return localStorage.getItem('token');
  }

  /**
   * Get stored user data
   */
  getUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    return !!this.getToken();
  }
}

export default new AuthService();
