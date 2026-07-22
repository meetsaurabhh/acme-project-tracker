import { createTheme } from '@mui/material/styles'

// Palette chosen for a control-room feel: cool paper, deep harbour blue,
// and two signal colours that only ever mean "healthy" or "needs attention".
export const tokens = {
  paper: '#EEF1F4',
  surface: '#FFFFFF',
  ink: '#0F1B2A',
  muted: '#5B6B7C',
  line: '#DDE3E9',
  harbour: '#1F5673',
  healthy: '#16745F',
  watch: '#B4530A',
  alert: '#A6231F',
}

const theme = createTheme({
  palette: {
    mode: 'light',
    background: { default: tokens.paper, paper: tokens.surface },
    primary: { main: tokens.harbour },
    success: { main: tokens.healthy },
    warning: { main: tokens.watch },
    error: { main: tokens.alert },
    text: { primary: tokens.ink, secondary: tokens.muted },
    divider: tokens.line,
  },
  typography: {
    fontFamily: '"Inter", system-ui, sans-serif',
    h1: { fontFamily: '"Space Grotesk", sans-serif', fontWeight: 700, fontSize: '2rem', letterSpacing: '-0.02em' },
    h2: { fontFamily: '"Space Grotesk", sans-serif', fontWeight: 700, fontSize: '1.5rem', letterSpacing: '-0.01em' },
    h3: { fontFamily: '"Space Grotesk", sans-serif', fontWeight: 500, fontSize: '1.15rem' },
    overline: { fontFamily: '"IBM Plex Mono", monospace', fontSize: '0.7rem', letterSpacing: '0.12em', fontWeight: 500 },
    button: { textTransform: 'none', fontWeight: 600 },
  },
  shape: { borderRadius: 6 },
  components: {
    MuiPaper: { styleOverrides: { root: { backgroundImage: 'none', border: `1px solid ${tokens.line}` } } },
    MuiTableCell: { styleOverrides: { head: { fontWeight: 600, color: tokens.muted, fontSize: '0.78rem', letterSpacing: '0.04em', textTransform: 'uppercase' } } },
  },
})

export default theme
