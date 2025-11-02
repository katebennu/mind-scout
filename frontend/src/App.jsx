import { useState } from 'react'
import Articles from './pages/Articles'
import Recommendations from './pages/Recommendations'
import Profile from './pages/Profile'
import Search from './pages/Search'

function App() {
  const [currentPage, setCurrentPage] = useState('articles')

  const navigation = [
    { id: 'articles', name: 'Articles', icon: '📚' },
    { id: 'recommendations', name: 'Recommendations', icon: '🎯' },
    { id: 'search', name: 'Search', icon: '🔍' },
    { id: 'profile', name: 'Profile', icon: '⚙️' },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <h1 className="text-3xl font-bold text-gray-900">
                🧠 Mind Scout
              </h1>
              <span className="ml-4 text-sm text-gray-500">
                AI Research Assistant
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {navigation.map((item) => (
              <button
                key={item.id}
                onClick={() => setCurrentPage(item.id)}
                className={`
                  py-4 px-1 inline-flex items-center border-b-2 font-medium text-sm
                  ${
                    currentPage === item.id
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <span className="mr-2">{item.icon}</span>
                {item.name}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentPage === 'articles' && <Articles />}
        {currentPage === 'recommendations' && <Recommendations />}
        {currentPage === 'search' && <Search />}
        {currentPage === 'profile' && <Profile />}
      </main>
    </div>
  )
}

export default App
