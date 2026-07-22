import { Chip } from '@mui/material'
import { tokens } from '../theme'

const MAP = {
  on_track: { label: 'On track', colour: tokens.healthy },
  watch: { label: 'Watch', colour: tokens.watch },
  at_risk: { label: 'At risk', colour: tokens.alert },
  closed: { label: 'Closed', colour: tokens.muted },
}

export default function RiskChip({ level, size = 'small' }) {
  const item = MAP[level] || MAP.closed
  return (
    <Chip
      size={size}
      label={item.label}
      sx={{
        bgcolor: `${item.colour}14`,
        color: item.colour,
        border: `1px solid ${item.colour}44`,
        fontWeight: 600,
        fontSize: '0.72rem',
      }}
    />
  )
}
