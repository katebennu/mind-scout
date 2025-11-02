import { useState, useEffect } from 'react'

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
    return <div className="text-center py-8">Loading recommendations...</div>
  }

  if (recommendations.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">No recommendations available.</p>
        <p className="text-sm text-gray-500 mt-2">
          Set your interests in the Profile page to get started!
        </p>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">
          Personalized Recommendations
        </h2>
        <p className="text-gray-600 mt-1">
          Papers recommended based on your interests and reading history
        </p>
      </div>

      <div className="space-y-4">
        {recommendations.map((rec) => {
          const article = rec.article
          return (
            <div
              key={article.id}
              className="bg-white shadow rounded-lg p-6 border-l-4 border-indigo-500 hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between items-start mb-3">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <span className="text-lg font-bold text-indigo-600">
                      {Math.round(rec.score * 100)}%
                    </span>
                    <span className="text-sm text-gray-500">match</span>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {article.title}
                  </h3>
                  <p className="text-sm text-gray-600 mb-2">{article.authors}</p>
                </div>
              </div>

              {/* Reasons */}
              <div className="mb-3">
                <p className="text-sm font-medium text-gray-700 mb-1">Why recommended:</p>
                <div className="flex flex-wrap gap-2">
                  {rec.reasons.map((reason, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 bg-indigo-50 text-indigo-700 text-sm rounded"
                    >
                      {reason}
                    </span>
                  ))}
                </div>
              </div>

              <p className="text-sm text-gray-500 line-clamp-2 mb-3">
                {article.abstract}
              </p>

              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4 text-sm text-gray-500">
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                    {article.source}
                  </span>
                  {article.published_date && (
                    <span>{new Date(article.published_date).toLocaleDateString()}</span>
                  )}
                  {article.citation_count && (
                    <span>📊 {article.citation_count} citations</span>
                  )}
                </div>

                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm font-medium text-indigo-600 hover:text-indigo-800"
                >
                  View Paper →
                </a>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
