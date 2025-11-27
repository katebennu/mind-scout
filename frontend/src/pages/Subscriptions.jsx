import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardActions,
  Button,
  TextField,
  CircularProgress,
  Chip,
  Stack,
  Grid,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Tabs,
  Tab,
  Tooltip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material'
import {
  Add,
  Delete,
  Refresh,
  RssFeed,
  Podcasts,
  Article,
  Newspaper,
  Email,
  Science,
} from '@mui/icons-material'

const API_BASE = 'http://localhost:8000/api'

const CATEGORY_ICONS = {
  tech_blog: <Article />,
  news: <Newspaper />,
  podcast: <Podcasts />,
  newsletter: <Email />,
  papers: <Science />,
}

const CATEGORY_COLORS = {
  tech_blog: 'primary',
  news: 'secondary',
  podcast: 'success',
  newsletter: 'warning',
  papers: 'info',
}

export default function Subscriptions() {
  const [subscriptions, setSubscriptions] = useState([])
  const [curatedFeeds, setCuratedFeeds] = useState([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [addDialogOpen, setAddDialogOpen] = useState(false)
  const [newFeedUrl, setNewFeedUrl] = useState('')
  const [newFeedTitle, setNewFeedTitle] = useState('')
  const [newFeedCategory, setNewFeedCategory] = useState('')
  const [addError, setAddError] = useState('')
  const [addLoading, setAddLoading] = useState(false)
  const [currentTab, setCurrentTab] = useState(0)
  const [curatedCategory, setCuratedCategory] = useState('all')

  useEffect(() => {
    fetchSubscriptions()
    fetchCuratedFeeds()
  }, [])

  const fetchSubscriptions = async () => {
    try {
      const response = await fetch(`${API_BASE}/subscriptions`)
      const data = await response.json()
      setSubscriptions(data)
    } catch (error) {
      console.error('Error fetching subscriptions:', error)
    }
    setLoading(false)
  }

  const fetchCuratedFeeds = async () => {
    try {
      const response = await fetch(`${API_BASE}/subscriptions/curated`)
      const data = await response.json()
      setCuratedFeeds(data)
    } catch (error) {
      console.error('Error fetching curated feeds:', error)
    }
  }

  const handleAddSubscription = async () => {
    if (!newFeedUrl.trim()) {
      setAddError('Please enter a feed URL')
      return
    }

    setAddLoading(true)
    setAddError('')

    try {
      const response = await fetch(`${API_BASE}/subscriptions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: newFeedUrl,
          title: newFeedTitle || null,
          category: newFeedCategory || null,
        })
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to add subscription')
      }

      setAddDialogOpen(false)
      setNewFeedUrl('')
      setNewFeedTitle('')
      setNewFeedCategory('')
      fetchSubscriptions()
    } catch (error) {
      setAddError(error.message)
    }
    setAddLoading(false)
  }

  const handleSubscribeToCurated = async (feed) => {
    try {
      const response = await fetch(`${API_BASE}/subscriptions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: feed.url,
          title: feed.title,
          category: feed.category,
        })
      })

      if (response.ok) {
        fetchSubscriptions()
      }
    } catch (error) {
      console.error('Error subscribing:', error)
    }
  }

  const handleDeleteSubscription = async (id) => {
    try {
      await fetch(`${API_BASE}/subscriptions/${id}`, {
        method: 'DELETE'
      })
      fetchSubscriptions()
    } catch (error) {
      console.error('Error deleting subscription:', error)
    }
  }

  const handleRefreshFeed = async (id) => {
    try {
      const response = await fetch(`${API_BASE}/subscriptions/${id}/refresh`, {
        method: 'POST'
      })
      const data = await response.json()
      if (data.new_articles > 0) {
        alert(`Found ${data.new_articles} new article(s)!`)
      } else {
        alert('No new articles found')
      }
    } catch (error) {
      console.error('Error refreshing feed:', error)
    }
  }

  const handleRefreshAll = async () => {
    setRefreshing(true)
    try {
      const response = await fetch(`${API_BASE}/subscriptions/refresh-all`, {
        method: 'POST'
      })
      const data = await response.json()
      alert(`Checked ${data.feeds_checked} feeds. Found ${data.new_articles} new article(s).`)
    } catch (error) {
      console.error('Error refreshing feeds:', error)
    }
    setRefreshing(false)
  }

  const isSubscribed = (url) => {
    return subscriptions.some(sub => sub.url === url)
  }

  const filteredCuratedFeeds = curatedCategory === 'all'
    ? curatedFeeds
    : curatedFeeds.filter(feed => feed.category === curatedCategory)

  const categories = ['all', ...new Set(curatedFeeds.map(f => f.category))]

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" py={8}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight="bold">
          Subscriptions
        </Typography>
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            startIcon={refreshing ? <CircularProgress size={20} /> : <Refresh />}
            onClick={handleRefreshAll}
            disabled={refreshing || subscriptions.length === 0}
          >
            Refresh All
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setAddDialogOpen(true)}
          >
            Add Custom Feed
          </Button>
        </Stack>
      </Box>

      <Tabs
        value={currentTab}
        onChange={(e, v) => setCurrentTab(v)}
        sx={{ mb: 3 }}
      >
        <Tab label={`My Subscriptions (${subscriptions.length})`} />
        <Tab label="Discover Feeds" />
      </Tabs>

      {currentTab === 0 && (
        <>
          {subscriptions.length === 0 ? (
            <Card>
              <CardContent>
                <Box textAlign="center" py={4}>
                  <RssFeed sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    No subscriptions yet
                  </Typography>
                  <Typography variant="body2" color="text.secondary" mb={3}>
                    Subscribe to RSS feeds to get notified about new articles
                  </Typography>
                  <Button
                    variant="contained"
                    onClick={() => setCurrentTab(1)}
                  >
                    Browse Suggested Feeds
                  </Button>
                </Box>
              </CardContent>
            </Card>
          ) : (
            <Grid container spacing={2}>
              {subscriptions.map((sub) => (
                <Grid item xs={12} md={6} lg={4} key={sub.id}>
                  <Card>
                    <CardContent>
                      <Box display="flex" alignItems="flex-start" gap={1}>
                        {CATEGORY_ICONS[sub.category] || <RssFeed />}
                        <Box flex={1}>
                          <Typography variant="subtitle1" fontWeight="bold" noWrap>
                            {sub.title || 'Untitled Feed'}
                          </Typography>
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            noWrap
                            sx={{ maxWidth: 250 }}
                          >
                            {sub.url}
                          </Typography>
                        </Box>
                      </Box>
                      <Box mt={2}>
                        {sub.category && (
                          <Chip
                            label={sub.category.replace('_', ' ')}
                            size="small"
                            color={CATEGORY_COLORS[sub.category] || 'default'}
                            sx={{ mr: 1 }}
                          />
                        )}
                        {sub.last_checked && (
                          <Typography variant="caption" color="text.secondary">
                            Last checked: {new Date(sub.last_checked).toLocaleString()}
                          </Typography>
                        )}
                      </Box>
                    </CardContent>
                    <CardActions>
                      <Tooltip title="Check for new articles">
                        <IconButton
                          size="small"
                          onClick={() => handleRefreshFeed(sub.id)}
                        >
                          <Refresh />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Unsubscribe">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDeleteSubscription(sub.id)}
                        >
                          <Delete />
                        </IconButton>
                      </Tooltip>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </>
      )}

      {currentTab === 1 && (
        <>
          <Box mb={3}>
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Category</InputLabel>
              <Select
                value={curatedCategory}
                label="Category"
                onChange={(e) => setCuratedCategory(e.target.value)}
              >
                {categories.map((cat) => (
                  <MenuItem key={cat} value={cat}>
                    {cat === 'all' ? 'All Categories' : cat.replace('_', ' ')}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          <Grid container spacing={2}>
            {filteredCuratedFeeds.map((feed, idx) => (
              <Grid item xs={12} md={6} lg={4} key={idx}>
                <Card
                  sx={{
                    opacity: isSubscribed(feed.url) ? 0.7 : 1,
                  }}
                >
                  <CardContent>
                    <Box display="flex" alignItems="flex-start" gap={1}>
                      {CATEGORY_ICONS[feed.category] || <RssFeed />}
                      <Box flex={1}>
                        <Typography variant="subtitle1" fontWeight="bold">
                          {feed.title}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {feed.description}
                        </Typography>
                      </Box>
                    </Box>
                    <Box mt={2}>
                      <Chip
                        label={feed.category.replace('_', ' ')}
                        size="small"
                        color={CATEGORY_COLORS[feed.category] || 'default'}
                      />
                    </Box>
                  </CardContent>
                  <CardActions>
                    {isSubscribed(feed.url) ? (
                      <Chip label="Subscribed" color="success" size="small" />
                    ) : (
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={<Add />}
                        onClick={() => handleSubscribeToCurated(feed)}
                      >
                        Subscribe
                      </Button>
                    )}
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        </>
      )}

      {/* Add Custom Feed Dialog */}
      <Dialog
        open={addDialogOpen}
        onClose={() => {
          setAddDialogOpen(false)
          setAddError('')
        }}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Add Custom RSS Feed</DialogTitle>
        <DialogContent>
          {addError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {addError}
            </Alert>
          )}
          <Stack spacing={2} mt={1}>
            <TextField
              label="Feed URL"
              placeholder="https://example.com/feed.xml"
              value={newFeedUrl}
              onChange={(e) => setNewFeedUrl(e.target.value)}
              fullWidth
              required
            />
            <TextField
              label="Title (optional)"
              placeholder="My Custom Feed"
              value={newFeedTitle}
              onChange={(e) => setNewFeedTitle(e.target.value)}
              fullWidth
            />
            <FormControl fullWidth>
              <InputLabel>Category (optional)</InputLabel>
              <Select
                value={newFeedCategory}
                label="Category (optional)"
                onChange={(e) => setNewFeedCategory(e.target.value)}
              >
                <MenuItem value="">None</MenuItem>
                <MenuItem value="tech_blog">Tech Blog</MenuItem>
                <MenuItem value="news">News</MenuItem>
                <MenuItem value="podcast">Podcast</MenuItem>
                <MenuItem value="newsletter">Newsletter</MenuItem>
                <MenuItem value="papers">Papers</MenuItem>
              </Select>
            </FormControl>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleAddSubscription}
            disabled={addLoading}
          >
            {addLoading ? <CircularProgress size={24} /> : 'Add Feed'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
