import { Link } from 'react-router-dom'

export function HomePage() {
  return (
    <div className="px-4">
      <div className="text-center py-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Reshith</h1>
        <p className="text-xl text-gray-600 mb-2">
          Master classical languages through spaced repetition
        </p>
        <p className="text-sm text-gray-500 italic mb-8">
          "The fear of the LORD is the beginning (reshith) of knowledge" - Proverbs 1:7
        </p>

        <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto mt-12">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Flashcards</h3>
            <p className="text-gray-600 text-sm">
              Build vocabulary with spaced repetition using the SM-2 algorithm
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Translation Drills</h3>
            <p className="text-gray-600 text-sm">
              Practice translation with LLM-powered exercises and feedback
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Multiple Languages</h3>
            <p className="text-gray-600 text-sm">
              Biblical Hebrew, Latin, Greek, Sanskrit, Pali, and more
            </p>
          </div>
        </div>

        <div className="mt-12">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            Start with Biblical Hebrew
          </h2>
          <div className="flex flex-wrap justify-center gap-4">
            <Link
              to="/alphabet"
              className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Learn the Alphabet
            </Link>
            <Link
              to="/vowels"
              className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Learn the Vowels
            </Link>
            <Link
              to="/lesson/01"
              className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Lesson 1 Vocabulary
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
