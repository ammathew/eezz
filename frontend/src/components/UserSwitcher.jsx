import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../services/authApi';
import {
  Box,
  Button,
  Menu,
  MenuItem,
  Typography,
  Avatar,
  Divider,
  TextField,
  CircularProgress,
  Chip,
} from '@mui/material';
import {
  SupervisorAccount as SupervisorAccountIcon,
  KeyboardArrowDown as ArrowDownIcon,
  Person as PersonIcon,
} from '@mui/icons-material';

function UserSwitcher() {
  const [anchorEl, setAnchorEl] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const { user, accessToken, setUser, setAccessToken, setRefreshToken } = useAuth();

  const open = Boolean(anchorEl);

  // Check if there's a hijack session active
  const hijackToken = sessionStorage.getItem('hijackToken');
  const adminEmail = sessionStorage.getItem('adminEmail');
  const isInHijackMode = !!hijackToken;

  // Show this component if current user is superuser OR if we're in hijack mode
  if (!user?.is_superuser && !isInHijackMode) {
    return null;
  }

  const handleClick = async (event) => {
    setAnchorEl(event.currentTarget);

    // Load users when opening dropdown
    if (users.length === 0) {
      await loadUsers();
    }
  };

  const handleClose = () => {
    setAnchorEl(null);
    setSearchTerm('');
  };

  const loadUsers = async () => {
    try {
      setLoading(true);
      // Always use current accessToken - backend handles permissions
      const data = await authApi.getAllUsers(accessToken);
      setUsers(data);
    } catch (err) {
      console.error('Error loading users:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSwitchUser = async (targetUser) => {
    try {
      // Don't switch if already this user
      if (targetUser.id === user.id) {
        handleClose();
        return;
      }

      // Start new hijack session
      // Backend will automatically end any existing hijack session if in hijack mode
      const data = await authApi.startHijackSession(targetUser.id, accessToken);

      // Store NEW hijack session token in sessionStorage
      sessionStorage.setItem('hijackToken', data.hijack_token);
      sessionStorage.setItem('adminEmail', data.admin_email);
      sessionStorage.setItem('hijackExpiresAt', data.expires_at);

      // Update tokens in localStorage
      localStorage.setItem('accessToken', data.access);
      localStorage.setItem('refreshToken', data.refresh);

      handleClose();

      console.log('Switching to user:', data.user.email);

      // Reload the page to refresh all data for the new user
      window.location.reload();
    } catch (err) {
      console.error('Error switching user:', err);
      alert(err.message || 'Failed to switch user');
    }
  };

  const handleExitHijack = async () => {
    try {
      if (!hijackToken) {
        console.log('No hijack token found');
        return;
      }

      console.log('Ending hijack session with token:', hijackToken);

      // End hijack session
      const data = await authApi.endHijackSession(hijackToken, accessToken);

      console.log('Received admin data:', data);

      // CRITICAL: Store admin tokens in localStorage FIRST before clearing anything
      localStorage.setItem('accessToken', data.access);
      localStorage.setItem('refreshToken', data.refresh);

      // Clear hijack session data from sessionStorage
      sessionStorage.removeItem('hijackToken');
      sessionStorage.removeItem('adminEmail');
      sessionStorage.removeItem('hijackExpiresAt');

      handleClose();

      console.log('Reloading page as admin user:', data.user.email);

      // Force reload - this will pick up the new admin tokens from localStorage
      window.location.reload();
    } catch (err) {
      console.error('Error exiting hijack:', err);
      alert(err.message || 'Failed to exit hijack mode');
    }
  };

  const filteredUsers = users.filter(u =>
    u.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    `${u.first_name} ${u.last_name}`.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <>
      <Button
        onClick={handleClick}
        startIcon={<SupervisorAccountIcon />}
        endIcon={<ArrowDownIcon />}
        variant="outlined"
        size="small"
        sx={{
          mr: 2,
          borderColor: isInHijackMode && !user?.is_superuser ? 'warning.main' : 'primary.main',
          color: isInHijackMode && !user?.is_superuser ? 'warning.main' : 'primary.main',
          textTransform: 'none',
          '&:hover': {
            borderColor: isInHijackMode && !user?.is_superuser ? 'warning.dark' : 'primary.dark',
            bgcolor: isInHijackMode && !user?.is_superuser ? 'warning.light' : 'primary.light',
          },
        }}
      >
        {isInHijackMode && !user?.is_superuser ? 'Viewing as User' : 'Switch User'}
      </Button>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        PaperProps={{
          sx: {
            width: 350,
            maxHeight: 500,
          },
        }}
      >
        <Box sx={{ px: 2, py: 1.5 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Switch to User Account
          </Typography>
          <TextField
            fullWidth
            size="small"
            placeholder="Search users..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            sx={{ mt: 1 }}
          />
        </Box>

        <Divider />

        <Box sx={{ maxHeight: 350, overflow: 'auto' }}>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress size={24} />
            </Box>
          ) : filteredUsers.length === 0 ? (
            <MenuItem disabled>
              <Typography color="text.secondary">No users found</Typography>
            </MenuItem>
          ) : (
            filteredUsers.map((u) => (
              <MenuItem
                key={u.id}
                onClick={() => handleSwitchUser(u)}
                selected={u.id === user.id}
                sx={{
                  py: 1.5,
                  display: 'flex',
                  gap: 1.5,
                }}
              >
                <Avatar
                  src={u.picture}
                  sx={{ width: 32, height: 32 }}
                >
                  {u.email[0].toUpperCase()}
                </Avatar>
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography variant="body2" noWrap>
                    {u.first_name || u.last_name
                      ? `${u.first_name} ${u.last_name}`.trim()
                      : u.email}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" noWrap>
                    {u.email}
                  </Typography>
                </Box>
                {u.id === user.id && (
                  <Chip label="Current" size="small" color="primary" />
                )}
                {u.is_superuser && (
                  <Chip label="Admin" size="small" color="error" />
                )}
              </MenuItem>
            ))
          )}
        </Box>

        <Divider />

        <Box sx={{ px: 2, py: 1.5 }}>
          {isInHijackMode && !user?.is_superuser ? (
            <Box>
              <Typography variant="caption" color="warning.main" fontWeight="bold">
                Currently viewing as: {user.email}
              </Typography>
              <Typography variant="caption" display="block" color="text.secondary" sx={{ mb: 1 }}>
                Original admin: {adminEmail}
              </Typography>
              <Button
                fullWidth
                variant="contained"
                color="primary"
                size="small"
                onClick={handleExitHijack}
              >
                Return to Admin Account
              </Button>
            </Box>
          ) : (
            <Typography variant="caption" color="text.secondary">
              Logged in as: {user.email}
            </Typography>
          )}
        </Box>
      </Menu>
    </>
  );
}

export default UserSwitcher;
