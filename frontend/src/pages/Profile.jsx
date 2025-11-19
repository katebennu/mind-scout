import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Chip,
  Stack,
  Grid,
  LinearProgress,
  Divider,
} from '@mui/material'
import {
  Edit,
  Save,
  Cancel,
} from '@mui/icons-material'

const API_BASE = 'http://localhost:8000/api'

export default function Profile() {
  const [profile, setProfile] = useState(null)
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)
  const [formData, setFormData] = useState({
    interests: [],
    skill_level: 'intermediate',
    preferred_sources: [],
    daily_reading_goal: 5
  })

  useEffect(() => {
    fetchProfile()
    fetchStats()
  }, [])

  const fetchProfile = async () => {
    try {
      const response = await fetch(`${API_BASE}/profile`)
      const data = await response.json()
      setProfile(data)
      setFormData({
        interests: data.interests || [],
        skill_level: data.skill_level || 'intermediate',
        preferred_sources: data.preferred_sources || [],
        daily_reading_goal: data.daily_reading_goal || 5
      })
    } catch (error) {
      console.error('Error fetching profile:', error)
    }
    setLoading(false)
  }

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/profile/stats`)
      const data = await response.json()
      setStats(data)
    } catch (error) {
      console.error('Error fetching stats:', error)
    }
  }

  const handleSave = async () => {
    try {
      await fetch(`${API_BASE}/profile`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })
      setEditing(false)
      fetchProfile()
    } catch (error) {
      console.error('Error updating profile:', error)
    }
  }

  const handleInterestsChange = (value) => {
    setFormData({
      ...formData,
      interests: value.split(',').map(s => s.trim()).filter(Boolean)
    })
  }

  const handleSourcesChange = (value) => {
    setFormData({
      ...formData,
      preferred_sources: value.split(',').map(s => s.trim()).filter(Boolean)
    })
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" py={8}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Typography variant="h4" fontWeight="bold" gutterBottom>
        Profile & Settings
      </Typography>

      <Grid container spacing={3} mt={1}>
        {/* Profile Card */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Typography variant="h6" fontWeight="bold">
                  Your Profile
                </Typography>
                {!editing ? (
                  <Button
                    size="small"
                    startIcon={<Edit />}
                    onClick={() => setEditing(true)}
                  >
                    Edit
                  </Button>
                ) : (
                  <Box>
                    <Button
                      size="small"
                      startIcon={<Cancel />}
                      onClick={() => {
                        setEditing(false)
                        // Reset form data
                        setFormData({
                          interests: profile?.interests || [],
                          skill_level: profile?.skill_level || 'intermediate',
                          preferred_sources: profile?.preferred_sources || [],
                          daily_reading_goal: profile?.daily_reading_goal || 5
                        })
                      }}
                      sx={{ mr: 1 }}
                    >
                      Cancel
                    </Button>
                  </Box>
                )}
              </Box>

              {!editing ? (
                <Stack spacing={3}>
                  <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Interests
                    </Typography>
                    <Stack direction="row" spacing={1} flexWrap="wrap" gap={1}>
                      {profile?.interests?.map((interest, idx) => (
                        <Chip
                          key={idx}
                          label={interest}
                          size="small"
                          color="primary"
                        />
                      ))}
                    </Stack>
                  </Box>

                  <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Skill Level
                    </Typography>
                    <Typography variant="body1" textTransform="capitalize">
                      {profile?.skill_level}
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Preferred Sources
                    </Typography>
                    <Typography variant="body1">
                      {profile?.preferred_sources?.join(', ')}
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Daily Reading Goal
                    </Typography>
                    <Typography variant="body1">
                      {profile?.daily_reading_goal} papers
                    </Typography>
                  </Box>
                </Stack>
              ) : (
                <Stack spacing={3}>
                  <TextField
                    label="Interests (comma-separated)"
                    value={formData.interests.join(', ')}
                    onChange={(e) => handleInterestsChange(e.target.value)}
                    placeholder="e.g., transformers, RL, computer vision"
                    fullWidth
                  />

                  <FormControl fullWidth>
                    <InputLabel>Skill Level</InputLabel>
                    <Select
                      value={formData.skill_level}
                      onChange={(e) => setFormData({ ...formData, skill_level: e.target.value })}
                      label="Skill Level"
                    >
                      <MenuItem value="beginner">Beginner</MenuItem>
                      <MenuItem value="intermediate">Intermediate</MenuItem>
                      <MenuItem value="advanced">Advanced</MenuItem>
                    </Select>
                  </FormControl>

                  <TextField
                    label="Preferred Sources (comma-separated)"
                    value={formData.preferred_sources.join(', ')}
                    onChange={(e) => handleSourcesChange(e.target.value)}
                    placeholder="e.g., arxiv, semanticscholar"
                    fullWidth
                  />

                  <TextField
                    label="Daily Reading Goal"
                    type="number"
                    value={formData.daily_reading_goal}
                    onChange={(e) => setFormData({ ...formData, daily_reading_goal: parseInt(e.target.value) })}
                    inputProps={{ min: 1 }}
                    fullWidth
                  />

                  <Button
                    variant="contained"
                    startIcon={<Save />}
                    onClick={handleSave}
                    fullWidth
                  >
                    Save Changes
                  </Button>
                </Stack>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Stats Card */}
        {stats && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight="bold" gutterBottom>
                  Statistics
                </Typography>

                <Stack spacing={3} mt={2}>
                  <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Total Articles
                    </Typography>
                    <Typography variant="h4" fontWeight="bold">
                      {stats.total_articles}
                    </Typography>
                  </Box>

                  <Divider />

                  <Box>
                    <Box display="flex" justifyContent="space-between" mb={1}>
                      <Typography variant="body2" color="text.secondary">
                        Read
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {stats.read_percentage}%
                      </Typography>
                    </Box>
                    <Typography variant="h5" color="success.main" fontWeight="bold" gutterBottom>
                      {stats.read_articles}
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={stats.read_percentage}
                      color="success"
                      sx={{ height: 8, borderRadius: 1 }}
                    />
                  </Box>

                  <Divider />

                  <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Rated Articles
                    </Typography>
                    <Typography variant="h5" fontWeight="bold">
                      {stats.rated_articles}
                    </Typography>
                    {stats.average_rating && (
                      <Typography variant="body2" color="text.secondary" mt={0.5}>
                        Avg: {stats.average_rating} ★
                      </Typography>
                    )}
                  </Box>

                  <Divider />

                  <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Articles by Source
                    </Typography>
                    <Stack spacing={1} mt={1}>
                      {Object.entries(stats.articles_by_source || {}).map(([source, count]) => (
                        <Box key={source} display="flex" justifyContent="space-between">
                          <Typography variant="body2">{source}</Typography>
                          <Typography variant="body2" fontWeight="bold">
                            {count}
                          </Typography>
                        </Box>
                      ))}
                    </Stack>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  )
}
