import { useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Typography, Paper, Avatar, Grid, Button, Alert, CircularProgress, Chip, FormControl, Select, MenuItem, InputLabel } from '@mui/material';
import { AuthContext } from '../context/AuthContext';
import { subscriptionApi } from '../services/subscriptionApi';
import api from '../services/api';

function UserProfile() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [emailFrequency, setEmailFrequency] = useState('daily');
  const [emailChoices, setEmailChoices] = useState([]);
  const [emailPrefLoading, setEmailPrefLoading] = useState(true);
  const [emailPrefSaving, setEmailPrefSaving] = useState(false);
  const [emailPrefMessage, setEmailPrefMessage] = useState(null);

  useEffect(() => {
    loadSubscriptionStatus();
    loadEmailPreferences();
  }, []);

  const loadSubscriptionStatus = async () => {
    try {
      const status = await subscriptionApi.getStatus();
      setSubscriptionStatus(status);
    } catch (err) {
      console.error('Failed to load subscription status:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadEmailPreferences = async () => {
    try {
      const accessToken = localStorage.getItem('accessToken');
      const response = await api.get('/api/preferences/email/', {
        headers: { 'Authorization': `Bearer ${accessToken}` }
      });
      setEmailFrequency(response.data.email_frequency);
      setEmailChoices(response.data.choices);
    } catch (err) {
      console.error('Failed to load email preferences:', err);
    } finally {
      setEmailPrefLoading(false);
    }
  };

  const handleEmailFrequencyChange = async (event) => {
    const newFrequency = event.target.value;
    setEmailPrefSaving(true);
    setEmailPrefMessage(null);

    try {
      const accessToken = localStorage.getItem('accessToken');
      await api.post('/api/preferences/email/update/',
        { email_frequency: newFrequency },
        { headers: { 'Authorization': `Bearer ${accessToken}` } }
      );
      setEmailFrequency(newFrequency);
      setEmailPrefMessage({ type: 'success', text: 'Email preferences updated successfully!' });
      setTimeout(() => setEmailPrefMessage(null), 3000);
    } catch (err) {
      console.error('Failed to update email preferences:', err);
      setEmailPrefMessage({ type: 'error', text: 'Failed to update email preferences' });
    } finally {
      setEmailPrefSaving(false);
    }
  };

  const handleSubscribe = async () => {
    setActionLoading(true);
    try {
      const { url } = await subscriptionApi.createCheckoutSession(
        `${window.location.origin}/profile`,
        `${window.location.origin}/profile`
      );
      window.location.href = url;
    } catch (err) {
      console.error('Failed to create checkout session:', err);
      setActionLoading(false);
    }
  };

  const handleManageSubscription = async () => {
    setActionLoading(true);
    try {
      const { url } = await subscriptionApi.createPortalSession(
        window.location.href
      );
      window.location.href = url;
    } catch (err) {
      console.error('Failed to create portal session:', err);
      setActionLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <Box sx={{ p: 3, pb: 6, height: '100%', overflow: 'auto' }}>
      <Typography variant="h4" gutterBottom>
        User Profile
      </Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <Avatar
              src={user?.picture || undefined}
              sx={{
                width: 120,
                height: 120,
                margin: '0 auto',
                bgcolor: 'primary.main',
                fontSize: '3rem'
              }}
            >
              {!user?.picture && (user?.first_name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || 'U')}
            </Avatar>
            <Typography variant="h5" sx={{ mt: 2 }}>
              {user?.first_name && user?.last_name
                ? `${user.first_name} ${user.last_name}`
                : user?.first_name || user?.email || 'User'}
            </Typography>
            {user?.first_name && user?.email && (
              <Typography variant="body2" color="text.secondary">
                {user.email}
              </Typography>
            )}
            <Button
              variant="outlined"
              color="error"
              sx={{ mt: 2 }}
              onClick={handleLogout}
            >
              Logout
            </Button>
          </Paper>
        </Grid>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Account Information
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Typography variant="body1"><strong>Username:</strong> {user?.username || 'N/A'}</Typography>
              <Typography variant="body1" sx={{ mt: 1 }}><strong>Email:</strong> {user?.email || 'N/A'}</Typography>
              <Typography variant="body1" sx={{ mt: 1 }}><strong>Account Type:</strong> Standard</Typography>
            </Box>
          </Paper>
          <Paper sx={{ p: 3, mt: 3 }}>
            <Typography variant="h6" gutterBottom>
              Subscription & Billing
            </Typography>
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
              </Box>
            ) : subscriptionStatus ? (
              <Box sx={{ mt: 2 }}>
                {/* Subscription Status */}
                <Box sx={{ mb: 3 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Status
                  </Typography>
                  {subscriptionStatus.has_subscription ? (
                    <Chip label="Active Subscription" color="success" />
                  ) : subscriptionStatus.is_trial_active ? (
                    <Chip label="Free Trial" color="info" />
                  ) : (
                    <Chip label="Trial Expired" color="error" />
                  )}
                </Box>

                {/* Trial Information */}
                {!subscriptionStatus.has_subscription && subscriptionStatus.trial_ends_at && (
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Trial Status
                    </Typography>
                    <Typography variant="body1">
                      {subscriptionStatus.is_trial_active ? (
                        <>
                          Trial ends: {new Date(subscriptionStatus.trial_ends_at).toLocaleDateString()}
                          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                            ({Math.ceil((new Date(subscriptionStatus.trial_ends_at) - new Date()) / (1000 * 60 * 60 * 24))} days remaining)
                          </Typography>
                        </>
                      ) : (
                        <Typography color="error">
                          Trial ended on {new Date(subscriptionStatus.trial_ends_at).toLocaleDateString()}
                        </Typography>
                      )}
                    </Typography>
                  </Box>
                )}

                {/* Action Buttons */}
                <Box sx={{ mt: 3, display: 'flex', gap: 2, flexDirection: 'column' }}>
                  {subscriptionStatus.has_subscription ? (
                    <>
                      <Alert severity="success" sx={{ mb: 2 }}>
                        You have full access to Unravel
                      </Alert>
                      <Button
                        variant="outlined"
                        color="primary"
                        onClick={handleManageSubscription}
                        disabled={actionLoading}
                        fullWidth
                      >
                        {actionLoading ? <CircularProgress size={24} /> : 'Manage Subscription'}
                      </Button>
                    </>
                  ) : subscriptionStatus.is_trial_active ? (
                    <>
                      <Alert severity="info" sx={{ mb: 2 }}>
                        Subscribe now to ensure uninterrupted access after your trial ends
                      </Alert>
                      <Button
                        variant="contained"
                        color="primary"
                        onClick={handleSubscribe}
                        disabled={actionLoading}
                        fullWidth
                      >
                        {actionLoading ? <CircularProgress size={24} /> : 'Subscribe for $12/month'}
                      </Button>
                    </>
                  ) : (
                    <>
                      <Alert severity="error" sx={{ mb: 2 }}>
                        Your trial has ended. Subscribe to continue using Unravel.
                      </Alert>
                      <Button
                        variant="contained"
                        color="error"
                        onClick={handleSubscribe}
                        disabled={actionLoading}
                        fullWidth
                      >
                        {actionLoading ? <CircularProgress size={24} /> : 'Subscribe for $12/month'}
                      </Button>
                    </>
                  )}
                </Box>
              </Box>
            ) : (
              <Alert severity="warning">Failed to load subscription status</Alert>
            )}
          </Paper>
          <Paper sx={{ p: 3, mt: 3 }}>
            <Typography variant="h6" gutterBottom>
              Email Preferences
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Control how often you receive daily insight emails
            </Typography>
            {emailPrefLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
              </Box>
            ) : (
              <Box>
                <FormControl fullWidth>
                  <InputLabel id="email-frequency-label">Email Frequency</InputLabel>
                  <Select
                    labelId="email-frequency-label"
                    id="email-frequency"
                    value={emailFrequency}
                    label="Email Frequency"
                    onChange={handleEmailFrequencyChange}
                    disabled={emailPrefSaving}
                  >
                    {emailChoices.map(([value, label]) => (
                      <MenuItem key={value} value={value}>
                        {label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                {emailPrefMessage && (
                  <Alert severity={emailPrefMessage.type} sx={{ mt: 2 }}>
                    {emailPrefMessage.text}
                  </Alert>
                )}
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default UserProfile;
