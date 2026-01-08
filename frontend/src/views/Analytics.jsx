import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
} from '@mui/material';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import PeopleIcon from '@mui/icons-material/People';
import EmailIcon from '@mui/icons-material/Email';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import { authApi } from '../services/authApi';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

function Analytics() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [overview, setOverview] = useState(null);
  const [signupsData, setSignupsData] = useState(null);
  const [emailData, setEmailData] = useState(null);
  const [funnelData, setFunnelData] = useState(null);
  const [topUsers, setTopUsers] = useState(null);
  const { accessToken } = useAuth();

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      setError('');

      // Fetch all analytics data in parallel
      const [
        overviewRes,
        signupsRes,
        emailRes,
        funnelRes,
        topUsersRes
      ] = await Promise.all([
        authApi.get('/api/analytics/overview/', accessToken).then(r => r.json()),
        authApi.get('/api/analytics/signups/?days=30', accessToken).then(r => r.json()),
        authApi.get('/api/analytics/email-engagement/?days=30', accessToken).then(r => r.json()),
        authApi.get('/api/analytics/public-funnel/?days=30', accessToken).then(r => r.json()),
        authApi.get('/api/analytics/top-users/?limit=10', accessToken).then(r => r.json()),
      ]);

      setOverview(overviewRes);
      setSignupsData(signupsRes);
      setEmailData(emailRes);
      setFunnelData(funnelRes);
      setTopUsers(topUsersRes);
    } catch (err) {
      setError('Failed to load analytics. You may not have admin permissions.');
      console.error('Error loading analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
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

  // Prepare chart data
  const signupsChartData = {
    labels: signupsData?.signups?.map(s => new Date(s.date).toLocaleDateString()) || [],
    datasets: [
      {
        label: 'Signups',
        data: signupsData?.signups?.map(s => s.count) || [],
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        tension: 0.4,
      },
    ],
  };

  const emailChartData = {
    labels: emailData?.emails_sent?.map(e => new Date(e.date).toLocaleDateString()) || [],
    datasets: [
      {
        label: 'Emails Sent',
        data: emailData?.emails_sent?.map(e => e.count) || [],
        borderColor: 'rgb(54, 162, 235)',
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
      },
      {
        label: 'Opens',
        data: emailData?.opens?.map(o => {
          const date = new Date(o.date).toLocaleDateString();
          return o.count;
        }) || [],
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
      },
      {
        label: 'Clicks',
        data: emailData?.clicks?.map(c => {
          const date = new Date(c.date).toLocaleDateString();
          return c.count;
        }) || [],
        borderColor: 'rgb(255, 159, 64)',
        backgroundColor: 'rgba(255, 159, 64, 0.2)',
      },
    ],
  };

  const funnelChartData = {
    labels: funnelData?.funnel_by_day?.map(f => new Date(f.date).toLocaleDateString()) || [],
    datasets: [
      {
        label: 'Dream Submissions',
        data: funnelData?.funnel_by_day?.map(f => f.total) || [],
        backgroundColor: 'rgba(153, 102, 255, 0.6)',
      },
      {
        label: 'Email Captured',
        data: funnelData?.funnel_by_day?.map(f => f.with_email) || [],
        backgroundColor: 'rgba(75, 192, 192, 0.6)',
      },
      {
        label: 'Interpretations Sent',
        data: funnelData?.funnel_by_day?.map(f => f.sent) || [],
        backgroundColor: 'rgba(54, 162, 235, 0.6)',
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        width: '100%',
        overflow: 'auto',
        p: 3,
      }}
    >
      <Typography variant="h4" gutterBottom>
        Marketing Analytics
      </Typography>

      {/* Overview Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <PeopleIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Total Users</Typography>
              </Box>
              <Typography variant="h3">{overview?.overview?.total_users || 0}</Typography>
              <Typography variant="body2" color="text.secondary">
                +{overview?.overview?.new_users_7d || 0} this week
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TrendingUpIcon sx={{ mr: 1, color: 'success.main' }} />
                <Typography variant="h6">Active Users</Typography>
              </Box>
              <Typography variant="h3">{overview?.overview?.active_users_30d || 0}</Typography>
              <Typography variant="body2" color="text.secondary">
                Last 30 days
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <AttachMoneyIcon sx={{ mr: 1, color: 'warning.main' }} />
                <Typography variant="h6">Subscriptions</Typography>
              </Box>
              <Typography variant="h3">{overview?.subscriptions?.active || 0}</Typography>
              <Typography variant="body2" color="text.secondary">
                {overview?.subscriptions?.trial || 0} in trial
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <EmailIcon sx={{ mr: 1, color: 'info.main' }} />
                <Typography variant="h6">Email Open Rate</Typography>
              </Box>
              <Typography variant="h3">{overview?.email_performance?.open_rate || 0}%</Typography>
              <Typography variant="body2" color="text.secondary">
                Last 30 days
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              User Signups (Last 30 Days)
            </Typography>
            <Box sx={{ height: 'calc(100% - 40px)' }}>
              <Line data={signupsChartData} options={chartOptions} />
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              Email Engagement (Last 30 Days)
            </Typography>
            <Box sx={{ height: 'calc(100% - 40px)' }}>
              <Line data={emailChartData} options={chartOptions} />
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ p: 2, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              Public Dream Funnel (Last 30 Days)
            </Typography>
            <Box sx={{ height: 'calc(100% - 40px)' }}>
              <Bar data={funnelChartData} options={chartOptions} />
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Public Funnel Stats */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Public Dream Funnel
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography>Total Submissions</Typography>
                <Chip label={overview?.public_funnel?.total_submissions || 0} color="primary" />
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography>Email Captured</Typography>
                <Chip label={overview?.public_funnel?.email_captured || 0} color="success" />
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography>Interpretations Sent</Typography>
                <Chip label={overview?.public_funnel?.interpretations_sent || 0} color="info" />
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography>Conversion Rate</Typography>
                <Chip label={`${overview?.public_funnel?.conversion_rate || 0}%`} color="warning" />
              </Box>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Email Performance (30 Days)
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography>Emails Sent</Typography>
                <Chip label={overview?.email_performance?.emails_sent_30d || 0} color="primary" />
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography>Unique Opens</Typography>
                <Chip label={overview?.email_performance?.unique_opens_30d || 0} color="success" />
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography>Clicks</Typography>
                <Chip label={overview?.email_performance?.clicks_30d || 0} color="info" />
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography>Click Rate</Typography>
                <Chip label={`${overview?.email_performance?.click_rate || 0}%`} color="warning" />
              </Box>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Top Users Tables */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Top Users by Conversations
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Email</TableCell>
                    <TableCell>Name</TableCell>
                    <TableCell align="right">Count</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {topUsers?.top_by_conversations?.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell>{user.email}</TableCell>
                      <TableCell>
                        {user.first_name || user.last_name
                          ? `${user.first_name || ''} ${user.last_name || ''}`.trim()
                          : '-'}
                      </TableCell>
                      <TableCell align="right">{user.conversation_count}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Top Users by Messages
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Email</TableCell>
                    <TableCell>Name</TableCell>
                    <TableCell align="right">Count</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {topUsers?.top_by_messages?.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell>{user.email}</TableCell>
                      <TableCell>
                        {user.first_name || user.last_name
                          ? `${user.first_name || ''} ${user.last_name || ''}`.trim()
                          : '-'}
                      </TableCell>
                      <TableCell align="right">{user.message_count}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Analytics;
