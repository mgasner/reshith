import { Link } from 'react-router-dom'

export function EcclesiasticalLatinHomePage() {
  return (
    <div className="px-4">
      <div className="text-center py-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Ecclesiastical Latin</h1>
        <p className="text-xl text-gray-600 mb-2">
          The Latin of the Vulgate and the Church Fathers
        </p>
        <p className="text-sm text-gray-500 italic mb-8">
          Based on Jerome's Vulgate, the Church Fathers, and the ecclesiastical tradition
        </p>

        <div className="mt-10">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Vocabulary Lessons</h2>
          <div className="flex flex-wrap justify-center gap-4">
            {['1', '2', '3'].map((num, i) => (
              <Link
                key={num}
                to={`/ecclesiastical-latin/lesson/${num}`}
                className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Lesson {i + 1}
              </Link>
            ))}
            <Link
              to="/exercises/ecclesiastical-latin"
              className="inline-block px-6 py-3 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50"
            >
              Grammar Exercises
            </Link>
          </div>
        </div>

        <div className="mt-10">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Texts</h2>
          <div className="flex flex-wrap justify-center gap-4">
            <Link
              to="/ecclesiastical-latin/vulgate"
              className="inline-block px-6 py-3 bg-amber-700 text-white rounded-lg hover:bg-amber-800"
            >
              Vulgata Latina
            </Link>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto mt-12">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Jerome's Vulgate</h3>
            <p className="text-gray-600 text-sm">
              The Latin Bible translated by St. Jerome in the 4th century, the standard
              Scripture of the Western Church
            </p>
            <Link
              to="/ecclesiastical-latin/vulgate"
              className="inline-block mt-3 text-sm text-amber-700 hover:text-amber-800 font-medium"
            >
              Open interlinear viewer →
            </Link>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Church Fathers</h3>
            <p className="text-gray-600 text-sm">
              Theological and devotional Latin of Augustine, Ambrose, Gregory the Great,
              and other patristic writers
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Ecclesiastical Tradition</h3>
            <p className="text-gray-600 text-sm">
              Liturgical Latin, hymns, creeds, and conciliar documents that shaped
              Christian worship and doctrine
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
