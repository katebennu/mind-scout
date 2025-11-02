import { useState, useEffect } from 'react'

const API_BASE = 'http://localhost:8000/api'

export default function Articles() {
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)

  useEffect(() => {
    fetchArticles()
  }, [page])

  const fetchArticles = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE}/articles?page=${page}&page_size=10`)
      const data = await response.json()
      setArticles(data.articles)
      setTotal(data.total)
    } catch (error) {
      console.error('Error fetching articles:', error)
    }
    setLoading(false)
  }

  const handleRate = async (id, rating) => {
    try {
      await fetch(`${API_BASE}/articles/${id}/rate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating })
      })
      fetchArticles() // Refresh
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
      fetchArticles() // Refresh
    } catch (error) {
      console.error('Error marking article:', error)
    }
  }

  if (loading) {
    return <div className="text-center py-8">Loading...</div>
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Articles</h2>
        <span className="text-sm text-gray-500">{total} total</span>
      </div>

      <div className="space-y-4">
        {articles.map((article) => (
          <div
            key={article.id}
            className="bg-white shadow rounded-lg p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {article.title}
                </h3>
                <p className="text-sm text-gray-600 mb-2">{article.authors}</p>
                <p className="text-sm text-gray-500 line-clamp-2 mb-3">
                  {article.abstract}
                </p>
                <div className="flex items-center space-x-4 text-sm text-gray-500">
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">
                    {article.source}
                  </span>
                  {article.published_date && (
                    <span>{new Date(article.published_date).toLocaleDateString()}</span>
                  )}
                  {article.citation_count && (
                    <span>📊 {article.citation_count} citations</span>
                  )}
                </div>
              </div>

              <div className="ml-4 flex flex-col space-y-2">
                <button
                  onClick={() => handleMarkRead(article.id, !article.is_read)}
                  className={`px-3 py-1 text-sm rounded ${
                    article.is_read
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                  }`}
                >
                  {article.is_read ? '✓ Read' : 'Mark Read'}
                </button>

                {/* Rating buttons */}
                <div className="flex space-x-1">
                  {[1, 2, 3, 4, 5].map((rating) => (
                    <button
                      key={rating}
                      onClick={() => handleRate(article.id, rating)}
                      className={`text-lg ${
                        article.rating >= rating ? 'text-yellow-500' : 'text-gray-300'
                      } hover:text-yellow-400`}
                      title={`Rate ${rating} stars`}
                    >
                      ★
                    </button>
                  ))}
                </div>

                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-indigo-600 hover:text-indigo-800"
                >
                  View →
                </a>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      <div className="mt-6 flex justify-center space-x-2">
        <button
          onClick={() => setPage(p => Math.max(1, p - 1))}
          disabled={page === 1}
          className="px-4 py-2 bg-white border rounded disabled:opacity-50 hover:bg-gray-50"
        >
          Previous
        </button>
        <span className="px-4 py-2">Page {page}</span>
        <button
          onClick={() => setPage(p => p + 1)}
          disabled={page * 10 >= total}
          className="px-4 py-2 bg-white border rounded disabled:opacity-50 hover:bg-gray-50"
        >
          Next
        </button>
      </div>
    </div>
  )
}
