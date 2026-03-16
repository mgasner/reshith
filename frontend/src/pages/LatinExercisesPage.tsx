import { Link } from 'react-router-dom'

const EXERCISE_TYPES = [
  {
    path: '/exercises/latin/declension',
    title: 'Noun Declension',
    description: 'Practice 1st and 2nd declension noun forms across all five cases.',
    tag: 'Latin forms',
  },
  {
    path: '/exercises/latin/conjugation',
    title: 'Verb Conjugation',
    description: 'Conjugate 1st and 2nd conjugation verbs in the present tense active.',
    tag: 'Latin forms',
  },
]

export function LatinExercisesPage() {
  return (
    <div className="px-4">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Latin Exercises</h1>
        <p className="text-gray-600">Choose an exercise type to practice.</p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-2xl">
        {EXERCISE_TYPES.map((ex) => (
          <Link
            key={ex.path}
            to={ex.path}
            className="block bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:shadow-md hover:border-blue-300 transition-all"
          >
            <h2 className="text-lg font-semibold text-gray-900 mb-1">{ex.title}</h2>
            <p className="text-sm text-gray-600 mb-3">{ex.description}</p>
            <span className="inline-block text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">
              {ex.tag}
            </span>
          </Link>
        ))}
      </div>
    </div>
  )
}
