import { useState, useEffect } from 'react'

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
    return <div className="text-center py-8">Loading...</div>
  }

  return (
    <div className="max-w-4xl">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Profile & Settings</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {/* Profile Card */}
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Your Profile</h3>
            <button
              onClick={() => setEditing(!editing)}
              className="text-sm text-indigo-600 hover:text-indigo-800"
            >
              {editing ? 'Cancel' : 'Edit'}
            </button>
          </div>

          {!editing ? (
            <div className="space-y-3">
              <div>
                <p className="text-sm font-medium text-gray-700">Interests</p>
                <div className="flex flex-wrap gap-2 mt-1">
                  {profile?.interests?.map((interest, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 bg-indigo-100 text-indigo-800 rounded text-sm"
                    >
                      {interest}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <p className="text-sm font-medium text-gray-700">Skill Level</p>
                <p className="text-sm text-gray-900 mt-1 capitalize">
                  {profile?.skill_level}
                </p>
              </div>

              <div>
                <p className="text-sm font-medium text-gray-700">Preferred Sources</p>
                <p className="text-sm text-gray-900 mt-1">
                  {profile?.preferred_sources?.join(', ')}
                </p>
              </div>

              <div>
                <p className="text-sm font-medium text-gray-700">Daily Reading Goal</p>
                <p className="text-sm text-gray-900 mt-1">
                  {profile?.daily_reading_goal} papers
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Interests (comma-separated)
                </label>
                <input
                  type="text"
                  value={formData.interests.join(', ')}
                  onChange={(e) => handleInterestsChange(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500"
                  placeholder="e.g., transformers, RL, computer vision"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Skill Level
                </label>
                <select
                  value={formData.skill_level}
                  onChange={(e) => setFormData({ ...formData, skill_level: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="beginner">Beginner</option>
                  <option value="intermediate">Intermediate</option>
                  <option value="advanced">Advanced</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Preferred Sources (comma-separated)
                </label>
                <input
                  type="text"
                  value={formData.preferred_sources.join(', ')}
                  onChange={(e) => handleSourcesChange(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500"
                  placeholder="e.g., arxiv, semanticscholar"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Daily Reading Goal
                </label>
                <input
                  type="number"
                  value={formData.daily_reading_goal}
                  onChange={(e) => setFormData({ ...formData, daily_reading_goal: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500"
                  min="1"
                />
              </div>

              <button
                onClick={handleSave}
                className="w-full px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
              >
                Save Changes
              </button>
            </div>
          )}
        </div>

        {/* Stats Card */}
        {stats && (
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Statistics</h3>
            <div className="space-y-4">
              <div>
                <p className="text-sm text-gray-600">Total Articles</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total_articles}</p>
              </div>

              <div>
                <p className="text-sm text-gray-600">Read</p>
                <div className="flex items-center justify-between">
                  <p className="text-xl font-semibold text-green-600">
                    {stats.read_articles}
                  </p>
                  <p className="text-sm text-gray-500">
                    {stats.read_percentage}%
                  </p>
                </div>
                <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-600 h-2 rounded-full"
                    style={{ width: `${stats.read_percentage}%` }}
                  ></div>
                </div>
              </div>

              <div>
                <p className="text-sm text-gray-600">Rated Articles</p>
                <p className="text-xl font-semibold text-gray-900">{stats.rated_articles}</p>
                {stats.average_rating && (
                  <p className="text-sm text-gray-500">
                    Avg: {stats.average_rating} ★
                  </p>
                )}
              </div>

              <div>
                <p className="text-sm text-gray-600 mb-2">Articles by Source</p>
                <div className="space-y-1">
                  {Object.entries(stats.articles_by_source || {}).map(([source, count]) => (
                    <div key={source} className="flex justify-between text-sm">
                      <span className="text-gray-700">{source}</span>
                      <span className="font-medium text-gray-900">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
