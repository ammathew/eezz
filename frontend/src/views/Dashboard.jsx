import { Box, Typography, Paper, Grid } from '@mui/material';

function Dashboard() {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6} lg={3}>
          <Paper sx={{ p: 2, bgcolor: 'primary.main', color: 'white' }}>
            <Typography variant="h6">Total Conversations</Typography>
            <Typography variant="h3">0</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6} lg={3}>
          <Paper sx={{ p: 2, bgcolor: 'success.main', color: 'white' }}>
            <Typography variant="h6">Messages Today</Typography>
            <Typography variant="h3">0</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6} lg={3}>
          <Paper sx={{ p: 2, bgcolor: 'warning.main', color: 'white' }}>
            <Typography variant="h6">Active Users</Typography>
            <Typography variant="h3">1</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6} lg={3}>
          <Paper sx={{ p: 2, bgcolor: 'info.main', color: 'white' }}>
            <Typography variant="h6">Uptime</Typography>
            <Typography variant="h3">100%</Typography>
          </Paper>
        </Grid>
      </Grid>
      <Box sx={{ mt: 4 }}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Welcome to Unravel
          </Typography>
          <Typography variant="body1">
            This is your personal AI chat assistant dashboard. Navigate to the Chat section to start a conversation.
          </Typography>
        </Paper>
      </Box>
    </Box>
  );
}

export default Dashboard;
