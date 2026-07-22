import { Box, Tooltip, Typography } from '@mui/material'
import { tokens } from '../theme'

/**
 * The signature element of this app.
 *
 * Two stacked tracks on the same scale: how much of the schedule has been
 * used (top, hairline) and how much has actually been delivered (bottom,
 * filled). The gap between the two marks IS the slippage, so a project in
 * trouble is visible without reading a single number.
 */
export default function DeliveryRail({ timePct = 0, donePct = 0, height = 8 }) {
  const slip = Math.round(timePct - donePct)
  const colour = slip >= 20 ? tokens.alert : slip >= 10 ? tokens.watch : tokens.healthy

  return (
    <Tooltip
      title={`${Math.round(timePct)}% of schedule used, ${Math.round(donePct)}% delivered`}
      arrow
    >
      <Box sx={{ width: '100%', minWidth: 120 }}>
        <Box sx={{ position: 'relative', height: 3, bgcolor: tokens.line, borderRadius: 2 }}>
          <Box
            sx={{
              position: 'absolute', inset: 0, width: `${Math.min(timePct, 100)}%`,
              bgcolor: tokens.muted, borderRadius: 2,
            }}
          />
        </Box>
        <Box sx={{ position: 'relative', height, bgcolor: tokens.line, borderRadius: 2, mt: '3px' }}>
          <Box
            sx={{
              position: 'absolute', inset: 0, width: `${Math.min(donePct, 100)}%`,
              bgcolor: colour, borderRadius: 2, transition: 'width .4s ease',
            }}
          />
        </Box>
        <Typography
          variant="overline"
          sx={{ color: slip > 0 ? colour : tokens.muted, lineHeight: 1.6 }}
        >
          {slip > 0 ? `${slip} pts behind` : 'on pace'}
        </Typography>
      </Box>
    </Tooltip>
  )
}
