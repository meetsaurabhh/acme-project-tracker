import { useCallback, useEffect, useState } from 'react'
import {
  Alert, Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle,
  Grid, IconButton, LinearProgress, Paper, Stack, TextField, Typography,
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import EditIcon from '@mui/icons-material/EditOutlined'
import DeleteIcon from '@mui/icons-material/DeleteOutline'
import api, { readError } from '../api'
import { useAuth } from '../auth'
import { tokens } from '../theme'

const EMPTY = { full_name: '', email: '', job_title: '', department: '', location: '', weekly_capacity_hours: 40 }

export default function Resources() {
  const { canEdit } = useAuth()
  const [rows, setRows] = useState([])
  const [search, setSearch] = useState('')
  const [dialog, setDialog] = useState(false)
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    try {
      const { data } = await api.get('/api/analytics/resource-utilisation')
      setRows(data)
    } catch (e) { setError(readError(e, 'Could not load people.')) }
  }, [])

  useEffect(() => { load() }, [load])

  const filtered = rows.filter((r) =>
    !search || `${r.resource_name} ${r.job_title} ${r.department}`.toLowerCase().includes(search.toLowerCase())
  )

  const save = async () => {
    try {
      const payload = { ...form, weekly_capacity_hours: Number(form.weekly_capacity_hours), email: form.email || null }
      if (form.id) await api.patch(`/api/resources/${form.id}`, payload)
      else await api.post('/api/resources', payload)
      setDialog(false); load()
    } catch (e) { setError(readError(e, 'Could not save this person.')) }
  }

  const remove = async (r) => {
    if (!window.confirm(`Remove ${r.resource_name}? Their project assignments go too.`)) return
    try { await api.delete(`/api/resources/${r.resource_id}`); load() }
    catch (e) { setError(readError(e)) }
  }

  const field = (key) => ({ value: form[key] ?? '', onChange: (e) => setForm((f) => ({ ...f, [key]: e.target.value })) })
  const barColour = (s) => (s === 'over' ? tokens.alert : s === 'full' ? tokens.watch : tokens.healthy)

  return (
    <Stack spacing={3}>
      <Stack direction="row" justifyContent="space-between" alignItems="flex-end" flexWrap="wrap" gap={2}>
        <Box>
          <Typography variant="overline" sx={{ color: tokens.muted }}>Capacity</Typography>
          <Typography variant="h1">People and their load</Typography>
        </Box>
        {canEdit && (
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => { setForm(EMPTY); setDialog(true) }}>
            Add person
          </Button>
        )}
      </Stack>

      {error && <Alert severity="error" onClose={() => setError('')}>{error}</Alert>}

      <TextField size="small" label="Search by name, title or department" value={search}
        onChange={(e) => setSearch(e.target.value)} sx={{ maxWidth: 420 }} />

      <Grid container spacing={2}>
        {filtered.map((r) => (
          <Grid item xs={12} md={6} lg={4} key={r.resource_id}>
            <Paper sx={{ p: 2.5, height: '100%' }}>
              <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                <Box>
                  <Typography sx={{ fontWeight: 600 }}>{r.resource_name}</Typography>
                  <Typography variant="overline" sx={{ color: tokens.muted }}>
                    {r.job_title} · {r.department}
                  </Typography>
                </Box>
                {canEdit && (
                  <Box>
                    <IconButton size="small" onClick={() => { setForm({ id: r.resource_id, full_name: r.resource_name, job_title: r.job_title, department: r.department, weekly_capacity_hours: r.weekly_capacity_hours }); setDialog(true) }}>
                      <EditIcon fontSize="small" />
                    </IconButton>
                    <IconButton size="small" onClick={() => remove(r)}><DeleteIcon fontSize="small" /></IconButton>
                  </Box>
                )}
              </Stack>

              <Box sx={{ mt: 2 }}>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="overline" sx={{ color: tokens.muted }}>Committed</Typography>
                  <Typography sx={{ fontFamily: '"IBM Plex Mono", monospace', fontSize: '0.8rem', color: barColour(r.status) }}>
                    {r.total_allocation_pct}% · {r.committed_hours}h/wk
                  </Typography>
                </Stack>
                <LinearProgress
                  variant="determinate"
                  value={Math.min(r.total_allocation_pct, 100)}
                  sx={{ height: 8, borderRadius: 2, mt: 0.5, bgcolor: tokens.line, '& .MuiLinearProgress-bar': { bgcolor: barColour(r.status) } }}
                />
              </Box>

              <Stack spacing={0.5} sx={{ mt: 1.5 }}>
                {r.assignments.length === 0
                  ? <Typography sx={{ fontSize: '0.8rem', color: tokens.muted }}>Available. No live assignments.</Typography>
                  : r.assignments.map((a) => (
                      <Stack key={a.project_id} direction="row" justifyContent="space-between">
                        <Typography sx={{ fontSize: '0.8rem' }}>{a.project_name}</Typography>
                        <Chip size="small" label={`${a.allocation_pct}%`} sx={{ height: 18, fontSize: '0.7rem' }} />
                      </Stack>
                    ))}
              </Stack>
            </Paper>
          </Grid>
        ))}
      </Grid>

      <Dialog open={dialog} onClose={() => setDialog(false)} fullWidth maxWidth="xs">
        <DialogTitle sx={{ fontFamily: '"Space Grotesk", sans-serif' }}>{form.id ? 'Edit person' : 'Add person'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField fullWidth label="Full name" {...field('full_name')} />
            <TextField fullWidth label="Email" {...field('email')} />
            <TextField fullWidth label="Job title" {...field('job_title')} />
            <TextField fullWidth label="Department" {...field('department')} />
            <TextField fullWidth label="Location" {...field('location')} />
            <TextField fullWidth type="number" label="Hours available per week" {...field('weekly_capacity_hours')} />
          </Stack>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={save}>Save person</Button>
        </DialogActions>
      </Dialog>
    </Stack>
  )
}
