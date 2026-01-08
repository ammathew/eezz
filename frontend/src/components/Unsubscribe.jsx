import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Box, Container, Typography, Button, CircularProgress, Paper } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';

function Unsubscribe() {
  const { token } = useParams();
  const [status, setStatus] = useState('loading'); // loading, success, error, already_unsubscribed
  const [email, setEmail] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    // First, get the subscription status
    fetch(`/api/public/unsubscribe/${token}/`)
      .then(res => res.json())
      .then(data => {
        setEmail(data.email);
        if (!data.is_subscribed) {
          setStatus('already_unsubscribed');
        } else {
          // If subscribed, automatically unsubscribe them
          handleUnsubscribe();
        }
      })
      .catch(err => {
        console.error('Error checking subscription:', err);
        setErrorMessage('Invalid unsubscribe link. This link may be expired or incorrect.');
        setStatus('error');
      });
  }, [token]);

  const handleUnsubscribe = () => {
    fetch(`/api/public/unsubscribe/${token}/`, {
      method: 'POST',
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setStatus('success');
        } else {
          setStatus('error');
          setErrorMessage(data.message || 'Failed to unsubscribe');
        }
      })
      .catch(err => {
        console.error('Error unsubscribing:', err);
        setErrorMessage('An error occurred while unsubscribing. Please try again.');
        setStatus('error');
      });
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        py: 4,
      }}
    >
      <Container maxWidth="sm">
        <Paper
          elevation={3}
          sx={{
            p: 4,
            textAlign: 'center',
            borderRadius: 2,
          }}
        >
          {status === 'loading' && (
            <>
              <CircularProgress sx={{ mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Processing your request...
              </Typography>
            </>
          )}

          {status === 'success' && (
            <>
              <CheckCircleIcon sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
              <Typography variant="h4" gutterBottom>
                Successfully Unsubscribed
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                {email && `${email} has been `}unsubscribed from follow-up emails. You will no longer receive dream insights from us.
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Changed your mind? You can always sign up for a free Unravel account to track your dreams and get personalized insights.
              </Typography>
              <Button
                variant="contained"
                href="https://app.unravel.so/signup"
                sx={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white',
                  px: 4,
                  py: 1.5,
                }}
              >
                Sign Up for Free
              </Button>
            </>
          )}

          {status === 'already_unsubscribed' && (
            <>
              <CheckCircleIcon sx={{ fontSize: 64, color: 'info.main', mb: 2 }} />
              <Typography variant="h4" gutterBottom>
                Already Unsubscribed
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                {email && `${email} is `}already unsubscribed from follow-up emails.
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Want to track your dreams? Sign up for a free Unravel account.
              </Typography>
              <Button
                variant="contained"
                href="https://app.unravel.so/signup"
                sx={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white',
                  px: 4,
                  py: 1.5,
                }}
              >
                Sign Up for Free
              </Button>
            </>
          )}

          {status === 'error' && (
            <>
              <ErrorIcon sx={{ fontSize: 64, color: 'error.main', mb: 2 }} />
              <Typography variant="h4" gutterBottom>
                Oops!
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                {errorMessage}
              </Typography>
              <Button
                variant="outlined"
                href="https://app.unravel.so"
                sx={{ mt: 2 }}
              >
                Go to Unravel
              </Button>
            </>
          )}
        </Paper>
      </Container>
    </Box>
  );
}

export default Unsubscribe;
