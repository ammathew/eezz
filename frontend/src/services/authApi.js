const API_BASE_URL = '/api/auth';

export const authApi = {
  // Register new user
  async register(email, password1, password2) {
    const response = await fetch(`${API_BASE_URL}/registration/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password1, password2 }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(JSON.stringify(error));
    }
    return response.json();
  },

  // Login user
  async login(email, password) {
    const response = await fetch(`${API_BASE_URL}/login/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(JSON.stringify(error));
    }
    return response.json();
  },

  // Logout user
  async logout(accessToken) {
    const response = await fetch(`${API_BASE_URL}/logout/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to logout');
    }
  },

  // Get current user
  async getCurrentUser(accessToken) {
    const response = await fetch(`${API_BASE_URL}/user/`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch user');
    }
    return response.json();
  },

  // Refresh token
  async refreshToken(refreshToken) {
    const response = await fetch(`${API_BASE_URL}/token/refresh/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh: refreshToken }),
    });

    if (!response.ok) {
      throw new Error('Failed to refresh token');
    }
    return response.json();
  },

  // Admin: Get all users
  async getAllUsers(accessToken) {
    const headers = {
      'Authorization': `Bearer ${accessToken}`,
    };

    // Add hijack token if in hijack mode
    const hijackToken = sessionStorage.getItem('hijackToken');
    if (hijackToken) {
      headers['X-Hijack-Token'] = hijackToken;
    }

    const response = await fetch('/api/admin/users/', {
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to fetch users');
    }
    return response.json();
  },

  // Admin: Login as user
  async loginAsUser(userId, accessToken) {
    const response = await fetch(`${API_BASE_URL}/login-as-user/${userId}/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to login as user');
    }
    return response.json();
  },

  // Admin: Start hijack session (new secure method)
  async startHijackSession(userId, accessToken) {
    const headers = {
      'Authorization': `Bearer ${accessToken}`,
    };

    // Add hijack token if already in hijack mode (switching users)
    const hijackToken = sessionStorage.getItem('hijackToken');
    if (hijackToken) {
      headers['X-Hijack-Token'] = hijackToken;
    }

    const response = await fetch(`/api/admin/hijack/start/${userId}/`, {
      method: 'POST',
      headers,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to start hijack session');
    }
    return response.json();
  },

  // Admin: End hijack session
  async endHijackSession(hijackToken, accessToken) {
    const response = await fetch(`/api/admin/hijack/end/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
        'X-Hijack-Token': hijackToken,
      },
      body: JSON.stringify({ hijack_token: hijackToken }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to end hijack session');
    }
    return response.json();
  },

  // Generic GET request with auth
  async get(url, accessToken) {
    const headers = {
      'Authorization': `Bearer ${accessToken}`,
    };

    // Add hijack token if in hijack mode
    const hijackToken = sessionStorage.getItem('hijackToken');
    if (hijackToken) {
      headers['X-Hijack-Token'] = hijackToken;
    }

    const response = await fetch(url, {
      headers,
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch ${url}`);
    }
    return response;
  },
};
