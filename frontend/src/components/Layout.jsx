import { useState } from 'react'
import { Link as RouterLink, useLocation, useNavigate } from 'react-router-dom'
import { useMediaQuery } from 'react-responsive'
import {
  AppBar, Box, Button, Divider, Drawer, IconButton, List, ListItemButton,
  ListItemIcon, ListItemText, Toolbar, Typography,
} from '@mui/material'
import MenuIcon from '@mui/icons-material/Menu'
import DashboardIcon from '@mui/icons-material/SpaceDashboardOutlined'
import FolderIcon from '@mui/icons-material/FolderOpenOutlined'
import PeopleIcon from '@mui/icons-material/GroupsOutlined'
import PaidIcon from '@mui/icons-material/PaidOutlined'
import BadgeIcon from '@mui/icons-material/BadgeOutlined'
import LogoutIcon from '@mui/icons-material/LogoutOutlined'
import { useAuth } from '../auth'
import { tokens } from '../theme'

const WIDTH = 236

export default function Layout({ children }) {
  const { user, logout, isAdmin } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const isMobile = useMediaQuery({ maxWidth: 900 })
  const [open, setOpen] = useState(false)

  const nav = [
    { to: '/', label: 'Dashboard', icon: <DashboardIcon fontSize="small" /> },
    { to: '/projects', label: 'Projects', icon: <FolderIcon fontSize="small" /> },
    { to: '/resources', label: 'People', icon: <PeopleIcon fontSize="small" /> },
    { to: '/budget', label: 'Budget', icon: <PaidIcon fontSize="small" /> },
    ...(isAdmin ? [{ to: '/users', label: 'Accounts', icon: <BadgeIcon fontSize="small" /> }] : []),
  ]

  const menu = (
    <Box sx={{ width: WIDTH, height: '100%', bgcolor: tokens.ink, color: '#fff', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ px: 2.5, py: 3 }}>
        <Typography variant="overline" sx={{ color: '#7FA8BF' }}>ACME Inc.</Typography>
        <Typography variant="h3" sx={{ color: '#fff', mt: 0.5 }}>Project Tracker</Typography>
      </Box>
      <Divider sx={{ borderColor: '#1E3346' }} />
      <List sx={{ px: 1.2, py: 1.5, flex: 1 }}>
        {nav.map((item) => {
          const active = location.pathname === item.to ||
            (item.to !== '/' && location.pathname.startsWith(item.to))
          return (
            <ListItemButton
              key={item.to}
              component={RouterLink}
              to={item.to}
              onClick={() => setOpen(false)}
              sx={{
                borderRadius: 1, mb: 0.4, color: active ? '#fff' : '#9DB4C4',
                bgcolor: active ? '#1E3346' : 'transparent',
                '&:hover': { bgcolor: '#1A2C3D' },
              }}
            >
              <ListItemIcon sx={{ minWidth: 34, color: 'inherit' }}>{item.icon}</ListItemIcon>
              <ListItemText primaryTypographyProps={{ fontSize: '0.9rem', fontWeight: active ? 600 : 400 }} primary={item.label} />
            </ListItemButton>
          )
        })}
      </List>
      <Divider sx={{ borderColor: '#1E3346' }} />
      <Box sx={{ p: 2 }}>
        <Typography sx={{ fontSize: '0.85rem', fontWeight: 600 }}>{user?.full_name}</Typography>
        <Typography variant="overline" sx={{ color: '#7FA8BF' }}>{user?.role}</Typography>
        <Button
          fullWidth size="small" startIcon={<LogoutIcon fontSize="small" />}
          sx={{ mt: 1.5, color: '#9DB4C4', justifyContent: 'flex-start' }}
          onClick={() => { logout(); navigate('/login') }}
        >
          Sign out
        </Button>
      </Box>
    </Box>
  )

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {isMobile ? (
        <>
          <AppBar position="fixed" elevation={0} sx={{ bgcolor: tokens.ink }}>
            <Toolbar variant="dense">
              <IconButton edge="start" color="inherit" onClick={() => setOpen(true)}>
                <MenuIcon />
              </IconButton>
              <Typography variant="h3" sx={{ ml: 1, fontSize: '1rem' }}>Project Tracker</Typography>
            </Toolbar>
          </AppBar>
          <Drawer open={open} onClose={() => setOpen(false)}>{menu}</Drawer>
        </>
      ) : (
        <Drawer
          variant="permanent"
          sx={{ width: WIDTH, flexShrink: 0, '& .MuiDrawer-paper': { width: WIDTH, border: 0 } }}
        >
          {menu}
        </Drawer>
      )}
      <Box component="main" sx={{ flexGrow: 1, p: { xs: 2, md: 4 }, pt: { xs: 8, md: 4 }, maxWidth: '100%', overflowX: 'hidden' }}>
        {children}
      </Box>
    </Box>
  )
}
