import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMediaQuery } from 'react-responsive'
import {
  Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, Grid,
  IconButton, MenuItem, Paper, Stack, Table, TableBody, TableCell, TableHead,
  TableRow, TextField, Typography,
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import EditIcon from '@mui/icons-material/EditOutlined'
import DeleteIcon from '@mui/icons-material/DeleteOutline'
import api, { readError } from '../api'
import { useAuth } from '../auth'
import DeliveryRail from '../components/DeliveryRail'
import RiskChip from '../components/RiskChip'
import { tokens } from '../theme'

const STATUSES = ['planning', 'active', 'on_hold', 'completed', 'cancelled']
const EMPTY = {
  code: '', name: '', description: '', department: '', status: 'planning',
  priority: 3, start_date: '', end_date: '', planned_budget: 0, manager_id: '',
}

export default function Projects() {
  const { canEdit } = useAuth()
  const navigate = useNavigate()
  const isMobile = useMediaQuery({ maxWidth: 900 })

  const [rows, setRows] = useState([])
  const [users, setUsers] = useState([])
  const [departments, setDepartments] = useState([])
  const [filters, setFilters] = useState({ search: '', status: '', department: '', risk: '' })
  const [dialog, setDialog] = useState(null)
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    try {
      const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v))
      const [p, d] = await Promise.all([
        api.get('/api/projects', { params }),
        api.get('/api/projects/departments'),
      ])
      setRows(p.data); setDepartments(d.data); setError('')
    } catch (e) { setError(readError(e, 'Could not load projects.')) }
  }, [filters])

  useEffect(() => { load() }, [load])
  useEffect(() => { api.get('/api/users').then((r) => setUsers(r.data)).catch(() => {}) }, [])

  const openCreate = () => { setForm(EMPTY); setDialog('create') }
  const openEdit = (row) => {
    setForm({ ...row, manager_id: row.manager_id ?? '', description: row.description ?? '', department: row.department ?? '' })
    setDialog('edit')
  }

  const save = async () => {
    const payload = {
      ...form,
      priority: Number(form.priority),
      planned_budget: Number(form.planned_budget),
      manager_id: form.manager_id === '' ? null : Number(form.manager_id),
    }
    delete payload.risk_reasons
    try {
      if (dialog === 'create') await api.post('/api/projects', payload)
      else await api.patch(`/api/projects/${form.id}`, payload)
      setDialog(null); load()
    } catch (e) { setError(readError(e, 'Could not save the project.')) }
  }

  const remove = async (row) => {
    if (!window.confirm(`Delete ${row.name}? Its deliverables, assignments and budget lines go with it.`)) return
    try { await api.delete(`/api/projects/${row.id}`); load() }
    catch (e) { setError(readError(e, 'Could not delete the project.')) }
  }

  const field = (key) => ({
    value: form[key] ?? '',
    onChange: (e) => setForm((f) => ({ ...f, [key]: e.target.value })),
  })

  return (
    <Stack spacing={3}>
      <Stack direction="row" justifyContent="space-between" alignItems="flex-end" flexWrap="wrap" gap={2}>
        <Box>
          <Typography variant="overline" sx={{ color: tokens.muted }}>Portfolio</Typography>
          <Typography variant="h1">Projects</Typography>
        </Box>
        {canEdit && <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>New project</Button>}
      </Stack>

      {error && <Alert severity="error" onClose={() => setError('')}>{error}</Alert>}

      <Paper sx={{ p: 2 }}>
        <Grid container spacing={1.5}>
          <Grid item xs={12} md={4}>
            <TextField size="small" fullWidth label="Search name, code or description"
              value={filters.search} onChange={(e) => setFilters({ ...filters, search: e.target.value })} />
          </Grid>
          <Grid item xs={6} md={2.6}>
            <TextField size="small" select fullWidth label="Status"
              value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
              <MenuItem value="">All</MenuItem>
              {STATUSES.map((s) => <MenuItem key={s} value={s}>{s.replace('_', ' ')}</MenuItem>)}
            </TextField>
          </Grid>
          <Grid item xs={6} md={2.6}>
            <TextField size="small" select fullWidth label="Department"
              value={filters.department} onChange={(e) => setFilters({ ...filters, department: e.target.value })}>
              <MenuItem value="">All</MenuItem>
              {departments.map((d) => <MenuItem key={d} value={d}>{d}</MenuItem>)}
            </TextField>
          </Grid>
          <Grid item xs={12} md={2.8}>
            <TextField size="small" select fullWidth label="Health"
              value={filters.risk} onChange={(e) => setFilters({ ...filters, risk: e.target.value })}>
              <MenuItem value="">All</MenuItem>
              <MenuItem value="on_track">On track</MenuItem>
              <MenuItem value="watch">Watch</MenuItem>
              <MenuItem value="at_risk">At risk</MenuItem>
            </TextField>
          </Grid>
        </Grid>
      </Paper>

      {rows.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h3">No projects match these filters</Typography>
          <Typography sx={{ color: tokens.muted, mt: 1 }}>Clear a filter, or create the first project.</Typography>
        </Paper>
      ) : isMobile ? (
        <Stack spacing={1.5}>
          {rows.map((p) => (
            <Paper key={p.id} sx={{ p: 2, cursor: 'pointer' }} onClick={() => navigate(`/projects/${p.id}`)}>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Typography sx={{ fontWeight: 600 }}>{p.name}</Typography>
                <RiskChip level={p.risk_level} />
              </Stack>
              <Typography variant="overline" sx={{ color: tokens.muted }}>
                {p.code} · {p.department} · {p.status.replace('_', ' ')}
              </Typography>
              <Box sx={{ mt: 1 }}><DeliveryRail timePct={p.time_elapsed_pct} donePct={p.completion_pct} /></Box>
            </Paper>
          ))}
        </Stack>
      ) : (
        <Paper>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Code</TableCell>
                <TableCell>Project</TableCell>
                <TableCell>Department</TableCell>
                <TableCell>Status</TableCell>
                <TableCell sx={{ width: 190 }}>Schedule vs delivery</TableCell>
                <TableCell align="right">Budget used</TableCell>
                <TableCell>Health</TableCell>
                {canEdit && <TableCell align="right">Actions</TableCell>}
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.map((p) => (
                <TableRow key={p.id} hover sx={{ cursor: 'pointer' }} onClick={() => navigate(`/projects/${p.id}`)}>
                  <TableCell sx={{ fontFamily: '"IBM Plex Mono", monospace', fontSize: '0.8rem' }}>{p.code}</TableCell>
                  <TableCell sx={{ fontWeight: 600, fontSize: '0.88rem' }}>{p.name}</TableCell>
                  <TableCell sx={{ fontSize: '0.85rem' }}>{p.department}</TableCell>
                  <TableCell sx={{ fontSize: '0.85rem' }}>{p.status.replace('_', ' ')}</TableCell>
                  <TableCell><DeliveryRail timePct={p.time_elapsed_pct} donePct={p.completion_pct} /></TableCell>
                  <TableCell align="right" sx={{ fontFamily: '"IBM Plex Mono", monospace', fontSize: '0.8rem' }}>
                    {p.budget_consumed_pct}%
                  </TableCell>
                  <TableCell><RiskChip level={p.risk_level} /></TableCell>
                  {canEdit && (
                    <TableCell align="right" onClick={(e) => e.stopPropagation()}>
                      <IconButton size="small" onClick={() => openEdit(p)}><EditIcon fontSize="small" /></IconButton>
                      <IconButton size="small" onClick={() => remove(p)}><DeleteIcon fontSize="small" /></IconButton>
                    </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}

      <Dialog open={Boolean(dialog)} onClose={() => setDialog(null)} fullWidth maxWidth="sm">
        <DialogTitle sx={{ fontFamily: '"Space Grotesk", sans-serif' }}>
          {dialog === 'create' ? 'New project' : 'Edit project'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 0 }}>
            <Grid item xs={12} sm={4}><TextField fullWidth label="Code" {...field('code')} /></Grid>
            <Grid item xs={12} sm={8}><TextField fullWidth label="Name" {...field('name')} /></Grid>
            <Grid item xs={12}><TextField fullWidth multiline rows={2} label="Description" {...field('description')} /></Grid>
            <Grid item xs={12} sm={6}><TextField fullWidth label="Department" {...field('department')} /></Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth select label="Status" {...field('status')}>
                {STATUSES.map((s) => <MenuItem key={s} value={s}>{s.replace('_', ' ')}</MenuItem>)}
              </TextField>
            </Grid>
            <Grid item xs={6} sm={3}><TextField fullWidth type="number" label="Priority" helperText="1 = highest" {...field('priority')} /></Grid>
            <Grid item xs={6} sm={4}><TextField fullWidth type="number" label="Planned budget" {...field('planned_budget')} /></Grid>
            <Grid item xs={12} sm={5}>
              <TextField fullWidth select label="Project manager" {...field('manager_id')}>
                <MenuItem value="">Unassigned</MenuItem>
                {users.map((u) => <MenuItem key={u.id} value={u.id}>{u.full_name}</MenuItem>)}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth type="date" label="Start date" InputLabelProps={{ shrink: true }} {...field('start_date')} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth type="date" label="End date" InputLabelProps={{ shrink: true }} {...field('end_date')} />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setDialog(null)}>Cancel</Button>
          <Button variant="contained" onClick={save}>
            {dialog === 'create' ? 'Create project' : 'Save changes'}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  )
}
