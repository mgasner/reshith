import { useState } from 'react'
import { Link, Outlet } from 'react-router-dom'

const LESSONS = [
  { num: '01', name: 'Lesson 1' },
  { num: '02', name: 'Lesson 2' },
  { num: '03', name: 'Lesson 3' },
]

export function Layout() {
  const [lessonsOpen, setLessonsOpen] = useState(false)

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <Link to="/" className="flex items-center">
                <span className="text-xl font-semibold text-gray-900">Reshith</span>
              </Link>
              <div className="hidden sm:ml-8 sm:flex sm:space-x-8">
                <Link
                  to="/alphabet"
                  className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-500 hover:text-gray-900"
                >
                  Alphabet
                </Link>
                <Link
                  to="/vowels"
                  className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-500 hover:text-gray-900"
                >
                  Vowels
                </Link>
                <div className="relative">
                  <button
                    onClick={() => setLessonsOpen(!lessonsOpen)}
                    className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-500 hover:text-gray-900"
                  >
                    Lessons
                    <svg
                      className={`ml-1 h-4 w-4 transition-transform ${lessonsOpen ? 'rotate-180' : ''}`}
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
                  to="/exercises/prepositions"
                  className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-500 hover:text-gray-900"
                >
                  Exercises
                </Link>
                <Link
                  to="/decks"
                  className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-500 hover:text-gray-900"
                >
                  Decks
                </Link>
              </div>
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
