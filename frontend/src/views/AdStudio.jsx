import { useEffect, useMemo, useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Divider,
  Grid,
  Stack,
  TextField,
  Typography,
  Alert,
} from '@mui/material';
import { adApi } from '../services/adApi';

const defaultForm = {
  product: '',
  audience: '',
  offer: '',
  proof: '',
  tone: 'Confident, direct, B2B',
  cta: 'Book Call',
  image_text: '',
  destination_url: '',
  daily_budget: '50',
  campaign_name: '',
  adset_name: '',
  ad_name: '',
  countries: 'US',
  age_min: '18',
  age_max: '65',
  status: 'PAUSED',
};

function AdStudio() {
  const [form, setForm] = useState(defaultForm);
  const [loading, setLoading] = useState(false);
  const [posting, setPosting] = useState(false);
  const [facebookStatus, setFacebookStatus] = useState({ connected: false });
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const redirectUri = useMemo(() => `${window.location.origin}/facebook/callback`, []);

  useEffect(() => {
    const loadStatus = async () => {
      try {
        const status = await adApi.getFacebookStatus();
        setFacebookStatus(status);
      } catch (err) {
        console.error(err);
      }
    };
    loadStatus();
  }, []);

  const handleChange = (field) => (event) => {
    setForm((prev) => ({ ...prev, [field]: event.target.value }));
  };

  const handleGenerate = async () => {
    setError('');
    setNotice('');
    setLoading(true);
    try {
      const data = await adApi.generateAd(form);
      setResult(data);
      setNotice('Ad generated. Review copy and post when ready.');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLaunch = async () => {
    if (!result) return;
    setError('');
    setNotice('');
    setPosting(true);
    try {
      const response = await adApi.launchAd({
        destination_url: form.destination_url,
        daily_budget: form.daily_budget,
        campaign_name: form.campaign_name,
        adset_name: form.adset_name,
        ad_name: form.ad_name,
        countries: form.countries.split(',').map((item) => item.trim()).filter(Boolean),
        age_min: form.age_min,
        age_max: form.age_max,
        status: form.status,
        primary_text: result.primary_text,
        headline: result.headline,
        cta: result.cta,
        image_text: result.image_text,
      });
      setNotice(`Launched ad. Campaign: ${response.campaign_id || 'ok'}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setPosting(false);
    }
  };

  const handleConnect = async () => {
    setError('');
    try {
      const data = await adApi.getFacebookLoginUrl(redirectUri);
      window.location.href = data.login_url;
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <Box sx={{ p: { xs: 2, md: 4 }, height: '100%', overflow: 'auto' }}>
      <Stack spacing={3}>
        <Box>
          <Typography variant="h4" fontWeight={600}>
            Ad Studio
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Generate a square Facebook post with a black background and white text, then publish it.
          </Typography>
        </Box>

        {error && <Alert severity="error">{error}</Alert>}
        {notice && <Alert severity="success">{notice}</Alert>}

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Stack spacing={2}>
                  <Typography variant="h6">Brief</Typography>
                  <TextField
                    label="Product"
                    value={form.product}
                    onChange={handleChange('product')}
                    placeholder="Ad generator for Meta marketers"
                    fullWidth
                  />
                  <TextField
                    label="Audience"
                    value={form.audience}
                    onChange={handleChange('audience')}
                    placeholder="Performance marketers and growth teams"
                    fullWidth
                  />
                  <TextField
                    label="Offer / Outcome"
                    value={form.offer}
                    onChange={handleChange('offer')}
                    placeholder="Generate 10 ads in minutes"
                    fullWidth
                  />
                  <TextField
                    label="Proof / Credibility"
                    value={form.proof}
                    onChange={handleChange('proof')}
                    placeholder="Used by 200+ marketing teams"
                    fullWidth
                  />
                  <TextField
                    label="Tone"
                    value={form.tone}
                    onChange={handleChange('tone')}
                    fullWidth
                  />
                  <TextField
                    label="CTA Preference"
                    value={form.cta}
                    onChange={handleChange('cta')}
                    fullWidth
                  />
                  <TextField
                    label="Image Text Override (optional)"
                    value={form.image_text}
                    onChange={handleChange('image_text')}
                    fullWidth
                  />

                  <Button
                    variant="contained"
                    onClick={handleGenerate}
                    disabled={loading}
                  >
                    {loading ? <CircularProgress size={22} /> : 'Generate Ad'}
                  </Button>
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%' }}>
              <CardContent sx={{ height: '100%' }}>
                <Stack spacing={2} sx={{ height: '100%' }}>
                  <Typography variant="h6">Preview</Typography>
                  <Box
                    sx={{
                      width: '100%',
                      aspectRatio: '1 / 1',
                      bgcolor: 'black',
                      borderRadius: 2,
                      overflow: 'hidden',
                      border: '1px solid',
                      borderColor: 'divider',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    {result?.image_data_url ? (
                      <img
                        src={result.image_data_url}
                        alt="Ad preview"
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      />
                    ) : (
                      <Typography color="white" sx={{ textAlign: 'center', px: 3 }}>
                        Generate to preview the image.
                      </Typography>
                    )}
                  </Box>
                  <Divider />
                  <Stack spacing={1}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Primary Text
                    </Typography>
                    <Typography variant="body2">
                      {result?.primary_text || '—'}
                    </Typography>
                    <Typography variant="subtitle2" color="text.secondary">
                      Headline
                    </Typography>
                    <Typography variant="body2">
                      {result?.headline || '—'}
                    </Typography>
                    <Typography variant="subtitle2" color="text.secondary">
                      CTA
                    </Typography>
                    <Typography variant="body2">
                      {result?.cta || '—'}
                    </Typography>
                  </Stack>
                  <Divider />
                  <Stack spacing={1}>
                    <Typography variant="subtitle2">Facebook Connection</Typography>
                    {facebookStatus.connected ? (
                      <Typography variant="body2">
                        Connected to {facebookStatus.page_name || 'Page'}
                        {facebookStatus.ad_account_name ? ` • ${facebookStatus.ad_account_name}` : ''}.
                      </Typography>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        Connect to a Facebook Page to launch ads.
                      </Typography>
                    )}
                    <Stack direction="row" spacing={2}>
                      <Button variant="outlined" onClick={handleConnect}>
                        {facebookStatus.connected ? 'Reconnect Facebook' : 'Connect Facebook'}
                      </Button>
                    </Stack>
                  </Stack>

                  <Divider />
                  <Stack spacing={2}>
                    <Typography variant="subtitle2">Launch Settings</Typography>
                    <TextField
                      label="Destination URL"
                      value={form.destination_url}
                      onChange={handleChange('destination_url')}
                      fullWidth
                    />
                    <TextField
                      label="Daily Budget (USD)"
                      value={form.daily_budget}
                      onChange={handleChange('daily_budget')}
                      fullWidth
                    />
                    <TextField
                      label="Campaign Name (optional)"
                      value={form.campaign_name}
                      onChange={handleChange('campaign_name')}
                      fullWidth
                    />
                    <TextField
                      label="Ad Set Name (optional)"
                      value={form.adset_name}
                      onChange={handleChange('adset_name')}
                      fullWidth
                    />
                    <TextField
                      label="Ad Name (optional)"
                      value={form.ad_name}
                      onChange={handleChange('ad_name')}
                      fullWidth
                    />
                    <TextField
                      label="Countries (comma-separated)"
                      value={form.countries}
                      onChange={handleChange('countries')}
                      fullWidth
                    />
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <TextField
                          label="Age Min"
                          value={form.age_min}
                          onChange={handleChange('age_min')}
                          fullWidth
                        />
                      </Grid>
                      <Grid item xs={6}>
                        <TextField
                          label="Age Max"
                          value={form.age_max}
                          onChange={handleChange('age_max')}
                          fullWidth
                        />
                      </Grid>
                    </Grid>
                    <TextField
                      label="Status"
                      value={form.status}
                      onChange={handleChange('status')}
                      helperText="Use PAUSED to avoid spending while reviewing."
                      fullWidth
                    />
                    <Button
                      variant="contained"
                      disabled={!facebookStatus.connected || !result || posting}
                      onClick={handleLaunch}
                    >
                      {posting ? <CircularProgress size={22} /> : 'Launch Campaign'}
                    </Button>
                  </Stack>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Stack>
    </Box>
  );
}

export default AdStudio;
