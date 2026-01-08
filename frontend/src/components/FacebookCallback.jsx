import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, CircularProgress, Typography, Alert } from '@mui/material';
import { adApi } from '../services/adApi';

function FacebookCallback() {
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const redirectUri = useMemo(() => `${window.location.origin}/facebook/callback`, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const fbError = params.get('error');
    const fbErrorDesc = params.get('error_description');

    if (fbError) {
      setError(fbErrorDesc || 'Facebook authorization failed.');
      return;
    }

    if (!code) {
      setError('Missing authorization code.');
      return;
    }

    const connect = async () => {
      try {
        await adApi.connectFacebook({ code, redirect_uri: redirectUri });
        navigate('/ad-studio?connected=1', { replace: true });
      } catch (err) {
        setError(err.message);
      }
    };

    connect();
  }, [navigate, redirectUri]);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mt: 10 }}>
      {error ? (
        <Alert severity="error">{error}</Alert>
      ) : (
        <>
          <CircularProgress />
          <Typography sx={{ mt: 2 }}>Connecting your Facebook account…</Typography>
        </>
      )}
    </Box>
  );
}

export default FacebookCallback;
