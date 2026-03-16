import { Link } from 'react-router-dom'

export function SanskritHomePage() {
  return (
    <div className="px-4">
      <div className="text-center py-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Sanskrit</h1>
        <p className="text-xl text-gray-600 mb-2">
          Master Classical Sanskrit through vocabulary and spaced repetition
        </p>
        <p className="text-sm text-gray-500 italic mb-8">
          Classical Sanskrit — the language of the Vedas, Upanishads, and Bhagavad Gita
        </p>

        <div className="mt-10">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Vocabulary Lessons</h2>
          <div className="flex flex-wrap justify-center gap-4">
            {['1', '2', '3'].map((num, i) => (
              <Link
                key={num}
                to={`/sanskrit/lesson/${num}`}
                className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Lesson {i + 1}
              </Link>
            ))}
            <Link
              to="/exercises/sanskrit"
              className="inline-block px-6 py-3 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50"
            >
              Grammar Exercises
            </Link>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto mt-12">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Devanagari Script</h3>
            <p className="text-gray-600 text-sm">
              Learn to read and write the Devanagari alphabet with IAST transliteration
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Nominal Declension</h3>
            <p className="text-gray-600 text-sm">
              A-stem, i-stem, and u-stem nouns across all eight cases in three genders
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Verbal System</h3>
            <p className="text-gray-600 text-sm">
              Present tense conjugation, sandhi rules, and the thematic and athematic classes
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
