import { useState } from 'react'
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
  CssBaseline
} from '@mui/material'
import {
  LibraryBooks,
  Recommend,
  Search as SearchIcon,
  Settings
} from '@mui/icons-material'
import Articles from './pages/Articles'
import Recommendations from './pages/Recommendations'
import Profile from './pages/Profile'
import Search from './pages/Search'

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

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue)
  }

  const tabs = [
    { label: 'Articles', icon: <LibraryBooks />, component: <Articles /> },
    { label: 'Recommendations', icon: <Recommend />, component: <Recommendations /> },
    { label: 'Search', icon: <SearchIcon />, component: <Search /> },
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
              🧠 Mind Scout
            </Typography>
            <Typography variant="body2" color="text.secondary">
              AI Research Assistant
            </Typography>
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
