import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Stack,
  Link,
  Button,
  Alert,
  AlertTitle,
} from '@mui/material'
import {
  TrendingUp,
  BarChart,
  Launch,
} from '@mui/icons-material'

const API_BASE = 'http://localhost:8000/api'

export default function Recommendations() {
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchRecommendations()
  }, [])

  const fetchRecommendations = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE}/recommendations?limit=10`)
      const data = await response.json()
      setRecommendations(data)
    } catch (error) {
      console.error('Error fetching recommendations:', error)
    }
    setLoading(false)
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" py={8}>
        <CircularProgress />
      </Box>
    )
  }

  if (recommendations.length === 0) {
    return (
      <Box textAlign="center" py={12}>
        <Alert severity="info">
          <AlertTitle>No recommendations available</AlertTitle>
          Set your interests in the Profile page to get personalized recommendations!
        </Alert>
      </Box>
    )
  }

  return (
    <Box>
      <Box mb={4}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          Personalized Recommendations
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Papers recommended based on your interests and reading history
        </Typography>
      </Box>

      <Stack spacing={2}>
        {recommendations.map((rec) => {
          const article = rec.article
          return (
            <Card
              key={article.id}
              elevation={2}
              sx={{
                borderLeft: 4,
                borderColor: 'primary.main',
              }}
            >
              <CardContent>
                <Box display="flex" alignItems="center" gap={2} mb={2}>
                  <TrendingUp color="primary" />
                  <Typography variant="h6" color="primary.main" fontWeight="bold">
                    {Math.round(rec.score * 100)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    match
                  </Typography>
                </Box>

                <Typography variant="h6" gutterBottom>
                  {article.title}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {article.authors}
                </Typography>

                {/* Reasons */}
                <Box my={2}>
                  <Typography variant="body2" fontWeight="medium" gutterBottom>
                    Why recommended:
                  </Typography>
                  <Stack direction="row" spacing={1} flexWrap="wrap" gap={1}>
                    {rec.reasons.map((reason, idx) => (
                      <Chip
                        key={idx}
                        label={reason}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                    ))}
                  </Stack>
                </Box>

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
  )
}
