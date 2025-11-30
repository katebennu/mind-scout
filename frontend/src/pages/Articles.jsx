import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Checkbox,
  Chip,
  IconButton,
  CircularProgress,
  ListItemText,
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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
} from '@mui/material'
import {
  BarChart,
  CheckCircle,
  Circle,
  Download,
  Launch,
  Psychology,
  School,
  Science,
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
  const [sortOrder, setSortOrder] = useState('desc')
  const [sources, setSources] = useState([])

  // Fetch dialog state
  const [fetchDialogOpen, setFetchDialogOpen] = useState(false)
  const [fetchSource, setFetchSource] = useState(null) // 'arxiv' or 'semanticscholar'
  const [fetching, setFetching] = useState(false)
  const [fetchResult, setFetchResult] = useState(null)
  const [fetchError, setFetchError] = useState(null)

  // arXiv fetch options
  const [arxivCategories, setArxivCategories] = useState([])
  const [selectedCategories, setSelectedCategories] = useState([])
  const [arxivQuery, setArxivQuery] = useState('')
  const [arxivAuthor, setArxivAuthor] = useState('')
  const [arxivTitle, setArxivTitle] = useState('')
  const [arxivMaxResults, setArxivMaxResults] = useState(100)

  // Semantic Scholar fetch options
  const [ssQuery, setSsQuery] = useState('')
  const [ssLimit, setSsLimit] = useState(50)
  const [ssYear, setSsYear] = useState('')
  const [ssMinCitations, setSsMinCitations] = useState('')

  // Process articles state
  const [processing, setProcessing] = useState(false)

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

  // Fetch arXiv categories
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await fetch(`${API_BASE}/fetch/arxiv/categories`)
        const data = await response.json()
        setArxivCategories(data)
        // Default select all categories
        setSelectedCategories(data.map(c => c.code))
      } catch (error) {
        console.error('Error fetching arXiv categories:', error)
      }
    }
    fetchCategories()
  }, [])

  // Fetch articles when filters or page changes
  useEffect(() => {
    fetchArticles()
  }, [page, unreadOnly, sourceName, sortOrder])

  const fetchArticles = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
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

  const openFetchDialog = (source) => {
    setFetchSource(source)
    setFetchResult(null)
    setFetchError(null)
    setFetchDialogOpen(true)
  }

  const closeFetchDialog = () => {
    setFetchDialogOpen(false)
    setFetchSource(null)
    setFetchResult(null)
    setFetchError(null)
    // Reset arXiv fields
    setArxivQuery('')
    setArxivAuthor('')
    setArxivTitle('')
    // Reset Semantic Scholar fields
    setSsQuery('')
    setSsYear('')
    setSsMinCitations('')
  }

  const handleFetchArxiv = async () => {
    setFetching(true)
    setFetchError(null)
    setFetchResult(null)

    try {
      const body = {
        max_results: arxivMaxResults,
      }
      if (arxivQuery.trim()) body.query = arxivQuery.trim()
      if (selectedCategories.length > 0) body.categories = selectedCategories
      if (arxivAuthor.trim()) body.author = arxivAuthor.trim()
      if (arxivTitle.trim()) body.title = arxivTitle.trim()

      const response = await fetch(`${API_BASE}/fetch/arxiv`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to fetch from arXiv')
      }

      setFetchResult(data)
      // Refresh articles list and sources
      fetchArticles()
      const sourcesRes = await fetch(`${API_BASE}/articles/sources`)
      setSources(await sourcesRes.json())
    } catch (error) {
      setFetchError(error.message)
    }
    setFetching(false)
  }

  const handleFetchSemanticScholar = async () => {
    if (!ssQuery.trim()) {
      setFetchError('Please enter a search query')
      return
    }

    setFetching(true)
    setFetchError(null)
    setFetchResult(null)

    try {
      const body = {
        query: ssQuery.trim(),
        limit: ssLimit,
      }
      if (ssYear.trim()) body.year = ssYear.trim()
      if (ssMinCitations) body.min_citations = parseInt(ssMinCitations)

      const response = await fetch(`${API_BASE}/fetch/semanticscholar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to fetch from Semantic Scholar')
      }

      setFetchResult(data)
      // Refresh articles list and sources
      fetchArticles()
      const sourcesRes = await fetch(`${API_BASE}/articles/sources`)
      setSources(await sourcesRes.json())
    } catch (error) {
      setFetchError(error.message)
    }
    setFetching(false)
  }

  const handleProcessArticles = async () => {
    setProcessing(true)
    try {
      const response = await fetch(`${API_BASE}/fetch/process`, {
        method: 'POST'
      })
      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to process articles')
      }
      alert(data.message)
    } catch (error) {
      alert(`Error: ${error.message}`)
    }
    setProcessing(false)
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
        <Box display="flex" gap={1} alignItems="center">
          <Typography variant="body2" color="text.secondary" mr={2}>
            {total} total
          </Typography>
          <Button
            variant="outlined"
            size="small"
            startIcon={<Science />}
            onClick={() => openFetchDialog('arxiv')}
          >
            Fetch arXiv
          </Button>
          <Button
            variant="outlined"
            size="small"
            startIcon={<School />}
            onClick={() => openFetchDialog('semanticscholar')}
          >
            Fetch Semantic Scholar
          </Button>
          <Button
            variant="outlined"
            size="small"
            color="secondary"
            startIcon={processing ? <CircularProgress size={16} /> : <Psychology />}
            onClick={handleProcessArticles}
            disabled={processing}
          >
            {processing ? 'Processing...' : 'Process Articles'}
          </Button>
        </Box>
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

        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Order</InputLabel>
          <Select
            value={sortOrder}
            label="Order"
            onChange={(e) => handleFilterChange(setSortOrder)(e.target.value)}
          >
            <MenuItem value="desc">Newest First</MenuItem>
            <MenuItem value="asc">Oldest First</MenuItem>
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

      {/* Fetch Dialog */}
      <Dialog open={fetchDialogOpen} onClose={closeFetchDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {fetchSource === 'arxiv' ? 'Fetch from arXiv' : 'Fetch from Semantic Scholar'}
        </DialogTitle>
        <DialogContent>
          {fetchError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {fetchError}
            </Alert>
          )}
          {fetchResult && (
            <Alert severity="success" sx={{ mb: 2 }}>
              {fetchResult.message}
            </Alert>
          )}

          {fetchSource === 'arxiv' && (
            <Stack spacing={2}>
              <Typography variant="body2" color="text.secondary">
                Search and fetch papers from arXiv by keyword, author, or category.
              </Typography>
              <TextField
                label="Search Query"
                value={arxivQuery}
                onChange={(e) => setArxivQuery(e.target.value)}
                placeholder="e.g., transformer attention mechanism"
                fullWidth
                helperText="Optional: keywords to search in all fields"
              />
              <TextField
                label="Author"
                value={arxivAuthor}
                onChange={(e) => setArxivAuthor(e.target.value)}
                placeholder="e.g., Vaswani"
                fullWidth
                helperText="Optional: filter by author name"
              />
              <TextField
                label="Title"
                value={arxivTitle}
                onChange={(e) => setArxivTitle(e.target.value)}
                placeholder="e.g., attention is all you need"
                fullWidth
                helperText="Optional: keywords in title"
              />
              <FormControl fullWidth>
                <InputLabel>Categories</InputLabel>
                <Select
                  multiple
                  value={selectedCategories}
                  onChange={(e) => setSelectedCategories(e.target.value)}
                  label="Categories"
                  renderValue={(selected) => selected.join(', ')}
                >
                  {arxivCategories.map((cat) => (
                    <MenuItem key={cat.code} value={cat.code}>
                      <Checkbox checked={selectedCategories.includes(cat.code)} />
                      <ListItemText primary={cat.name} secondary={cat.code} />
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <TextField
                label="Max Results"
                type="number"
                value={arxivMaxResults}
                onChange={(e) => setArxivMaxResults(parseInt(e.target.value) || 100)}
                inputProps={{ min: 1, max: 500 }}
                fullWidth
              />
            </Stack>
          )}

          {fetchSource === 'semanticscholar' && (
            <Stack spacing={2}>
              <Typography variant="body2" color="text.secondary">
                Search and fetch papers from Semantic Scholar by keyword.
              </Typography>
              <TextField
                label="Search Query"
                value={ssQuery}
                onChange={(e) => setSsQuery(e.target.value)}
                placeholder="e.g., transformer attention mechanism"
                fullWidth
                required
              />
              <TextField
                label="Max Results"
                type="number"
                value={ssLimit}
                onChange={(e) => setSsLimit(parseInt(e.target.value) || 50)}
                inputProps={{ min: 1, max: 100 }}
                fullWidth
              />
              <TextField
                label="Year Filter"
                value={ssYear}
                onChange={(e) => setSsYear(e.target.value)}
                placeholder="e.g., 2024 or 2020-2024"
                fullWidth
                helperText="Optional: single year or range"
              />
              <TextField
                label="Minimum Citations"
                type="number"
                value={ssMinCitations}
                onChange={(e) => setSsMinCitations(e.target.value)}
                inputProps={{ min: 0 }}
                fullWidth
                helperText="Optional: filter by citation count"
              />
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={closeFetchDialog}>
            Close
          </Button>
          <Button
            variant="contained"
            onClick={fetchSource === 'arxiv' ? handleFetchArxiv : handleFetchSemanticScholar}
            disabled={fetching || (fetchSource === 'semanticscholar' && !ssQuery.trim())}
            startIcon={fetching ? <CircularProgress size={16} /> : <Download />}
          >
            {fetching ? 'Fetching...' : 'Fetch Papers'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
