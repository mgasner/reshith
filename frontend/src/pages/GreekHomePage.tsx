import { Link } from 'react-router-dom'

export function GreekHomePage() {
  return (
    <div className="px-4">
      <div className="text-center py-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Ancient Greek</h1>
        <p className="text-xl text-gray-600 mb-2">
          Master Attic Greek through vocabulary and spaced repetition
        </p>
        <p className="text-sm text-gray-500 italic mb-8">
          Classical Attic dialect — the language of Plato, Thucydides, and Sophocles
        </p>

        <div className="mt-10">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Vocabulary Lessons</h2>
          <div className="flex flex-wrap justify-center gap-4">
            {['1', '2', '3'].map((num, i) => (
              <Link
                key={num}
                to={`/greek/lesson/${num}`}
                className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Lesson {i + 1}
              </Link>
            ))}
            <Link
              to="/exercises/greek"
              className="inline-block px-6 py-3 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50"
            >
              Grammar Exercises
            </Link>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto mt-12">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Alpha &amp; Omicron Declensions</h3>
            <p className="text-gray-600 text-sm">
              First and second declension nouns, basic adjectives, and the definite article
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Thematic Verbs</h3>
            <p className="text-gray-600 text-sm">
              Present active and middle/passive indicative, infinitive, and participle forms
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Third Declension</h3>
            <p className="text-gray-600 text-sm">
              Third declension nouns, contract verbs, and athematic verb forms
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
