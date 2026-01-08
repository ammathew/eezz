import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { ThemeProvider } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { Box, CircularProgress } from '@mui/material'
import './App.css'
import { AuthProvider, useAuth } from './context/AuthContext'
import Login from './components/Login'
import Signup from './components/Signup'
import OAuthCallback from './components/OAuthCallback'
import FacebookCallback from './components/FacebookCallback'
import PublicDreamForm from './components/PublicDreamForm'
import EmailCapture from './components/EmailCapture'
import Unsubscribe from './components/Unsubscribe'
import AdminLayout from './layouts/AdminLayout'
import theme from './theme'

function ProtectedRoute({ children }) {
  const { loading, isAuthenticated } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
          bgcolor: 'background.default',
        }}
      >
        <CircularProgress />
      </Box>
    )
  }

  if (!isAuthenticated) {
    if (location.pathname.startsWith('/ad-studio')) {
      return children
    }
    // Redirect to go.unravel.so for non-logged-in users (production only)
    const isDevelopment = import.meta.env.DEV || window.location.hostname === 'localhost'

    if (isDevelopment) {
      // In development, redirect to local login page
      window.location.href = '/login'
    } else {
      // In production, redirect to marketing site
      window.location.href = 'https://go.unravel.so'
    }
    return null
  }

  return children
}

function LoginPage() {
  const navigate = useNavigate()
  return <Login onSwitch={() => navigate('/signup')} />
}

function SignupPage() {
  const navigate = useNavigate()
  return <Signup onSwitch={() => navigate('/login')} />
}

function App() {
  return (
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AuthProvider>
          <Routes>
            {/* Public routes */}
            <Route path="/interpret" element={<PublicDreamForm />} />
            <Route path="/interpret/email" element={<EmailCapture />} />
            <Route path="/public-unsubscribe/:token" element={<Unsubscribe />} />

            {/* Auth routes */}
            <Route path="/auth/callback" element={<OAuthCallback />} />
            <Route path="/facebook/callback" element={<FacebookCallback />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />

            {/* Protected routes */}
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <AdminLayout />
                </ProtectedRoute>
              }
            />

            {/* Default redirect */}
            {/* <Route path="/" element={<Navigate to="/interpret" replace />} /> */}
          </Routes>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  )
}

export default App
