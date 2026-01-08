import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { chatApi } from '../services/chatApi';
import './Chat.css';
import CircularProgress from '@mui/material/CircularProgress';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import SendIcon from '@mui/icons-material/Send';

// Global flags to prevent duplicate operations across component remounts (StrictMode)
let isInitializing = false;
let hasInitialized = false;

function Chat() {
  const [conversations, setConversations] = useState([]);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load conversations on mount
  useEffect(() => {
    if (hasInitialized || isInitializing) return;

    isInitializing = true;
    hasInitialized = true;

    const initializeChat = async () => {
      await loadConversations();
      isInitializing = false;
    };
    initializeChat();
  }, []);

  // Auto-focus input when conversation changes
  useEffect(() => {
    if (currentConversation && inputRef.current) {
      inputRef.current.focus();
    }
  }, [currentConversation]);

  const loadConversations = async () => {
    try {
      const data = await chatApi.getConversations();
      // Handle paginated response - conversations are in data.results
      const conversationsList = data.results || (Array.isArray(data) ? data : []);

      // Deduplicate conversations by ID (defensive programming)
      const uniqueConversations = conversationsList.reduce((acc, conv) => {
        if (!acc.find(c => c.id === conv.id)) {
          acc.push(conv);
        }
        return acc;
      }, []);

      setConversations(uniqueConversations);
    } catch (err) {
      console.error('Failed to load conversations:', err);
      setConversations([]);
    }
  };

  const loadConversation = async (id) => {
    try {
      setLoading(true);
      const data = await chatApi.getConversation(id);
      setCurrentConversation(data);
      setMessages(data.messages || []);
      setError(null);
    } catch (err) {
      setError('Failed to load conversation');
      console.error('Error loading conversation:', err);
    } finally {
      setLoading(false);
    }
  };

  const startNewChat = () => {
    // Clear current conversation and messages
    // Conversation will be created when user sends first message
    setCurrentConversation(null);
    setMessages([]);
    setError(null);
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();

    if (!inputMessage.trim()) return;

    const messageText = inputMessage.trim();
    setInputMessage('');
    setLoading(true);
    setError(null);

    try {
      let conversationToUse = currentConversation;

      // Create a new conversation if one doesn't exist
      if (!conversationToUse) {
        conversationToUse = await chatApi.createConversation();
        setCurrentConversation(conversationToUse);
      }

      const response = await chatApi.sendMessage(
        conversationToUse.id,
        messageText
      );

      // Add both user and assistant messages to the conversation
      setMessages([
        ...messages,
        response.user_message,
        response.assistant_message,
      ]);

      // Update current conversation with new title if provided
      if (response.conversation) {
        setCurrentConversation({
          ...conversationToUse,
          title: response.conversation.title,
          updated_at: response.conversation.updated_at
        });
      }

      // Reload conversations to update the list (includes updated title)
      await loadConversations();
    } catch (err) {
      setError(err.message || 'Failed to send message');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteConversation = async (id) => {
    if (!confirm('Are you sure you want to delete this conversation?')) {
      return;
    }

    try {
      await chatApi.deleteConversation(id);
      setConversations(conversations.filter((c) => c.id !== id));
      if (currentConversation?.id === id) {
        setCurrentConversation(null);
        setMessages([]);
      }
    } catch (err) {
      setError('Failed to delete conversation');
      console.error(err);
    }
  };

  return (
    <div className="chat-container">
      {/* Sidebar */}
      <div className="chat-sidebar">
        <div className="sidebar-header">
          <h2>Conversations</h2>
          <button onClick={startNewChat} className="new-chat-btn" disabled={loading}>
            + New Chat
          </button>
        </div>
        <div className="conversations-list">
          {!Array.isArray(conversations) || conversations.length === 0 ? (
            <p className="no-conversations">No conversations yet</p>
          ) : (
            conversations.map((conv) => (
              <div
                key={conv.id}
                className={`conversation-item ${
                  currentConversation?.id === conv.id ? 'active' : ''
                }`}
                onClick={() => loadConversation(conv.id)}
              >
                <div className="conversation-title">{conv.title}</div>
                <div className="conversation-meta">
                  {conv.message_count} messages
                </div>
                <button
                  className="delete-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteConversation(conv.id);
                  }}
                  aria-label="Delete conversation"
                >
                  <DeleteOutlineIcon fontSize="small" />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="chat-main">
        {/* Messages */}
        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="no-messages">
              <div style={{ fontSize: '3rem', marginBottom: '20px' }}>💬</div>
              <p style={{ fontSize: '1.2rem', fontWeight: '500', color: '#374151' }}>
                Ready to chat with Unravel Dream Interpretation App!
              </p>
              <p style={{ fontSize: '1rem', color: '#9ca3af' }}>
                Type your dream below to get started
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`message ${message.role}`}
              >
                <div className="message-content">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
                <div className="message-time">
                  {new Date(message.created_at).toLocaleTimeString()}
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Form - Always visible */}
        <form onSubmit={handleSendMessage} className="message-form">
          {error && <div className="error-message">{error}</div>}
          <div className="input-container">
            <input
              ref={inputRef}
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Type your dream here..."
              disabled={loading}
              className="message-input"
            />
            <button
              type="submit"
              disabled={loading || !inputMessage.trim()}
              className="send-btn"
              aria-label="Send message"
            >
              {loading ? (
                <CircularProgress size={20} style={{ color: '#f5f1e8' }} />
              ) : (
                <SendIcon />
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default Chat;
