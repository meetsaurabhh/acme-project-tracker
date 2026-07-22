import { useCallback, useEffect, useState } from 'react'
import {
  Alert, Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle,
  IconButton, MenuItem, Paper, Stack, Table, TableBody, TableCell, TableHead,
  TableRow, TextField, Typography,
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import DeleteIcon from '@mui/icons-material/DeleteOutline'
import api, { readError } from '../api'
import { tokens } from '../theme'

const ROLES = ['admin', 'manager', 'viewer']
const EMPTY = { email: '', full_name: '', role: 'viewer', password: '' }

export default function Users() {
  const [rows, setRows] = useState([])
  const [dialog, setDialog] = useState(false)
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    try { setRows((await api.get('/api/users')).data) }
    catch (e) { setError(readError(e, 'Could not load accounts.')) }
  }, [])

  useEffect(() => { load() }, [load])

  const save = async () => {
    try { await api.post('/api/users', form); setDialog(false); load() }
    catch (e) { setError(readError(e, 'Could not create the account.')) }
  }

  const remove = async (u) => {
    if (!window.confirm(`Delete the account for ${u.full_name}?`)) return
    try { await api.delete(`/api/users/${u.id}`); load() }
    catch (e) { setError(readError(e)) }
  }

  const field = (key) => ({ value: form[key], onChange: (e) => setForm((f) => ({ ...f, [key]: e.target.value })) })

  return (
    <Stack spacing={3}>
      <Stack direction="row" justifyContent="space-between" alignItems="flex-end" flexWrap="wrap" gap={2}>
        <Box>
          <Typography variant="overline" sx={{ color: tokens.muted }}>Administration</Typography>
          <Typography variant="h1">Accounts and access</Typography>
        </Box>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => { setForm(EMPTY); setDialog(true) }}>
          New account
        </Button>
      </Stack>

      {error && <Alert severity="error" onClose={() => setError('')}>{error}</Alert>}

      <Paper sx={{ p: 2 }}>
        <Typography sx={{ fontSize: '0.85rem', color: tokens.muted }}>
          Admins manage accounts and everything else. Managers create and edit projects, deliverables,
          assignments and spend. Viewers can read but not change anything.
        </Typography>
      </Paper>

      <Paper>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Role</TableCell>
              <TableCell>Active</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((u) => (
              <TableRow key={u.id} hover>
                <TableCell sx={{ fontWeight: 600, fontSize: '0.88rem' }}>{u.full_name}</TableCell>
                <TableCell sx={{ fontFamily: '"IBM Plex Mono", monospace', fontSize: '0.8rem' }}>{u.email}</TableCell>
                <TableCell><Chip size="small" label={u.role} /></TableCell>
                <TableCell>{u.is_active ? 'Yes' : 'No'}</TableCell>
                <TableCell align="right">
                  <IconButton size="small" onClick={() => remove(u)}><DeleteIcon fontSize="small" /></IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Dialog open={dialog} onClose={() => setDialog(false)} fullWidth maxWidth="xs">
        <DialogTitle sx={{ fontFamily: '"Space Grotesk", sans-serif' }}>New account</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField fullWidth label="Full name" {...field('full_name')} />
            <TextField fullWidth label="Work email" {...field('email')} />
            <TextField fullWidth select label="Role" {...field('role')}>
              {ROLES.map((r) => <MenuItem key={r} value={r}>{r}</MenuItem>)}
            </TextField>
            <TextField fullWidth type="password" label="Temporary password" helperText="At least 6 characters" {...field('password')} />
          </Stack>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={save}>Create account</Button>
        </DialogActions>
      </Dialog>
    </Stack>
  )
}
