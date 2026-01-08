import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
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
import DreamIcon from '@mui/icons-material/Bedtime';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

function PublicDreamForm() {
  const [dreamText, setDreamText] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validation
    if (!dreamText.trim()) {
      setError('Please describe your dream');
      return;
    }

    if (dreamText.trim().length < 2) {
      setError('Please provide more details about your dream (at least 2 characters)');
      return;
    }

    if (dreamText.length > 5000) {
      setError('Dream description is too long. Please keep it under 5000 characters.');
      return;
    }

    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/public/submit-dream/`, {
        dream_text: dreamText.trim(),
      });

      // Navigate to email capture page with submission ID
      navigate(`/interpret/email?id=${response.data.submission_id}`);
    } catch (err) {
      console.error('Failed to submit dream:', err);
      setError(
        err.response?.data?.error ||
        err.response?.data?.dream_text?.[0] ||
        'Failed to submit your dream. Please try again.'
      );
      setLoading(false);
    }
  };

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
      <Container maxWidth="md">
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
            <DreamIcon
              sx={{
                fontSize: 60,
                color: 'primary.main',
                mb: 2,
              }}
            />
            <Typography
              variant="h3"
              sx={{
                mb: 2,
                fontWeight: 600,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              Interpret Your Dream
            </Typography>
            <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
               Share your dream and get an interpretation in less than a minute
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Utilizes AI and a symbol dictionary trusted by people with decades of experience interpreting their own dreams.
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
              multiline
              rows={8}
              label="Describe your dream"
              placeholder="Last night, I dreamed about..."
              value={dreamText}
              onChange={(e) => setDreamText(e.target.value)}
              disabled={loading}
              sx={{ mb: 3 }}
              helperText={`${dreamText.length}/5000 characters`}
              inputProps={{
                maxLength: 5000,
              }}
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              disabled={loading || !dreamText.trim()}
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
                  Submitting...
                </>
              ) : (
                'Get My Interpretation'
              )}
            </Button>
          </Box>

          {/* Footer */}
        </Paper>
      </Container>
    </Box>
  );
}

export default PublicDreamForm;
