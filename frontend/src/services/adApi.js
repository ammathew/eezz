const API_BASE_URL = '/api';

const getAuthHeaders = () => {
  const token = localStorage.getItem('accessToken');
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  };
};

export const adApi = {
  async generateAd(payload) {
    const response = await fetch(`${API_BASE_URL}/ads/generate/`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to generate ad');
    }
    return response.json();
  },

  async postAd(payload) {
    const response = await fetch(`${API_BASE_URL}/ads/post/`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to post ad');
    }
    return response.json();
  },

  async launchAd(payload) {
    const response = await fetch(`${API_BASE_URL}/ads/launch/`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to launch ad');
    }
    return response.json();
  },

  async getFacebookStatus() {
    const response = await fetch(`${API_BASE_URL}/facebook/status/`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      throw new Error('Failed to fetch Facebook status');
    }
    return response.json();
  },

  async getFacebookLoginUrl(redirectUri) {
    const params = new URLSearchParams();
    if (redirectUri) params.append('redirect_uri', redirectUri);
    const response = await fetch(`${API_BASE_URL}/facebook/login-url/?${params.toString()}`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to get Facebook login URL');
    }
    return response.json();
  },

  async connectFacebook(payload) {
    const response = await fetch(`${API_BASE_URL}/facebook/connect/`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to connect Facebook');
    }
    return response.json();
  },
};
