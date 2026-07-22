import { useEffect, useState } from 'react'
import { Link as RouterLink } from 'react-router-dom'
import { useMediaQuery } from 'react-responsive'
import {
  Alert, Box, LinearProgress, Paper, Stack, Table, TableBody, TableCell,
  TableHead, TableRow, Typography,
} from '@mui/material'
import api, { readError } from '../api'
import { tokens } from '../theme'

const money = (n) => `$${Number(n || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`

export default function Budget() {
  const [rows, setRows] = useState([])
  const [error, setError] = useState('')
  const isMobile = useMediaQuery({ maxWidth: 900 })

  useEffect(() => {
    api.get('/api/analytics/budget')
      .then((r) => setRows(r.data))
      .catch((e) => setError(readError(e, 'Could not load budget figures.')))
  }, [])

  const colour = (pct) => (pct > 100 ? tokens.alert : pct > 85 ? tokens.watch : tokens.healthy)

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="overline" sx={{ color: tokens.muted }}>Finance</Typography>
        <Typography variant="h1">Planned versus consumed</Typography>
      </Box>

      {error && <Alert severity="error">{error}</Alert>}

      {isMobile ? (
        <Stack spacing={1.5}>
          {rows.map((r) => (
            <Paper key={r.project_id} sx={{ p: 2 }}>
              <Typography sx={{ fontWeight: 600 }}>{r.project_name}</Typography>
              <Typography variant="overline" sx={{ color: tokens.muted }}>{r.project_code}</Typography>
              <LinearProgress variant="determinate" value={Math.min(r.consumed_pct, 100)}
                sx={{ height: 8, borderRadius: 2, my: 1, bgcolor: tokens.line, '& .MuiLinearProgress-bar': { bgcolor: colour(r.consumed_pct) } }} />
              <Typography sx={{ fontFamily: '"IBM Plex Mono", monospace', fontSize: '0.78rem', color: tokens.muted }}>
                {money(r.consumed_budget)} of {money(r.planned_budget)} · {r.consumed_pct}%
              </Typography>
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
                <TableCell align="right">Planned</TableCell>
                <TableCell align="right">Consumed</TableCell>
                <TableCell sx={{ width: 180 }}>Burn</TableCell>
                <TableCell align="right">Remaining</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.map((r) => (
                <TableRow key={r.project_id} hover component={RouterLink} to={`/projects/${r.project_id}`} sx={{ textDecoration: 'none', cursor: 'pointer' }}>
                  <TableCell sx={{ fontFamily: '"IBM Plex Mono", monospace', fontSize: '0.8rem' }}>{r.project_code}</TableCell>
                  <TableCell sx={{ fontWeight: 600, fontSize: '0.88rem' }}>{r.project_name}</TableCell>
                  <TableCell align="right" sx={{ fontFamily: '"IBM Plex Mono", monospace', fontSize: '0.8rem' }}>{money(r.planned_budget)}</TableCell>
                  <TableCell align="right" sx={{ fontFamily: '"IBM Plex Mono", monospace', fontSize: '0.8rem' }}>{money(r.consumed_budget)}</TableCell>
                  <TableCell>
                    <LinearProgress variant="determinate" value={Math.min(r.consumed_pct, 100)}
                      sx={{ height: 8, borderRadius: 2, bgcolor: tokens.line, '& .MuiLinearProgress-bar': { bgcolor: colour(r.consumed_pct) } }} />
                    <Typography variant="overline" sx={{ color: colour(r.consumed_pct) }}>{r.consumed_pct}%</Typography>
                  </TableCell>
                  <TableCell align="right" sx={{ fontFamily: '"IBM Plex Mono", monospace', fontSize: '0.8rem', color: r.variance < 0 ? tokens.alert : tokens.ink }}>
                    {money(r.variance)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}
    </Stack>
  )
}
