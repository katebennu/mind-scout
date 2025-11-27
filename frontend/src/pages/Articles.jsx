import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  IconButton,
  CircularProgress,
  Pagination,
  Stack,
  Rating,
  Link,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
} from '@mui/material'
import {
  CheckCircle,
  Circle,
  Launch,
  BarChart,
} from '@mui/icons-material'

const API_BASE = 'http://localhost:8000/api'

export default function Articles() {
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const pageSize = 10

  // Filter and sort state
  const [unreadOnly, setUnreadOnly] = useState(false)
  const [sourceName, setSourceName] = useState('')
  const [sortOption, setSortOption] = useState('fetched_date_desc')
  const [sources, setSources] = useState([])

  // Fetch sources for filter dropdown
  useEffect(() => {
    const fetchSources = async () => {
      try {
        const response = await fetch(`${API_BASE}/articles/sources`)
        const data = await response.json()
        setSources(data)
      } catch (error) {
        console.error('Error fetching sources:', error)
      }
    }
    fetchSources()
  }, [])

  // Fetch articles when filters or page changes
  useEffect(() => {
    fetchArticles()
  }, [page, unreadOnly, sourceName, sortOption])

  const fetchArticles = async () => {
    setLoading(true)
    try {
      const [sortBy, sortOrder] = sortOption.split('_').length === 3
        ? [sortOption.split('_').slice(0, 2).join('_'), sortOption.split('_')[2]]
        : [sortOption.split('_')[0], sortOption.split('_')[1]]

      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
        sort_by: sortBy,
        sort_order: sortOrder,
      })

      if (unreadOnly) params.append('unread_only', 'true')
      if (sourceName) params.append('source_name', sourceName)

      const response = await fetch(`${API_BASE}/articles?${params}`)
      const data = await response.json()
      setArticles(data.articles)
      setTotal(data.total)
    } catch (error) {
      console.error('Error fetching articles:', error)
    }
    setLoading(false)
  }

  // Reset to page 1 when filters change
  const handleFilterChange = (setter) => (value) => {
    setPage(1)
    setter(value)
  }

  const handleRate = async (id, rating) => {
    try {
      await fetch(`${API_BASE}/articles/${id}/rate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating })
      })
      fetchArticles()
    } catch (error) {
      console.error('Error rating article:', error)
    }
  }

  const handleMarkRead = async (id, isRead) => {
    try {
      await fetch(`${API_BASE}/articles/${id}/read`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_read: isRead })
      })
      fetchArticles()
    } catch (error) {
      console.error('Error marking article:', error)
    }
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" py={8}>
        <CircularProgress />
      </Box>
    )
  }

  const totalPages = Math.ceil(total / pageSize)

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight="bold">
          Articles
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {total} total
        </Typography>
      </Box>

      {/* Filters and Sort Controls */}
      <Box
        display="flex"
        gap={2}
        mb={3}
        flexWrap="wrap"
        alignItems="center"
      >
        <FormControlLabel
          control={
            <Switch
              checked={unreadOnly}
              onChange={(e) => handleFilterChange(setUnreadOnly)(e.target.checked)}
              color="primary"
            />
          }
          label="Unread only"
        />

        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel>Source</InputLabel>
          <Select
            value={sourceName}
            label="Source"
            onChange={(e) => handleFilterChange(setSourceName)(e.target.value)}
          >
            <MenuItem value="">All Sources</MenuItem>
            {sources.map((src) => (
              <MenuItem key={src.source_name} value={src.source_name}>
                {src.source_name} ({src.count})
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ minWidth: 180 }}>
          <InputLabel>Sort by</InputLabel>
          <Select
            value={sortOption}
            label="Sort by"
            onChange={(e) => handleFilterChange(setSortOption)(e.target.value)}
          >
            <MenuItem value="fetched_date_desc">Recently Fetched</MenuItem>
            <MenuItem value="published_date_desc">Recently Published</MenuItem>
            <MenuItem value="published_date_asc">Oldest First</MenuItem>
            <MenuItem value="rating_desc">Highest Rated</MenuItem>
          </Select>
        </FormControl>
      </Box>

      <Stack spacing={2}>
        {articles.map((article) => (
          <Card key={article.id} elevation={2}>
            <CardContent>
              <Box display="flex" justifyContent="space-between" gap={2}>
                <Box flex={1}>
                  <Typography variant="h6" gutterBottom>
                    {article.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {article.authors}
                  </Typography>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                      mb: 2
                    }}
                  >
                    {article.abstract}
                  </Typography>
                  <Stack direction="row" spacing={1} flexWrap="wrap" gap={1}>
                    <Chip
                      label={article.source_name || article.source}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                    {article.published_date && (
                      <Chip
                        label={new Date(article.published_date).toLocaleDateString()}
                        size="small"
                        variant="outlined"
                      />
                    )}
                    {article.citation_count > 0 && (
                      <Chip
                        icon={<BarChart />}
                        label={`${article.citation_count} citations`}
                        size="small"
                        variant="outlined"
                      />
                    )}
                  </Stack>
                </Box>

                <Box display="flex" flexDirection="column" gap={1} alignItems="flex-end">
                  <Button
                    size="small"
                    variant={article.is_read ? 'contained' : 'outlined'}
                    color={article.is_read ? 'success' : 'inherit'}
                    startIcon={article.is_read ? <CheckCircle /> : <Circle />}
                    onClick={() => handleMarkRead(article.id, !article.is_read)}
                  >
                    {article.is_read ? 'Read' : 'Mark Read'}
                  </Button>

                  <Box display="flex" alignItems="center" gap={0.5}>
                    <Rating
                      value={article.rating || 0}
                      onChange={(event, newValue) => {
                        if (newValue) handleRate(article.id, newValue)
                      }}
                      size="small"
                    />
                  </Box>

                  <Link
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    underline="hover"
                  >
                    <Button
                      size="small"
                      endIcon={<Launch />}
                      color="primary"
                    >
                      View
                    </Button>
                  </Link>
                </Box>
              </Box>
            </CardContent>
          </Card>
        ))}
      </Stack>

      {totalPages > 1 && (
        <Box display="flex" justifyContent="center" mt={4}>
          <Pagination
            count={totalPages}
            page={page}
            onChange={(event, value) => setPage(value)}
            color="primary"
          />
        </Box>
      )}
    </Box>
  )
}
