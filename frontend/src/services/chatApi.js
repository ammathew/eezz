const API_BASE_URL = '/api';

const getAuthHeaders = () => {
  const token = localStorage.getItem('accessToken');
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
  };
};

export const chatApi = {
  // Get all conversations
  async getConversations() {
    const response = await fetch(`${API_BASE_URL}/conversations/`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      throw new Error('Failed to fetch conversations');
    }
    return response.json();
  },

  // Get a single conversation with messages
  async getConversation(id) {
    const response = await fetch(`${API_BASE_URL}/conversations/${id}/`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      throw new Error('Failed to fetch conversation');
    }
    return response.json();
  },

  // Create a new conversation
  async createConversation(title = 'New Conversation') {
    const response = await fetch(`${API_BASE_URL}/conversations/`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ title }),
    });
    if (!response.ok) {
      throw new Error('Failed to create conversation');
    }
    return response.json();
  },

  // Send a message in a conversation
  async sendMessage(conversationId, content) {
    const response = await fetch(
      `${API_BASE_URL}/conversations/${conversationId}/send_message/`,
      {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ content }),
      }
    );
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to send message');
    }
    return response.json();
  },

  // Delete a conversation
  async deleteConversation(id) {
    const response = await fetch(`${API_BASE_URL}/conversations/${id}/`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      throw new Error('Failed to delete conversation');
    }
  },

  // Get conversations by date range for calendar
  async getConversationsByDate(startDate, endDate) {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const response = await fetch(
      `${API_BASE_URL}/conversations/by_date/?${params.toString()}`,
      {
        headers: getAuthHeaders(),
      }
    );
    if (!response.ok) {
      throw new Error('Failed to fetch calendar data');
    }
    return response.json();
  },
};
