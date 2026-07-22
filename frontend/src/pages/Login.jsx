import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Alert, Box, Button, Paper, Stack, TextField, Typography } from '@mui/material'
import { useAuth } from '../auth'
import { readError } from '../api'
import { tokens } from '../theme'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('admin@acme.com')
  const [password, setPassword] = useState('Admin@123')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async () => {
    setBusy(true); setError('')
    try {
      await login(email.trim().toLowerCase(), password)
      navigate('/')
    } catch (e) {
      setError(readError(e, 'Could not sign in. Check the email and password.'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Box sx={{ minHeight: '100vh', display: 'grid', placeItems: 'center', bgcolor: tokens.ink, p: 2 }}>
      <Paper sx={{ p: { xs: 3, sm: 5 }, width: '100%', maxWidth: 420, border: 0 }}>
        <Typography variant="overline" sx={{ color: tokens.muted }}>ACME Inc.</Typography>
        <Typography variant="h1" sx={{ mt: 0.5, mb: 0.5 }}>Project Tracker</Typography>
        <Typography sx={{ color: tokens.muted, mb: 3, fontSize: '0.92rem' }}>
          Sign in to see project health, deliverables and resource load.
        </Typography>

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        <Stack spacing={2}>
          <TextField
            label="Work email" value={email} fullWidth
            onChange={(e) => setEmail(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && submit()}
          />
          <TextField
            label="Password" type="password" value={password} fullWidth
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && submit()}
          />
          <Button variant="contained" size="large" disabled={busy} onClick={submit}>
            {busy ? 'Signing in...' : 'Sign in'}
          </Button>
        </Stack>

        <Box sx={{ mt: 3, pt: 2, borderTop: `1px solid ${tokens.line}` }}>
          <Typography variant="overline" sx={{ color: tokens.muted }}>Demo accounts</Typography>
          <Typography sx={{ fontFamily: '"IBM Plex Mono", monospace', fontSize: '0.75rem', color: tokens.muted, mt: 0.5 }}>
            admin@acme.com / Admin@123<br />
            manager@acme.com / Manager@123<br />
            viewer@acme.com / Viewer@123
          </Typography>
        </Box>
      </Paper>
    </Box>
  )
}
