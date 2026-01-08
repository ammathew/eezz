import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { chatApi } from '../services/chatApi';
import { subscriptionApi } from '../services/subscriptionApi';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Send as SendIcon,
} from '@mui/icons-material';

function Chat({ currentConversation, onConversationUpdate, onConversationsUpdate }) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [canUseService, setCanUseService] = useState(true);
  const [isSendingMessage, setIsSendingMessage] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Check subscription status on mount
  useEffect(() => {
    const checkSubscription = async () => {
      try {
        const status = await subscriptionApi.getStatus();
        setCanUseService(status.can_use_service);
      } catch (err) {
        console.error('Failed to check subscription:', err);
      }
    };
    checkSubscription();
  }, []);

  // Load messages when currentConversation changes
  useEffect(() => {
    // Skip loading if we're currently sending a message
    if (isSendingMessage) return;

    const loadConversation = async () => {
      if (currentConversation?.id) {
        try {
          setLoading(true);
          const data = await chatApi.getConversation(currentConversation.id);
          setMessages(data.messages || []);
          setError(null);
        } catch (err) {
          setError('Failed to load conversation');
          console.error('Error loading conversation:', err);
        } finally {
          setLoading(false);
        }
      } else {
        // New conversation - clear messages
        setMessages([]);
      }
    };
    loadConversation();
  }, [currentConversation, isSendingMessage]);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, [currentConversation]);

  const handleSendMessage = async (e) => {
    e.preventDefault();

    if (!inputMessage.trim()) return;

    const messageText = inputMessage.trim();
    setInputMessage('');
    setLoading(true);
    setIsSendingMessage(true);
    setError(null);

    // Add user message immediately
    const tempUserMessage = {
      role: 'user',
      content: messageText,
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, tempUserMessage]);

    try {
      let conversationToUse = currentConversation;

      // Create a new conversation if one doesn't exist
      if (!conversationToUse) {
        conversationToUse = await chatApi.createConversation();
        onConversationUpdate(conversationToUse);
      }

      const response = await chatApi.sendMessage(
        conversationToUse.id,
        messageText
      );

      // Replace temp user message with real messages from server
      setMessages(prev => {
        const withoutTemp = prev.filter(m => m !== tempUserMessage);
        return [
          ...withoutTemp,
          response.user_message,
          response.assistant_message,
        ];
      });

      // Notify parent to reload conversations
      onConversationsUpdate();
    } catch (err) {
      // Remove temp message on error
      setMessages(prev => prev.filter(m => m !== tempUserMessage));
      setError(err.message || 'Failed to send message');
      console.error(err);
    } finally {
      setLoading(false);
      setIsSendingMessage(false);
    }
  };

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        width: '100%',
        overflow: 'hidden',
        position: 'relative',
      }}
    >
      {/* Trial expired banner - only show if trial expired */}
      {!canUseService && (
        <Box sx={{ p: 2 }}>
          <Alert severity="error">
            Your trial has ended. Please visit your profile to subscribe and continue using Unravel.
          </Alert>
        </Box>
      )}

      {/* Messages area */}
      <Box
        sx={{
          flex: 1,
          overflow: 'auto',
          display: 'flex',
          justifyContent: 'center',
          bgcolor: 'background.default',
          minHeight: 0,
        }}
      >
        <Box sx={{
          maxWidth: 900,
          width: '100%',
          p: 3,
          mx: 'auto',
          boxSizing: 'border-box',
        }}>
          {messages.length === 0 ? (
            <Box
              sx={{
                display: 'flex',
                alignItems: 'flex-start',
                justifyContent: 'flex-start',
                minHeight: '60vh',
                flexDirection: 'column',
                gap: 2,
              }}
            >
              <Typography variant="h4" color="text.secondary">
                Welcome to Unravel
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Start chatting with dream interpretation AI
              </Typography>
              <Typography variant="body2" color="text.disabled">
                Type your message below to begin
              </Typography>
            </Box>
          ) : (
            messages.map((message) => (
              <Paper
                key={message.id}
                elevation={1}
                sx={{
                  p: 2,
                  mb: 2,
                  maxWidth: '80%',
                  ml: message.role === 'user' ? 'auto' : 0,
                  bgcolor: message.role === 'user'
                    ? 'primary.main'
                    : 'background.paper',
                  color: message.role === 'user' ? 'white' : 'text.primary',
                }}
              >
                <Box
                  sx={{
                    textAlign: 'left',
                    '& p': { m: 0, mb: 1, textAlign: 'left' },
                    '& p:last-child': { mb: 0 },
                    '& pre': {
                      bgcolor: message.role === 'user'
                        ? 'rgba(255,255,255,0.1)'
                        : 'rgba(0,0,0,0.05)',
                      p: 1.5,
                      borderRadius: 1,
                      overflow: 'auto',
                      textAlign: 'left',
                    },
                    '& code': {
                      bgcolor: message.role === 'user'
                        ? 'rgba(255,255,255,0.2)'
                        : 'rgba(0,0,0,0.05)',
                      px: 0.5,
                      py: 0.25,
                      borderRadius: 0.5,
                    },
                    '& ul, & ol': { textAlign: 'left', pl: 3 },
                    '& li': { textAlign: 'left' },
                  }}
                >
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </Box>
                <Typography variant="caption" sx={{ display: 'block', mt: 1, opacity: 0.7, textAlign: 'left' }}>
                  {new Date(message.created_at).toLocaleTimeString()}
                </Typography>
              </Paper>
            ))
          )}
          <div ref={messagesEndRef} />
        </Box>
      </Box>

      {/* Input area */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          borderTop: 1,
          borderColor: 'divider',
          flexShrink: 0,
          bgcolor: 'background.paper',
        }}
      >
        <Paper
          component="form"
          onSubmit={handleSendMessage}
          elevation={0}
          sx={{
            p: 2,
            display: 'flex',
            gap: 1,
            alignItems: 'flex-end',
            width: '100%',
            maxWidth: 900,
            bgcolor: 'background.paper',
          }}
        >
          {error && (
            <Alert severity="error" sx={{ mb: 2, width: '100%' }}>
              {error}
            </Alert>
          )}
          <TextField
            fullWidth
            multiline
            maxRows={4}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage(e);
              }
            }}
            placeholder={canUseService ? "Type your message here..." : "Subscribe to continue chatting..."}
            disabled={loading || !canUseService}
            inputRef={inputRef}
            variant="outlined"
          />
          <IconButton
            type="submit"
            color="primary"
            disabled={loading || !inputMessage.trim() || !canUseService}
            size="large"
          >
            {loading ? <CircularProgress size={24} /> : <SendIcon />}
          </IconButton>
        </Paper>
      </Box>
    </Box>
  );
}

export default Chat;
