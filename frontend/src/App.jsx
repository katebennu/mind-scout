import { useState, useEffect } from 'react'
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  Tabs,
  Tab,
  ThemeProvider,
  createTheme,
  CssBaseline,
  IconButton,
  Badge,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from '@mui/material'
import {
  LibraryBooks,
  Recommend,
  Search as SearchIcon,
  Settings,
  Notifications as NotificationsIcon,
  RssFeed,
  OpenInNew,
  DoneAll,
} from '@mui/icons-material'
import Articles from './pages/Articles'
import Recommendations from './pages/Recommendations'
import Profile from './pages/Profile'
import Search from './pages/Search'
import Subscriptions from './pages/Subscriptions'
import Notifications from './pages/Notifications'

const API_BASE = 'http://localhost:8000/api'

const theme = createTheme({
  palette: {
    primary: {
      main: '#6366f1', // Indigo
    },
    secondary: {
      main: '#8b5cf6', // Purple
    },
  },
})

function App() {
  const [currentTab, setCurrentTab] = useState(0)
  const [notificationCount, setNotificationCount] = useState(0)
  const [recentNotifications, setRecentNotifications] = useState([])
  const [notificationMenuAnchor, setNotificationMenuAnchor] = useState(null)

  useEffect(() => {
    fetchNotificationCount()
    // Poll for notifications every 30 seconds
    const interval = setInterval(fetchNotificationCount, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchNotificationCount = async () => {
    try {
      const response = await fetch(`${API_BASE}/notifications/count`)
      const data = await response.json()
      setNotificationCount(data.unread)

      // Also fetch recent notifications for the dropdown
      const notifResponse = await fetch(`${API_BASE}/notifications?unread_only=true&limit=5`)
      const notifData = await notifResponse.json()
      setRecentNotifications(notifData)
    } catch (error) {
      console.error('Error fetching notifications:', error)
    }
  }

  const handleNotificationClick = (event) => {
    setNotificationMenuAnchor(event.currentTarget)
  }

  const handleNotificationClose = () => {
    setNotificationMenuAnchor(null)
  }

  const handleMarkAllRead = async () => {
    try {
      await fetch(`${API_BASE}/notifications/read-all`, {
        method: 'POST'
      })
      fetchNotificationCount()
    } catch (error) {
      console.error('Error marking all read:', error)
    }
    handleNotificationClose()
  }

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue)
  }

  const tabs = [
    { label: 'Articles', icon: <LibraryBooks />, component: <Articles /> },
    { label: 'Recommendations', icon: <Recommend />, component: <Recommendations /> },
    { label: 'Search', icon: <SearchIcon />, component: <Search /> },
    { label: 'Subscriptions', icon: <RssFeed />, component: <Subscriptions /> },
    { label: 'Notifications', icon: <NotificationsIcon />, component: <Notifications /> },
    { label: 'Profile', icon: <Settings />, component: <Profile /> },
  ]

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ flexGrow: 1, bgcolor: 'grey.50', minHeight: '100vh' }}>
        {/* Header */}
        <AppBar position="static" color="default" elevation={1}>
          <Toolbar>
            <Typography
              variant="h5"
              component="h1"
              sx={{ flexGrow: 1, fontWeight: 'bold' }}
            >
              Mind Scout
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mr: 2 }}>
              AI Research Assistant
            </Typography>
            <IconButton
              color="inherit"
              onClick={handleNotificationClick}
              aria-label={`${notificationCount} new notifications`}
            >
              <Badge badgeContent={notificationCount} color="error">
                <NotificationsIcon />
              </Badge>
            </IconButton>
            <Menu
              anchorEl={notificationMenuAnchor}
              open={Boolean(notificationMenuAnchor)}
              onClose={handleNotificationClose}
              PaperProps={{
                sx: { width: 360, maxHeight: 400 }
              }}
            >
              {recentNotifications.length === 0 ? (
                <MenuItem disabled>
                  <ListItemText primary="No new notifications" />
                </MenuItem>
              ) : (
                <>
                  {recentNotifications.map((notif) => (
                    <MenuItem
                      key={notif.id}
                      onClick={() => {
                        window.open(notif.article.url, '_blank')
                        handleNotificationClose()
                      }}
                      sx={{ whiteSpace: 'normal' }}
                    >
                      <ListItemIcon>
                        <RssFeed fontSize="small" />
                      </ListItemIcon>
                      <ListItemText
                        primary={notif.article.title}
                        secondary={notif.feed?.title || notif.article.source}
                        primaryTypographyProps={{
                          noWrap: true,
                          sx: { maxWidth: 250 }
                        }}
                      />
                      <OpenInNew fontSize="small" color="action" />
                    </MenuItem>
                  ))}
                  <Divider />
                  <MenuItem onClick={handleMarkAllRead}>
                    <ListItemIcon>
                      <DoneAll fontSize="small" />
                    </ListItemIcon>
                    <ListItemText primary="Mark all as read" />
                  </MenuItem>
                  <MenuItem onClick={() => {
                    setCurrentTab(4) // Notifications tab index
                    handleNotificationClose()
                  }}>
                    <ListItemText primary="View all notifications" sx={{ textAlign: 'center' }} />
                  </MenuItem>
                </>
              )}
            </Menu>
          </Toolbar>
        </AppBar>

        {/* Navigation Tabs */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider', bgcolor: 'background.paper' }}>
          <Container maxWidth="lg">
            <Tabs
              value={currentTab}
              onChange={handleTabChange}
              aria-label="navigation tabs"
            >
              {tabs.map((tab, index) => (
                <Tab
                  key={index}
                  label={tab.label}
                  icon={tab.icon}
                  iconPosition="start"
                />
              ))}
            </Tabs>
          </Container>
        </Box>

        {/* Main Content */}
        <Container maxWidth="lg" sx={{ py: 4 }}>
          {tabs[currentTab].component}
        </Container>
      </Box>
    </ThemeProvider>
  )
}

export default App
