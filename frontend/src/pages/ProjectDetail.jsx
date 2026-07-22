import { useCallback, useEffect, useState } from 'react'
import { useParams, Link as RouterLink } from 'react-router-dom'
import {
  Alert, Box, Button, Chip, CircularProgress, Dialog, DialogActions, DialogContent,
  DialogTitle, Divider, Grid, IconButton, MenuItem, Paper, Stack, Tab, Tabs,
  TextField, Typography,
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import DeleteIcon from '@mui/icons-material/DeleteOutline'
import EditIcon from '@mui/icons-material/EditOutlined'
import ArrowBackIcon from '@mui/icons-material/ArrowBackIosNew'
import api, { readError } from '../api'
import { useAuth } from '../auth'
import DeliveryRail from '../components/DeliveryRail'
import RiskChip from '../components/RiskChip'
import { tokens } from '../theme'

const D_STATUS = ['not_started', 'in_progress', 'blocked', 'completed']
const money = (n) => `$${Number(n || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`

export default function ProjectDetail() {
  const { id } = useParams()
  const { canEdit } = useAuth()
  const [tab, setTab] = useState(0)
  const [project, setProject] = useState(null)
  const [chain, setChain] = useState([])
  const [deliverables, setDeliverables] = useState([])
  const [allocations, setAllocations] = useState([])
  const [entries, setEntries] = useState([])
  const [resources, setResources] = useState([])
  const [dialog, setDialog] = useState(null)
  const [form, setForm] = useState({})
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    try {
      const [p, c, d, a, b, r] = await Promise.all([
        api.get(`/api/projects/${id}`),
        api.get(`/api/projects/${id}/dependency-chain`),
        api.get('/api/deliverables', { params: { project_id: id } }),
        api.get('/api/allocations', { params: { project_id: id } }),
        api.get('/api/budget-entries', { params: { project_id: id } }),
        api.get('/api/resources'),
      ])
      setProject(p.data); setChain(c.data); setDeliverables(d.data)
      setAllocations(a.data); setEntries(b.data); setResources(r.data)
    } catch (e) { setError(readError(e, 'Could not load this project.')) }
  }, [id])

  useEffect(() => { load() }, [load])

  const field = (key) => ({
    value: form[key] ?? '',
    onChange: (e) => setForm((f) => ({ ...f, [key]: e.target.value })),
  })

  const saveDeliverable = async () => {
    const payload = {
      project_id: Number(id),
      name: form.name,
      description: form.description || null,
      status: form.status || 'not_started',
      due_date: form.due_date || null,
      completion_pct: Number(form.completion_pct || 0),
      owner_id: form.owner_id ? Number(form.owner_id) : null,
      depends_on_id: form.depends_on_id ? Number(form.depends_on_id) : null,
    }
    try {
      if (form.id) await api.patch(`/api/deliverables/${form.id}`, payload)
      else await api.post('/api/deliverables', payload)
      setDialog(null); load()
    } catch (e) { setError(readError(e, 'Could not save the deliverable.')) }
  }

  const saveAllocation = async () => {
    try {
      await api.post('/api/allocations', {
        project_id: Number(id),
        resource_id: Number(form.resource_id),
        allocation_pct: Number(form.allocation_pct || 0),
        role_on_project: form.role_on_project || null,
      })
      setDialog(null); load()
    } catch (e) { setError(readError(e, 'Could not add the assignment.')) }
  }

  const saveEntry = async () => {
    try {
      await api.post('/api/budget-entries', {
        project_id: Number(id),
        category: form.category || 'general',
        amount: Number(form.amount || 0),
        entry_date: form.entry_date,
        description: form.description || null,
      })
      setDialog(null); load()
    } catch (e) { setError(readError(e, 'Could not record the spend.')) }
  }

  const del = async (path, label) => {
    if (!window.confirm(`Delete ${label}?`)) return
    try { await api.delete(path); load() } catch (e) { setError(readError(e)) }
  }

  if (error && !project) return <Alert severity="error">{error}</Alert>
  if (!project) return <Box sx={{ display: 'grid', placeItems: 'center', minHeight: 300 }}><CircularProgress /></Box>

  return (
    <Stack spacing={3}>
      <Button component={RouterLink} to="/projects" startIcon={<ArrowBackIcon sx={{ fontSize: 12 }} />} sx={{ alignSelf: 'flex-start', color: tokens.muted }}>
        All projects
      </Button>

      {error && <Alert severity="error" onClose={() => setError('')}>{error}</Alert>}

      <Paper sx={{ p: { xs: 2, md: 3 } }}>
        <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" gap={2}>
          <Box>
            <Typography variant="overline" sx={{ color: tokens.muted }}>{project.code} · {project.department}</Typography>
            <Typography variant="h1">{project.name}</Typography>
            <Typography sx={{ color: tokens.muted, mt: 1, maxWidth: 640 }}>{project.description}</Typography>
          </Box>
          <Stack spacing={1} alignItems={{ md: 'flex-end' }}>
            <RiskChip level={project.risk_level} size="medium" />
            <Typography variant="overline" sx={{ color: tokens.muted }}>
              {project.start_date} → {project.end_date}
            </Typography>
            <Typography variant="overline" sx={{ color: tokens.muted }}>
              Manager: {project.manager_name || 'unassigned'}
            </Typography>
          </Stack>
        </Stack>

        <Divider sx={{ my: 2.5 }} />

        <Grid container spacing={3}>
          <Grid item xs={12} md={5}>
            <Typography variant="overline" sx={{ color: tokens.muted }}>Schedule vs delivery</Typography>
            <Box sx={{ mt: 0.5 }}><DeliveryRail timePct={project.time_elapsed_pct} donePct={project.completion_pct} height={12} /></Box>
          </Grid>
          <Grid item xs={6} md={2}>
            <Typography variant="overline" sx={{ color: tokens.muted }}>Delivered</Typography>
            <Typography sx={{ fontFamily: '"Space Grotesk", sans-serif', fontSize: '1.5rem', fontWeight: 700 }}>{project.completion_pct}%</Typography>
          </Grid>
          <Grid item xs={6} md={2}>
            <Typography variant="overline" sx={{ color: tokens.muted }}>Budget used</Typography>
            <Typography sx={{ fontFamily: '"Space Grotesk", sans-serif', fontSize: '1.5rem', fontWeight: 700 }}>{project.budget_consumed_pct}%</Typography>
            <Typography sx={{ fontSize: '0.75rem', color: tokens.muted }}>{money(project.budget_consumed)} of {money(project.planned_budget)}</Typography>
          </Grid>
          <Grid item xs={12} md={3}>
            <Typography variant="overline" sx={{ color: tokens.muted }}>Flags</Typography>
            {project.risk_reasons.length === 0
              ? <Typography sx={{ fontSize: '0.85rem', color: tokens.healthy }}>None. Tracking to plan.</Typography>
              : project.risk_reasons.map((r, i) => (
                  <Typography key={i} sx={{ fontSize: '0.8rem', color: tokens.muted }}>· {r}</Typography>
                ))}
          </Grid>
        </Grid>
      </Paper>

      <Paper>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ borderBottom: `1px solid ${tokens.line}`, px: 1 }} variant="scrollable">
          <Tab label={`Dependency chain (${chain.length})`} />
          <Tab label={`Deliverables (${deliverables.length})`} />
          <Tab label={`Team (${allocations.length})`} />
          <Tab label={`Spend (${entries.length})`} />
        </Tabs>

        <Box sx={{ p: { xs: 2, md: 3 } }}>
          {tab === 0 && (
            <Stack spacing={1}>
              <Typography sx={{ color: tokens.muted, fontSize: '0.88rem', mb: 1 }}>
                Each step is indented under the item it waits on. Amber means the item it depends on is not finished yet.
              </Typography>
              {chain.length === 0 && <Alert severity="info">No deliverables yet. Add one on the next tab.</Alert>}
              {chain.map((n) => (
                <Stack key={n.id} direction="row" alignItems="center" spacing={1.5}
                  sx={{ ml: `${n.depth * 24}px`, p: 1.2, border: `1px solid ${tokens.line}`, borderLeft: `3px solid ${n.blocked_by_incomplete ? tokens.watch : tokens.healthy}`, borderRadius: 1 }}>
                  <Box sx={{ flex: 1 }}>
                    <Typography sx={{ fontWeight: 600, fontSize: '0.88rem' }}>{n.name}</Typography>
                    <Typography variant="overline" sx={{ color: tokens.muted }}>
                      {n.status.replace('_', ' ')} · {n.completion_pct}% · due {n.due_date || 'not set'}
                    </Typography>
                  </Box>
                  {n.blocked_by_incomplete && <Chip size="small" label="Waiting on predecessor" sx={{ bgcolor: `${tokens.watch}14`, color: tokens.watch }} />}
                </Stack>
              ))}
            </Stack>
          )}

          {tab === 1 && (
            <Stack spacing={1.2}>
              {canEdit && (
                <Button startIcon={<AddIcon />} variant="outlined" sx={{ alignSelf: 'flex-start', mb: 1 }}
                  onClick={() => { setForm({ status: 'not_started', completion_pct: 0 }); setDialog('deliverable') }}>
                  Add deliverable
                </Button>
              )}
              {deliverables.map((d) => (
                <Stack key={d.id} direction="row" alignItems="center" spacing={1.5} sx={{ borderBottom: `1px solid ${tokens.line}`, pb: 1.2 }}>
                  <Box sx={{ flex: 1 }}>
                    <Typography sx={{ fontWeight: 600, fontSize: '0.88rem' }}>{d.name}</Typography>
                    <Typography variant="overline" sx={{ color: d.is_overdue ? tokens.alert : tokens.muted }}>
                      {d.status.replace('_', ' ')} · {d.completion_pct}% · {d.owner_name || 'no owner'} · due {d.due_date || 'not set'}
                      {d.depends_on_name ? ` · after ${d.depends_on_name}` : ''}
                    </Typography>
                  </Box>
                  {canEdit && (
                    <>
                      <IconButton size="small" onClick={() => { setForm({ ...d, owner_id: d.owner_id ?? '', depends_on_id: d.depends_on_id ?? '', due_date: d.due_date ?? '' }); setDialog('deliverable') }}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton size="small" onClick={() => del(`/api/deliverables/${d.id}`, d.name)}>
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </>
                  )}
                </Stack>
              ))}
            </Stack>
          )}

          {tab === 2 && (
            <Stack spacing={1.2}>
              {canEdit && (
                <Button startIcon={<AddIcon />} variant="outlined" sx={{ alignSelf: 'flex-start', mb: 1 }}
                  onClick={() => { setForm({ allocation_pct: 50 }); setDialog('allocation') }}>
                  Assign someone
                </Button>
              )}
              {allocations.length === 0 && <Alert severity="info">Nobody is assigned to this project yet.</Alert>}
              {allocations.map((a) => (
                <Stack key={a.id} direction="row" alignItems="center" spacing={1.5} sx={{ borderBottom: `1px solid ${tokens.line}`, pb: 1.2 }}>
                  <Box sx={{ flex: 1 }}>
                    <Typography sx={{ fontWeight: 600, fontSize: '0.88rem' }}>{a.resource_name}</Typography>
                    <Typography variant="overline" sx={{ color: tokens.muted }}>{a.role_on_project || 'role not set'}</Typography>
                  </Box>
                  <Chip size="small" label={`${a.allocation_pct}%`} />
                  {canEdit && <IconButton size="small" onClick={() => del(`/api/allocations/${a.id}`, `${a.resource_name}'s assignment`)}><DeleteIcon fontSize="small" /></IconButton>}
                </Stack>
              ))}
            </Stack>
          )}

          {tab === 3 && (
            <Stack spacing={1.2}>
              {canEdit && (
                <Button startIcon={<AddIcon />} variant="outlined" sx={{ alignSelf: 'flex-start', mb: 1 }}
                  onClick={() => { setForm({ category: 'labour', entry_date: new Date().toISOString().slice(0, 10) }); setDialog('entry') }}>
                  Record spend
                </Button>
              )}
              {entries.length === 0 && <Alert severity="info">No spend recorded against this project yet.</Alert>}
              {entries.map((e) => (
                <Stack key={e.id} direction="row" alignItems="center" spacing={1.5} sx={{ borderBottom: `1px solid ${tokens.line}`, pb: 1.2 }}>
                  <Box sx={{ flex: 1 }}>
                    <Typography sx={{ fontWeight: 600, fontSize: '0.88rem' }}>{money(e.amount)} · {e.category}</Typography>
                    <Typography variant="overline" sx={{ color: tokens.muted }}>{e.entry_date} · {e.description || 'no note'}</Typography>
                  </Box>
                  {canEdit && <IconButton size="small" onClick={() => del(`/api/budget-entries/${e.id}`, 'this spend line')}><DeleteIcon fontSize="small" /></IconButton>}
                </Stack>
              ))}
            </Stack>
          )}
        </Box>
      </Paper>

      {/* ---------- dialogs ---------- */}
      <Dialog open={dialog === 'deliverable'} onClose={() => setDialog(null)} fullWidth maxWidth="sm">
        <DialogTitle sx={{ fontFamily: '"Space Grotesk", sans-serif' }}>{form.id ? 'Edit deliverable' : 'Add deliverable'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 0 }}>
            <Grid item xs={12}><TextField fullWidth label="Name" {...field('name')} /></Grid>
            <Grid item xs={12}><TextField fullWidth multiline rows={2} label="Description" {...field('description')} /></Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth select label="Status" {...field('status')}>
                {D_STATUS.map((s) => <MenuItem key={s} value={s}>{s.replace('_', ' ')}</MenuItem>)}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6}><TextField fullWidth type="number" label="Percent complete" {...field('completion_pct')} /></Grid>
            <Grid item xs={12} sm={6}><TextField fullWidth type="date" label="Due date" InputLabelProps={{ shrink: true }} {...field('due_date')} /></Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth select label="Owner" {...field('owner_id')}>
                <MenuItem value="">Unassigned</MenuItem>
                {resources.map((r) => <MenuItem key={r.id} value={r.id}>{r.full_name}</MenuItem>)}
              </TextField>
            </Grid>
            <Grid item xs={12}>
              <TextField fullWidth select label="Starts after" helperText="Builds the dependency chain" {...field('depends_on_id')}>
                <MenuItem value="">Nothing. It can start immediately.</MenuItem>
                {deliverables.filter((d) => d.id !== form.id).map((d) => <MenuItem key={d.id} value={d.id}>{d.name}</MenuItem>)}
              </TextField>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setDialog(null)}>Cancel</Button>
          <Button variant="contained" onClick={saveDeliverable}>Save deliverable</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={dialog === 'allocation'} onClose={() => setDialog(null)} fullWidth maxWidth="xs">
        <DialogTitle sx={{ fontFamily: '"Space Grotesk", sans-serif' }}>Assign someone</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField select fullWidth label="Person" {...field('resource_id')}>
              {resources.map((r) => <MenuItem key={r.id} value={r.id}>{r.full_name} — {r.job_title}</MenuItem>)}
            </TextField>
            <TextField fullWidth type="number" label="Share of their week (%)" {...field('allocation_pct')} />
            <TextField fullWidth label="Role on this project" {...field('role_on_project')} />
          </Stack>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setDialog(null)}>Cancel</Button>
          <Button variant="contained" onClick={saveAllocation}>Assign</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={dialog === 'entry'} onClose={() => setDialog(null)} fullWidth maxWidth="xs">
        <DialogTitle sx={{ fontFamily: '"Space Grotesk", sans-serif' }}>Record spend</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField fullWidth type="number" label="Amount" {...field('amount')} />
            <TextField fullWidth label="Category" {...field('category')} />
            <TextField fullWidth type="date" label="Date" InputLabelProps={{ shrink: true }} {...field('entry_date')} />
            <TextField fullWidth label="Note" {...field('description')} />
          </Stack>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setDialog(null)}>Cancel</Button>
          <Button variant="contained" onClick={saveEntry}>Record spend</Button>
        </DialogActions>
      </Dialog>
    </Stack>
  )
}
