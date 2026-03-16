import { useState } from 'react'
import { Link, Outlet } from 'react-router-dom'

const LESSONS = [
  { num: '01', name: 'Lesson 1' },
  { num: '02', name: 'Lesson 2' },
  { num: '03', name: 'Lesson 3' },
]

const LANGUAGES = [
  { code: 'he', label: 'א', name: 'Hebrew' },
]

export function Layout() {
  const [lessonsOpen, setLessonsOpen] = useState(false)
  const [selectedLang, setSelectedLang] = useState(LANGUAGES[0])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top bar: language picker */}
      <div className="bg-gray-900 text-gray-300">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center h-9 gap-1">
            <span className="text-xs uppercase tracking-widest text-gray-500 mr-2">Language</span>
            {LANGUAGES.map((lang) => (
              <button
                key={lang.code}
                onClick={() => setSelectedLang(lang)}
                className={`flex items-center gap-1.5 px-3 py-0.5 rounded text-sm font-medium transition-colors ${
                  selectedLang.code === lang.code
                    ? 'bg-gray-700 text-white'
                    : 'hover:bg-gray-800 hover:text-white'
                }`}
              >
                <span className="text-base leading-none">{lang.label}</span>
                <span>{lang.name}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Second bar: main nav */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center h-14 gap-8">
            <Link to="/" className="flex-shrink-0">
              <span className="text-xl font-semibold text-gray-900">Reshith</span>
            </Link>
            <div className="hidden sm:flex sm:items-center sm:gap-6">
              <Link
                to="/alphabet"
                className="text-sm font-medium text-gray-500 hover:text-gray-900"
              >
                Alphabet
              </Link>
              <Link
                to="/vowels"
                className="text-sm font-medium text-gray-500 hover:text-gray-900"
              >
                Vowels
              </Link>
              <Link
                to="/exercises"
                className="text-sm font-medium text-gray-500 hover:text-gray-900"
              >
                Exercises
              </Link>
              <div className="relative">
                <button
                  onClick={() => setLessonsOpen(!lessonsOpen)}
                  className="flex items-center gap-1 text-sm font-medium text-gray-500 hover:text-gray-900"
                >
                  Lessons
                  <svg
                    className={`h-4 w-4 transition-transform ${lessonsOpen ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {lessonsOpen && (
                  <div className="absolute left-0 mt-2 w-40 bg-white rounded-md shadow-lg py-1 z-10">
                    {LESSONS.map((lesson) => (
                      <Link
                        key={lesson.num}
                        to={`/lesson/${lesson.num}`}
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        onClick={() => setLessonsOpen(false)}
                      >
                        {lesson.name}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
              <Link
                to="/decks"
                className="text-sm font-medium text-gray-500 hover:text-gray-900"
              >
                Decks
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <Outlet />
      </main>
    </div>
  )
}
