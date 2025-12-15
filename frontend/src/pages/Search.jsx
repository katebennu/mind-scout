import { useState } from 'react'
import {
  Box,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Stack,
  Link,
  Paper,
  Alert,
} from '@mui/material'
import {
  Search as SearchIcon,
  Launch,
  BarChart,
  CheckCircle,
} from '@mui/icons-material'

const API_BASE = 'http://localhost:8000/api'

export default function Search() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    setSearched(true)
    try {
      const response = await fetch(
        `${API_BASE}/search?q=${encodeURIComponent(query)}&limit=10`
      )
      const data = await response.json()
      setResults(data)
    } catch (error) {
      console.error('Error searching:', error)
    }
    setLoading(false)
  }

  const exampleQueries = [
    'attention mechanisms in deep learning',
    'computer vision transformers',
    'reinforcement learning for robotics',
    'diffusion models for image generation',
  ]

  return (
    <Box>
      <Box mb={4}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          Semantic Search
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Search for papers using natural language - find papers by meaning, not just keywords
        </Typography>
      </Box>

      {/* Search Form */}
      <Box component="form" onSubmit={handleSearch} mb={4}>
        <Stack direction="row" spacing={2}>
          <TextField
            fullWidth
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., 'attention mechanisms in transformers' or 'how to train large language models'"
            variant="outlined"
            InputProps={{
              startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
            }}
          />
          <Button
            type="submit"
            variant="contained"
            disabled={loading || !query.trim()}
            sx={{ minWidth: 120 }}
          >
            {loading ? <CircularProgress size={24} /> : 'Search'}
          </Button>
        </Stack>
      </Box>

      {/* Loading */}
      {loading && (
        <Box textAlign="center" py={12}>
          <CircularProgress />
          <Typography variant="body1" color="text.secondary" mt={2}>
            Searching...
          </Typography>
        </Box>
      )}

      {/* No Results */}
      {searched && !loading && results.length === 0 && (
        <Box textAlign="center" py={12}>
          <Alert severity="info">
            <Typography variant="body1">No results found.</Typography>
            <Typography variant="body2">Try a different search query</Typography>
          </Alert>
        </Box>
      )}

      {/* Results */}
      {!loading && results.length > 0 && (
        <Box>
          <Typography variant="body2" color="text.secondary" mb={2}>
            Found {results.length} results
          </Typography>
          <Stack spacing={2}>
            {results.map((result) => {
              const article = result.article
              return (
                <Card key={article.id} elevation={2}>
                  <CardContent>
                    <Box display="flex" alignItems="center" gap={1} mb={2}>
                      <CheckCircle color="success" fontSize="small" />
                      <Typography variant="body2" color="success.main" fontWeight="bold">
                        {Math.round(result.relevance * 100)}% relevant
                      </Typography>
                    </Box>

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
                        WebkitLineClamp: 3,
                        WebkitBoxOrient: 'vertical',
                        mb: 2
                      }}
                    >
                      {article.abstract}
                    </Typography>

                    <Box display="flex" justifyContent="space-between" alignItems="center">
                      <Stack direction="row" spacing={1} flexWrap="wrap" gap={1}>
                        <Chip
                          label={article.source}
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
                        {article.citation_count && (
                          <Chip
                            icon={<BarChart />}
                            label={`${article.citation_count} citations`}
                            size="small"
                            variant="outlined"
                          />
                        )}
                        {article.topics ? (
                          JSON.parse(article.topics).slice(0, 5).map((topic, idx) => (
                            <Chip
                              key={idx}
                              label={topic}
                              size="small"
                              color="secondary"
                              variant="outlined"
                            />
                          ))
                        ) : (
                          <Chip
                            label="Not yet processed"
                            size="small"
                            variant="outlined"
                            disabled
                          />
                        )}
                      </Stack>

                      <Link
                        href={article.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        underline="none"
                      >
                        <Button
                          endIcon={<Launch />}
                          color="primary"
                          size="small"
                        >
                          View Paper
                        </Button>
                      </Link>
                    </Box>
                  </CardContent>
                </Card>
              )
            })}
          </Stack>
        </Box>
      )}

      {/* Example queries */}
      {!searched && (
        <Paper elevation={0} sx={{ p: 3, bgcolor: 'grey.50', mt: 4 }}>
          <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
            Example queries:
          </Typography>
          <Stack spacing={1}>
            {exampleQueries.map((example) => (
              <Button
                key={example}
                onClick={() => setQuery(example)}
                sx={{ justifyContent: 'flex-start', textTransform: 'none' }}
                color="primary"
              >
                {example}
              </Button>
            ))}
          </Stack>
        </Paper>
      )}
    </Box>
  )
}
