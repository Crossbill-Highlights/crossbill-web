import { createTheme } from '@mui/material/styles';

const colors = {
  amber: {
    600: '#685A4B',
    700: '#43311E',
    800: '#2E2215',
  },
  stone: {
    50: '#fafaf9',
    400: '#a8a29e',
    600: '#78716c',
    700: '#57534e',
    900: '#1c1917',
  },
};

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: colors.amber[700],
      light: colors.amber[600],
      dark: colors.amber[800],
      contrastText: '#ffffff',
    },
    secondary: {
      main: colors.stone[600],
      light: colors.stone[400],
      dark: colors.stone[700],
      contrastText: '#ffffff',
    },
    background: {
      default: colors.stone[50],
      paper: '#ffffff',
    },
    text: {
      primary: colors.stone[900],
      secondary: colors.stone[600],
    },
  },
  typography: {
    fontFamily: ['"Lora"', 'Georgia', 'serif'].join(','),
    h1: {
      fontSize: '2rem',
      fontWeight: 900, // Extreme weight for impact
      letterSpacing: '-0.02em',
      lineHeight: 1.2,
    },
    h2: {
      fontSize: '1.4rem',
      fontWeight: 200, // Light weight for contrast
      lineHeight: 1.3,
    },
    h3: {
      fontSize: '1.1rem',
      fontWeight: 800, // Heavy weight
      letterSpacing: '0.01em',
    },
    h4: {
      fontSize: '1.0rem',
      fontWeight: 700,
    },
    h5: {
      fontSize: '1.0rem',
      fontWeight: 700,
    },
    h6: {
      fontSize: '1.0rem',
      fontWeight: 600,
    },
    body1: {
      fontSize: '1.0rem',
      fontWeight: 400, // Light for readability
      lineHeight: 1.75,
      letterSpacing: '0.01em',
    },
    body2: {
      fontWeight: 200, // Very light
      lineHeight: 1.6,
    },
  },
  shape: {
    borderRadius: 12, // rounded-xl as default
  },
  shadows: [
    'none',
    '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)', // shadow-sm
    '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)', // shadow-md
    '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)', // shadow-lg
    '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)', // shadow-xl
    '0 25px 50px -12px rgb(0 0 0 / 0.25)', // shadow-2xl
    '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
    '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
    '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
    '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
    '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
    '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
    '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
    '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
    '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
    '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
    '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
    '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
  ],
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 12,
          fontWeight: 500,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16, // rounded-2xl
          border: `1px solid ${colors.stone[400]}`,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        rounded: {
          borderRadius: 16, // rounded-2xl
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          backgroundColor: colors.stone[50], // Same as body background
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 12, // rounded-xl
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderColor: colors.amber[700],
            },
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
              borderColor: colors.amber[700],
              borderWidth: 2,
            },
          },
        },
      },
    },
  },
});
