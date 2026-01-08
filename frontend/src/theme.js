import { createTheme } from '@mui/material/styles';

// Black Dashboard inspired dark theme
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#e14eca',
      light: '#e76ff0',
      dark: '#ba2d9e',
    },
    secondary: {
      main: '#1d8cf8',
      light: '#4aa3f9',
      dark: '#1570c6',
    },
    success: {
      main: '#00f2c3',
      light: '#33f4d1',
      dark: '#00c29c',
    },
    warning: {
      main: '#ff8d72',
      light: '#ffa48e',
      dark: '#cc7158',
    },
    error: {
      main: '#fd5d93',
      light: '#fd7da9',
      dark: '#ca4a76',
    },
    info: {
      main: '#1d8cf8',
      light: '#4aa3f9',
      dark: '#1570c6',
    },
    background: {
      default: '#1e1e2e',
      paper: '#27293d',
    },
    text: {
      primary: '#ffffff',
      secondary: 'rgba(255, 255, 255, 0.7)',
    },
  },
  typography: {
    fontFamily: [
      'Poppins',
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
    h4: {
      fontWeight: 300,
      fontSize: '2.125rem',
    },
    h5: {
      fontWeight: 300,
      fontSize: '1.5rem',
    },
    h6: {
      fontWeight: 400,
      fontSize: '1.25rem',
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 400,
          borderRadius: 8,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: '#27293d',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: '#1e1e2e',
          backgroundImage: 'linear-gradient(0deg, #1e1e2e 0%, #1a1a28 100%)',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#27293d',
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          '&.Mui-selected': {
            backgroundColor: '#e14eca',
            '&:hover': {
              backgroundColor: '#ba2d9e',
            },
          },
        },
      },
    },
  },
});

export default theme;
