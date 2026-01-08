import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  CircularProgress,
  Alert
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import EmailIcon from '@mui/icons-material/Email';
import ReplyIcon from '@mui/icons-material/Reply';
import api from '../services/api';

function DreamBrain() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState({
    daily_insights: [],
    timeline: []
  });

  useEffect(() => {
    fetchDreamBrainData();
  }, []);

  const fetchDreamBrainData = async () => {
    try {
      setLoading(true);
      // Get access token from localStorage
      const accessToken = localStorage.getItem('accessToken');

      const response = await api.get('/api/dream-brain/data/', {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });
      setData(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching Dream Brain data:', err);
      setError('Failed to load Dream Brain data');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (isoString) => {
    if (!isoString) return 'N/A';
    const date = new Date(isoString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', overflow: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Your Dream Brain
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        View your daily insights, email responses, and dream journey timeline
      </Typography>

      {/* Daily Insights & Responses */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <EmailIcon /> Daily Insights & Your Responses
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          AI-generated insights sent to you via email and your replies
        </Typography>

        {data.daily_insights.length === 0 ? (
          <Alert severity="info">No daily insights sent yet. Check back tomorrow!</Alert>
        ) : (
          data.daily_insights.map((insight) => (
            <Accordion key={insight.id} sx={{ mb: 1 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box sx={{ flexGrow: 1 }}>
                  <Typography variant="subtitle1">{insight.subject}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Sent: {formatDate(insight.sent_at)}
                  </Typography>
                  {insight.responses && insight.responses.length > 0 && (
                    <Chip
                      icon={<ReplyIcon />}
                      label={`${insight.responses.length} ${insight.responses.length === 1 ? 'reply' : 'replies'}`}
                      size="small"
                      color="success"
                      sx={{ ml: 2 }}
                    />
                  )}
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Box>
                  <Typography variant="body2" sx={{ mb: 2, whiteSpace: 'pre-wrap' }}>
                    {insight.content}
                  </Typography>

                  {insight.responses && insight.responses.length > 0 && (
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      {insight.responses.map((response) => (
                        <Paper
                          key={response.id}
                          elevation={0}
                          sx={{
                            p: 2,
                            bgcolor: 'success.light',
                            borderLeft: '4px solid',
                            borderColor: 'success.main'
                          }}
                        >
                          <Typography variant="subtitle2" gutterBottom>
                            <ReplyIcon sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                            Your Response ({formatDate(response.received_at)})
                          </Typography>
                          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                            {response.content}
                          </Typography>
                        </Paper>
                      ))}
                    </Box>
                  )}
                </Box>
              </AccordionDetails>
            </Accordion>
          ))
        )}
      </Paper>

      {/* Timeline Events */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom>
          Your Dream Journey Timeline
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          A chronological view of your dreams and interactions
        </Typography>

        {data.timeline.length === 0 ? (
          <Alert severity="info">No timeline events yet. Start by sharing a dream!</Alert>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {data.timeline.map((event) => (
              <Paper key={event.id} elevation={1} sx={{ p: 2.5, bgcolor: 'background.paper', border: '1px solid', borderColor: 'divider' }}>
                <Box sx={{ display: 'flex', gap: 1, mb: 1.5, flexWrap: 'wrap', alignItems: 'center' }}>
                  <Chip
                    label={event.kind}
                    size="small"
                    color={
                      event.kind === 'Dream' ? 'primary' :
                      event.kind === 'Chat Summary' ? 'secondary' :
                      'success'
                    }
                    variant="outlined"
                  />
                  <Typography variant="caption" color="text.secondary">
                    {formatDate(event.at)}
                  </Typography>
                </Box>
                {(event.data.dream_summary || event.data.summary) && (
                  <Typography variant="body2" sx={{ color: 'text.primary', lineHeight: 1.6 }}>
                    {event.data.dream_summary || event.data.summary}
                  </Typography>
                )}
              </Paper>
            ))}
          </Box>
        )}
      </Paper>
    </Box>
  );
}

export default DreamBrain;
