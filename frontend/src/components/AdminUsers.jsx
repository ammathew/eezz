import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../services/authApi';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Alert,
  CircularProgress,
  Avatar,
} from '@mui/material';
import LoginIcon from '@mui/icons-material/Login';

function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { user, accessToken, setUser, setAccessToken, setRefreshToken } = useAuth();
  const navigate = useNavigate();

  // Redirect non-superusers
  useEffect(() => {
    if (user && !user.is_superuser) {
      navigate('/chat');
    }
  }, [user, navigate]);

  useEffect(() => {
    // Only load users if user is a superuser
    if (user?.is_superuser) {
      loadUsers();
    }
  }, [user]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await authApi.getAllUsers(accessToken);
      setUsers(data);
    } catch (err) {
      setError('Failed to load users. You may not have admin permissions.');
      console.error('Error loading users:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleLoginAsUser = async (userId) => {
    try {
      setError('');
      const data = await authApi.loginAsUser(userId, accessToken);

      // Update auth context with new tokens and user
      setAccessToken(data.access);
      setRefreshToken(data.refresh);
      setUser(data.user);

      // Store in localStorage
      localStorage.setItem('accessToken', data.access);
      localStorage.setItem('refreshToken', data.refresh);

      // Redirect to chat
      window.location.href = '/dashboard/chat';
    } catch (err) {
      setError('Failed to login as user. You may not have admin permissions.');
      console.error('Error logging in as user:', err);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        width: '100%',
        overflow: 'hidden',
      }}
    >
      {/* Header - fixed at top */}
      <Box sx={{ p: 3, pb: 2 }}>
        <Typography variant="h4" gutterBottom>
          User Management
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 0 }}>
            {error}
          </Alert>
        )}
      </Box>

      {/* Scrollable table area */}
      <Box
        sx={{
          flex: 1,
          overflow: 'auto',
          px: 3,
          pb: 3,
        }}
      >
        <TableContainer component={Paper}>
          <Table stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell>Avatar</TableCell>
                <TableCell>Email</TableCell>
                <TableCell>Name</TableCell>
                <TableCell>User ID</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.id}>
                  <TableCell>
                    <Avatar
                      src={user.picture}
                      alt={user.email}
                      sx={{ width: 40, height: 40 }}
                    />
                  </TableCell>
                  <TableCell>{user.email}</TableCell>
                  <TableCell>
                    {user.first_name || user.last_name
                      ? `${user.first_name} ${user.last_name}`.trim()
                      : '-'}
                  </TableCell>
                  <TableCell>{user.id}</TableCell>
                  <TableCell align="right">
                    <Button
                      variant="contained"
                      color="primary"
                      size="small"
                      startIcon={<LoginIcon />}
                      onClick={() => handleLoginAsUser(user.id)}
                    >
                      Login As
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        {users.length === 0 && !loading && (
          <Typography sx={{ textAlign: 'center', p: 4, color: 'text.secondary' }}>
            No users found
          </Typography>
        )}
      </Box>
    </Box>
  );
}

export default AdminUsers;
