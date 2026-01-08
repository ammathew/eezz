import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Alert,
  Container,
  CircularProgress,
} from '@mui/material';
import EmailIcon from '@mui/icons-material/Email';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

function EmailCapture() {
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();
  const submissionId = searchParams.get('id');

  useEffect(() => {
    // Redirect if no submission ID
    if (!submissionId) {
      navigate('/interpret');
    }
  }, [submissionId, navigate]);

  const validateEmail = (email) => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validation
    if (!email.trim()) {
      setError('Please enter your email address');
      return;
    }

    if (!validateEmail(email)) {
      setError('Please enter a valid email address');
      return;
    }

    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/public/submit-email/`, {
        submission_id: submissionId,
        email: email.trim(),
      });

      if (response.data.success) {
        setSuccess(true);

        // Track conversion event
        if (window.gtag) {
          window.gtag('event', 'conversion', {
            'send_to': 'AW-17817195887/CHscCMvGhdQbEO-q869C',
            'value': 1.0,
            'currency': 'USD'
          });
        }
      }
    } catch (err) {
      console.error('Failed to submit email:', err);
      setError(
        err.response?.data?.error ||
        err.response?.data?.email?.[0] ||
        'Failed to send interpretation. Please try again.'
      );
      setLoading(false);
    }
  };

  if (success) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          p: 2,
        }}
      >
        <Container maxWidth="sm">
          <Paper
            elevation={6}
            sx={{
              p: { xs: 3, sm: 5 },
              bgcolor: 'background.paper',
              borderRadius: 2,
              textAlign: 'center',
            }}
          >
            <CheckCircleIcon
              sx={{
                fontSize: 80,
                color: 'success.main',
                mb: 3,
              }}
            />
            <Typography
              variant="h4"
              sx={{
                mb: 2,
                fontWeight: 600,
                color: 'success.main',
              }}
            >
              Check Your Email!
            </Typography>
            <Typography variant="h6" color="text.secondary" sx={{ mb: 3 }}>
              We've sent your dream interpretation to:
            </Typography>
            <Typography
              variant="h6"
              sx={{
                mb: 4,
                fontWeight: 600,
                color: 'primary.main',
              }}
            >
              {email}
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
              We're generating your personalized interpretation right now.
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
              Your dream interpretation will arrive within the next few minutes. Don't forget to check your spam folder if you don't see it.
            </Typography>

            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
              <Button
                variant="contained"
                size="large"
                onClick={() => navigate('/signup', { state: { email } })}
                sx={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #5568d3 0%, #6a4091 100%)',
                  },
                }}
              >
                Create Free Account
              </Button>
              <Button
                variant="outlined"
                size="large"
                onClick={() => navigate('/interpret')}
              >
                Interpret Another Dream
              </Button>
            </Box>
          </Paper>
        </Container>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 2,
      }}
    >
      <Container maxWidth="sm">
        <Paper
          elevation={6}
          sx={{
            p: { xs: 3, sm: 5 },
            bgcolor: 'background.paper',
            borderRadius: 2,
          }}
        >
          {/* Header */}
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <EmailIcon
              sx={{
                fontSize: 60,
                color: 'primary.main',
                mb: 2,
              }}
            />
            <Typography
              variant="h4"
              sx={{
                mb: 2,
                fontWeight: 600,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              Almost There!
            </Typography>
            <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
              Enter your email to receive your interpretation
            </Typography>
            <Typography variant="body2" color="text.secondary">
              We'll send your personalized dream analysis straight to your inbox
            </Typography>
          </Box>

          {/* Form */}
          <Box component="form" onSubmit={handleSubmit}>
            {error && (
              <Alert severity="error" sx={{ mb: 3 }}>
                {error}
              </Alert>
            )}

            <TextField
              fullWidth
              type="email"
              label="Email Address"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
              autoFocus
              sx={{ mb: 3 }}
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              disabled={loading || !email.trim()}
              sx={{
                py: 1.5,
                fontSize: '1.1rem',
                fontWeight: 600,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #5568d3 0%, #6a4091 100%)',
                },
              }}
            >
              {loading ? (
                <>
                  <CircularProgress size={24} color="inherit" sx={{ mr: 1 }} />
                  Processing Your Dream...
                </>
              ) : (
                'Send My Interpretation'
              )}
            </Button>
          </Box>

          {/* Footer */}
          <Box sx={{ mt: 4, pt: 3, borderTop: '1px solid', borderColor: 'divider' }}>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textAlign: 'center' }}>
              By continuing, you agree to receive email from Unravel. Your email will not be shared. Unsubscribe any time.
            </Typography>
          </Box>
        </Paper>
      </Container>
    </Box>
  );
}

export default EmailCapture;
