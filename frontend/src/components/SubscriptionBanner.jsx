import { useState, useEffect } from 'react';
import { Alert, Button, Box } from '@mui/material';
import { subscriptionApi } from '../services/subscriptionApi';

function SubscriptionBanner() {
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadSubscriptionStatus();
  }, []);

  const loadSubscriptionStatus = async () => {
    try {
      const status = await subscriptionApi.getStatus();
      setSubscriptionStatus(status);
    } catch (err) {
      console.error('Failed to load subscription status:', err);
    }
  };

  const handleSubscribe = async () => {
    setLoading(true);
    try {
      const { url } = await subscriptionApi.createCheckoutSession(
        `${window.location.origin}/chat`,
        `${window.location.origin}/chat`
      );
      window.location.href = url;
    } catch (err) {
      console.error('Failed to create checkout session:', err);
      setLoading(false);
    }
  };

  const handleManageSubscription = async () => {
    setLoading(true);
    try {
      const { url } = await subscriptionApi.createPortalSession(
        window.location.href
      );
      window.location.href = url;
    } catch (err) {
      console.error('Failed to create portal session:', err);
      setLoading(false);
    }
  };

  if (!subscriptionStatus) return null;

  const { has_subscription, is_trial_active, can_use_service, trial_ends_at } = subscriptionStatus;

  // Don't show banner if user has active subscription
  if (has_subscription) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert
          severity="success"
          action={
            <Button color="inherit" size="small" onClick={handleManageSubscription} disabled={loading}>
              Manage
            </Button>
          }
        >
          You have an active subscription
        </Alert>
      </Box>
    );
  }

  // Calculate days remaining in trial
  let daysRemaining = 0;
  if (trial_ends_at) {
    const now = new Date();
    const trialEnd = new Date(trial_ends_at);
    daysRemaining = Math.ceil((trialEnd - now) / (1000 * 60 * 60 * 24));
  }

  // Trial is active
  if (is_trial_active && daysRemaining > 3) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert
          severity="info"
          action={
            <Button color="inherit" size="small" onClick={handleSubscribe} disabled={loading}>
              Subscribe Now
            </Button>
          }
        >
          Free trial: {daysRemaining} days remaining
        </Alert>
      </Box>
    );
  }

  // Trial ending soon (3 days or less)
  if (is_trial_active && daysRemaining <= 3) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert
          severity="warning"
          action={
            <Button color="inherit" size="small" onClick={handleSubscribe} disabled={loading}>
              Subscribe for $12/month
            </Button>
          }
        >
          Your trial ends in {daysRemaining} day{daysRemaining !== 1 ? 's' : ''}. Subscribe to continue using Unravel
        </Alert>
      </Box>
    );
  }

  // Trial expired
  if (!can_use_service) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert
          severity="error"
          action={
            <Button color="inherit" size="small" onClick={handleSubscribe} disabled={loading}>
              Subscribe for $12/month
            </Button>
          }
        >
          Your trial has ended. Subscribe to continue using Unravel.
        </Alert>
      </Box>
    );
  }

  return null;
}

export default SubscriptionBanner;
