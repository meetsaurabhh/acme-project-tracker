import { useEffect, useState } from 'react'
import { Link as RouterLink } from 'react-router-dom'
import { useMediaQuery } from 'react-responsive'
import {
  Alert, Box, Chip, CircularProgress, Grid, Paper, Stack, Table, TableBody,
  TableCell, TableHead, TableRow, Typography,
} from '@mui/material'
import api, { readError } from '../api'
import DeliveryRail from '../components/DeliveryRail'
import RiskChip from '../components/RiskChip'
import { tokens } from '../theme'

const money = (n) => `$${Number(n || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`

function Stat({ label, value, hint, accent }) {
  return (
    <Paper sx={{ p: 2.5, height: '100%' }}>
      <Typography variant="overline" sx={{ color: tokens.muted }}>{label}</Typography>
      <Typography sx={{ fontFamily: '"Space Grotesk", sans-serif', fontSize: '2rem', fontWeight: 700, color: accent || tokens.ink, lineHeight: 1.2 }}>
        {value}
      </Typography>
      {hint && <Typography sx={{ fontSize: '0.8rem', color: tokens.muted }}>{hint}</Typography>}
    </Paper>
  )
}

export default function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [atRisk, setAtRisk] = useState([])
  const [overAllocated, setOverAllocated] = useState([])
  const [error, setError] = useState('')
  const isMobile = useMediaQuery({ maxWidth: 900 })

  useEffect(() => {
    Promise.all([
      api.get('/api/analytics/summary'),
      api.get('/api/analytics/at-risk'),
      api.get('/api/analytics/over-allocated'),
    ])
      .then(([s, r, o]) => { setSummary(s.data); setAtRisk(r.data); setOverAllocated(o.data) })
      .catch((e) => setError(readError(e, 'Could not load the dashboard.')))
  }, [])

  if (error) return <Alert severity="error">{error}</Alert>
  if (!summary) return <Box sx={{ display: 'grid', placeItems: 'center', minHeight: 300 }}><CircularProgress /></Box>

  const burn = summary.planned_budget
    ? Math.round((summary.consumed_budget / summary.planned_budget) * 100)
    : 0

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="overline" sx={{ color: tokens.muted }}>Portfolio</Typography>
        <Typography variant="h1">Where things stand today</Typography>
      </Box>

      <Grid container spacing={2}>
        <Grid item xs={6} md={3}><Stat label="Active projects" value={summary.active_projects} hint={`${summary.total_projects} in the portfolio`} /></Grid>
        <Grid item xs={6} md={3}><Stat label="At risk" value={summary.at_risk_projects} hint="two or more warning signs" accent={tokens.alert} /></Grid>
        <Grid item xs={6} md={3}><Stat label="Overdue deliverables" value={summary.overdue_deliverables} hint={`of ${summary.total_deliverables} tracked`} accent={summary.overdue_deliverables ? tokens.watch : undefined} /></Grid>
        <Grid item xs={6} md={3}><Stat label="Budget consumed" value={`${burn}%`} hint={`${money(summary.consumed_budget)} of ${money(summary.planned_budget)}`} /></Grid>
      </Grid>

      <Paper sx={{ p: { xs: 2, md: 3 } }}>
        <Typography variant="h2" sx={{ mb: 0.5 }}>Projects needing attention</Typography>
        <Typography sx={{ color: tokens.muted, fontSize: '0.88rem', mb: 2 }}>
          The upper hairline is schedule used. The bar below it is work delivered. A gap means slippage.
        </Typography>

        {atRisk.length === 0 ? (
          <Alert severity="success">Nothing is flagged. Every active project is tracking to plan.</Alert>
        ) : isMobile ? (
          <Stack spacing={1.5}>
            {atRisk.map((p) => (
              <Paper key={p.id} component={RouterLink} to={`/projects/${p.id}`} sx={{ p: 2, textDecoration: 'none', display: 'block' }}>
                <Stack direction="row" justifyContent="space-between" alignItems="center">
                  <Typography sx={{ fontWeight: 600, color: tokens.ink }}>{p.name}</Typography>
                  <RiskChip level={p.risk_level} />
                </Stack>
                <Typography variant="overline" sx={{ color: tokens.muted }}>{p.code} · due {p.end_date}</Typography>
                <Box sx={{ mt: 1 }}><DeliveryRail timePct={p.time_elapsed_pct} donePct={p.completion_pct} /></Box>
              </Paper>
            ))}
          </Stack>
        ) : (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Project</TableCell>
                <TableCell>Due</TableCell>
                <TableCell sx={{ width: 200 }}>Schedule vs delivery</TableCell>
                <TableCell>Budget</TableCell>
                <TableCell>Why it is flagged</TableCell>
                <TableCell align="right">Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {atRisk.map((p) => (
                <TableRow key={p.id} hover component={RouterLink} to={`/projects/${p.id}`} sx={{ textDecoration: 'none', cursor: 'pointer' }}>
                  <TableCell>
                    <Typography sx={{ fontWeight: 600, fontSize: '0.9rem' }}>{p.name}</Typography>
                    <Typography variant="overline" sx={{ color: tokens.muted }}>{p.code}</Typography>
                  </TableCell>
                  <TableCell sx={{ fontFamily: '"IBM Plex Mono", monospace', fontSize: '0.8rem' }}>{p.end_date}</TableCell>
                  <TableCell><DeliveryRail timePct={p.time_elapsed_pct} donePct={p.completion_pct} /></TableCell>
                  <TableCell sx={{ fontFamily: '"IBM Plex Mono", monospace', fontSize: '0.8rem' }}>{p.budget_consumed_pct}%</TableCell>
                  <TableCell>
                    <Stack spacing={0.4}>
                      {p.risk_reasons.map((r, i) => (
                        <Typography key={i} sx={{ fontSize: '0.78rem', color: tokens.muted }}>· {r}</Typography>
                      ))}
                    </Stack>
                  </TableCell>
                  <TableCell align="right"><RiskChip level={p.risk_level} /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Paper>

      <Paper sx={{ p: { xs: 2, md: 3 } }}>
        <Typography variant="h2" sx={{ mb: 0.5 }}>People committed beyond capacity</Typography>
        <Typography sx={{ color: tokens.muted, fontSize: '0.88rem', mb: 2 }}>
          Total assignment across live projects adds up to more than a full week.
        </Typography>
        {overAllocated.length === 0 ? (
          <Alert severity="success">No one is over-committed right now.</Alert>
        ) : (
          <Stack spacing={1.2}>
            {overAllocated.map((r) => (
              <Stack key={r.resource_id} direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems={{ sm: 'center' }} sx={{ borderBottom: `1px solid ${tokens.line}`, pb: 1.2 }}>
                <Box sx={{ minWidth: 200 }}>
                  <Typography sx={{ fontWeight: 600, fontSize: '0.9rem' }}>{r.resource_name}</Typography>
                  <Typography variant="overline" sx={{ color: tokens.muted }}>{r.department}</Typography>
                </Box>
                <Chip size="small" label={`${r.total_allocation_pct}% committed`} sx={{ bgcolor: `${tokens.alert}14`, color: tokens.alert, fontWeight: 600 }} />
                <Typography sx={{ fontSize: '0.82rem', color: tokens.muted }}>
                  {r.project_count} projects: {r.projects.join(', ')}
                </Typography>
              </Stack>
            ))}
          </Stack>
        )}
      </Paper>
    </Stack>
  )
}
