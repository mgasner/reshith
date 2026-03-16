import { Link } from 'react-router-dom'

export function LatinHomePage() {
  return (
    <div className="px-4">
      <div className="text-center py-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Latin</h1>
        <p className="text-xl text-gray-600 mb-2">
          Master classical Latin through vocabulary and spaced repetition
        </p>
        <p className="text-sm text-gray-500 italic mb-8">
          Based on Wheelock's Latin, 7th Edition
        </p>

        <div className="mt-10">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Vocabulary Lessons</h2>
          <div className="flex flex-wrap justify-center gap-4">
            {['01', '02', '03'].map((num, i) => (
              <Link
                key={num}
                to={`/latin/lesson/${num}`}
                className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Lesson {i + 1}
              </Link>
            ))}
            <Link
              to="/exercises/latin"
              className="inline-block px-6 py-3 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50"
            >
              Grammar Exercises
            </Link>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto mt-12">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">1st &amp; 2nd Declension</h3>
            <p className="text-gray-600 text-sm">
              Nouns, verbs of the 1st and 2nd conjugations, basic adjectives
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">3rd Declension</h3>
            <p className="text-gray-600 text-sm">
              3rd declension nouns and adjectives, 3rd and 4th conjugation verbs
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Pronouns &amp; Particles</h3>
            <p className="text-gray-600 text-sm">
              Demonstrative pronouns, common prepositions, conjunctions, adverbs
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
