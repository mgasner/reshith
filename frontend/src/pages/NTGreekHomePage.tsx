import { Link } from 'react-router-dom'

export function NTGreekHomePage() {
  return (
    <div className="px-4">
      <div className="text-center py-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">New Testament Greek</h1>
        <p className="text-xl text-gray-600 mb-2">
          Read the New Testament in the original Koine Greek
        </p>
        <p className="text-sm text-gray-500 italic mb-8">
          Koine Greek — the common dialect of the Hellenistic world and the New Testament
        </p>

        <div className="mt-10">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Vocabulary Lessons</h2>
          <div className="flex flex-wrap justify-center gap-4">
            {['1', '2', '3'].map((num, i) => (
              <Link
                key={num}
                to={`/nt-greek/lesson/${num}`}
                className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Lesson {i + 1}
              </Link>
            ))}
            <Link
              to="/exercises/nt-greek"
              className="inline-block px-6 py-3 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50"
            >
              Grammar Exercises
            </Link>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto mt-12">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Nouns &amp; the Article</h3>
            <p className="text-gray-600 text-sm">
              First and second declension nouns, the definite article, and basic prepositions
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Present Indicative</h3>
            <p className="text-gray-600 text-sm">
              Present active and middle/passive indicative of thematic and contract verbs
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Third Declension &amp; Aorist</h3>
            <p className="text-gray-600 text-sm">
              Third declension nouns, aorist and imperfect tenses, and participles
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
