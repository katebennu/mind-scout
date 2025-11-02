import { useState } from 'react'

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

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Semantic Search
        </h2>
        <p className="text-gray-600">
          Search for papers using natural language - find papers by meaning, not just keywords
        </p>
      </div>

      {/* Search Form */}
      <form onSubmit={handleSearch} className="mb-8">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., 'attention mechanisms in transformers' or 'how to train large language models'"
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-6 py-3 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </form>

      {/* Results */}
      {loading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          <p className="mt-2 text-gray-600">Searching...</p>
        </div>
      )}

      {searched && !loading && results.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-600">No results found.</p>
          <p className="text-sm text-gray-500 mt-2">
            Try a different search query
          </p>
        </div>
      )}

      {!loading && results.length > 0 && (
        <div>
          <p className="text-sm text-gray-600 mb-4">
            Found {results.length} results
          </p>
          <div className="space-y-4">
            {results.map((result) => {
              const article = result.article
              return (
                <div
                  key={article.id}
                  className="bg-white shadow rounded-lg p-6 hover:shadow-md transition-shadow"
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <span className="text-sm font-bold text-green-600">
                          {Math.round(result.relevance * 100)}% relevant
                        </span>
                      </div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        {article.title}
                      </h3>
                      <p className="text-sm text-gray-600 mb-2">{article.authors}</p>
                      <p className="text-sm text-gray-500 line-clamp-3 mb-3">
                        {article.abstract}
                      </p>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                          <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                            {article.source}
                          </span>
                          {article.published_date && (
                            <span>
                              {new Date(article.published_date).toLocaleDateString()}
                            </span>
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
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Example queries */}
      {!searched && (
        <div className="mt-8 p-6 bg-gray-50 rounded-lg">
          <h3 className="font-medium text-gray-900 mb-3">Example queries:</h3>
          <div className="space-y-2">
            {[
              'attention mechanisms in deep learning',
              'computer vision transformers',
              'reinforcement learning for robotics',
              'diffusion models for image generation',
            ].map((example) => (
              <button
                key={example}
                onClick={() => setQuery(example)}
                className="block text-sm text-indigo-600 hover:text-indigo-800 hover:underline"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
