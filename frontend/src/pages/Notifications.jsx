import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardActionArea,
  Button,
  CircularProgress,
  Chip,
  Stack,
  IconButton,
  Divider,
  Alert,
} from '@mui/material'
import {
  CheckCircle,
  Delete,
  OpenInNew,
  RssFeed,
  DoneAll,
  DeleteSweep,
  Star,
} from '@mui/icons-material'

const API_BASE = 'http://localhost:8000/api'

export default function Notifications() {
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(true)
  const [showUnreadOnly, setShowUnreadOnly] = useState(false)

  useEffect(() => {
    fetchNotifications()
  }, [showUnreadOnly])

  const fetchNotifications = async () => {
    try {
      const params = new URLSearchParams()
      if (showUnreadOnly) params.append('unread_only', 'true')
      params.append('limit', '100')

      const response = await fetch(`${API_BASE}/notifications?${params}`)
      const data = await response.json()
      setNotifications(data)
    } catch (error) {
      console.error('Error fetching notifications:', error)
    }
    setLoading(false)
  }

  const handleMarkRead = async (id) => {
    try {
      await fetch(`${API_BASE}/notifications/${id}/read`, {
        method: 'POST'
      })
      // Update local state
      setNotifications(notifications.map(n =>
        n.id === id ? { ...n, is_read: true, read_date: new Date().toISOString() } : n
      ))
    } catch (error) {
      console.error('Error marking notification read:', error)
    }
  }

  const handleMarkAllRead = async () => {
    try {
      await fetch(`${API_BASE}/notifications/read-all`, {
        method: 'POST'
      })
      fetchNotifications()
    } catch (error) {
      console.error('Error marking all read:', error)
    }
  }

  const handleDelete = async (id) => {
    try {
      await fetch(`${API_BASE}/notifications/${id}`, {
        method: 'DELETE'
      })
      setNotifications(notifications.filter(n => n.id !== id))
    } catch (error) {
      console.error('Error deleting notification:', error)
    }
  }

  const handleClearRead = async () => {
    try {
      await fetch(`${API_BASE}/notifications?read_only=true`, {
        method: 'DELETE'
      })
      fetchNotifications()
    } catch (error) {
      console.error('Error clearing notifications:', error)
    }
  }

  const unreadCount = notifications.filter(n => !n.is_read).length

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
        <Box>
          <Typography variant="h4" fontWeight="bold">
            Notifications
          </Typography>
          {unreadCount > 0 && (
            <Typography variant="body2" color="text.secondary">
              {unreadCount} unread notification{unreadCount !== 1 ? 's' : ''}
            </Typography>
          )}
        </Box>
        <Stack direction="row" spacing={1}>
          <Button
            size="small"
            variant={showUnreadOnly ? "contained" : "outlined"}
            onClick={() => setShowUnreadOnly(!showUnreadOnly)}
          >
            {showUnreadOnly ? 'Show All' : 'Unread Only'}
          </Button>
          {unreadCount > 0 && (
            <Button
              size="small"
              startIcon={<DoneAll />}
              onClick={handleMarkAllRead}
            >
              Mark All Read
            </Button>
          )}
          <Button
            size="small"
            color="error"
            startIcon={<DeleteSweep />}
            onClick={handleClearRead}
          >
            Clear Read
          </Button>
        </Stack>
      </Box>

      {notifications.length === 0 ? (
        <Card>
          <CardContent>
            <Box textAlign="center" py={4}>
              <CheckCircle sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                {showUnreadOnly ? 'No unread notifications' : 'No notifications yet'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {showUnreadOnly
                  ? "You're all caught up!"
                  : 'Subscribe to feeds and refresh them to get notifications about new articles'
                }
              </Typography>
            </Box>
          </CardContent>
        </Card>
      ) : (
        <Stack spacing={1}>
          {notifications.map((notification) => (
            <Card
              key={notification.id}
              sx={{
                bgcolor: notification.is_read ? 'grey.50' : 'background.paper',
                borderLeft: notification.is_read ? 'none' : '4px solid',
                borderLeftColor: notification.type === 'interest_match' ? 'warning.main' : 'primary.main',
              }}
            >
              <CardContent sx={{ py: 2 }}>
                <Box display="flex" alignItems="flex-start" gap={2}>
                  {notification.type === 'interest_match' ? (
                    <Star color={notification.is_read ? 'disabled' : 'warning'} />
                  ) : (
                    <RssFeed color={notification.is_read ? 'disabled' : 'primary'} />
                  )}
                  <Box flex={1}>
                    <Typography
                      variant="subtitle1"
                      fontWeight={notification.is_read ? 'normal' : 'bold'}
                      sx={{
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden',
                      }}
                    >
                      {notification.article.title}
                    </Typography>
                    <Stack direction="row" spacing={1} alignItems="center" mt={1} flexWrap="wrap">
                      {notification.type === 'interest_match' && (
                        <Chip
                          label="Matches your interests"
                          size="small"
                          color="warning"
                          variant="filled"
                        />
                      )}
                      <Chip
                        label={notification.article.source}
                        size="small"
                        variant="outlined"
                      />
                      {notification.feed && (
                        <Typography variant="caption" color="text.secondary">
                          from {notification.feed.title || 'feed'}
                        </Typography>
                      )}
                      <Typography variant="caption" color="text.secondary">
                        {new Date(notification.created_date).toLocaleString()}
                      </Typography>
                    </Stack>
                  </Box>
                  <Stack direction="row" spacing={0.5}>
                    {!notification.is_read && (
                      <IconButton
                        size="small"
                        onClick={() => handleMarkRead(notification.id)}
                        title="Mark as read"
                      >
                        <CheckCircle fontSize="small" />
                      </IconButton>
                    )}
                    <IconButton
                      size="small"
                      href={notification.article.url}
                      target="_blank"
                      title="Open article"
                    >
                      <OpenInNew fontSize="small" />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleDelete(notification.id)}
                      title="Delete"
                    >
                      <Delete fontSize="small" />
                    </IconButton>
                  </Stack>
                </Box>
              </CardContent>
            </Card>
          ))}
        </Stack>
      )}
    </Box>
  )
}
