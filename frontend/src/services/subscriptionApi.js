const API_BASE_URL = '/api';

const getAuthHeaders = () => {
  const token = localStorage.getItem('accessToken');
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
  };
};

export const subscriptionApi = {
  // Get subscription status
  async getStatus() {
    const response = await fetch(`${API_BASE_URL}/subscription/status/`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      throw new Error('Failed to fetch subscription status');
    }
    return response.json();
  },

  // Create checkout session for new subscription
  async createCheckoutSession(successUrl, cancelUrl) {
    const response = await fetch(`${API_BASE_URL}/subscription/create-checkout/`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        success_url: successUrl,
        cancel_url: cancelUrl,
      }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to create checkout session');
    }
    return response.json();
  },

  // Create customer portal session for managing subscription
  async createPortalSession(returnUrl) {
    const response = await fetch(`${API_BASE_URL}/subscription/create-portal/`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        return_url: returnUrl,
      }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to create portal session');
    }
    return response.json();
  },
};
