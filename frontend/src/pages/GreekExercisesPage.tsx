import { Link } from 'react-router-dom'

const EXERCISE_TYPES = [
  {
    path: '/exercises/greek/declension',
    title: 'Noun Declension',
    description: 'Practice first and second declension noun forms across all five cases.',
    tag: 'Greek forms',
  },
  {
    path: '/exercises/greek/conjugation',
    title: 'Verb Conjugation',
    description: 'Conjugate thematic verbs in the present active indicative.',
    tag: 'Greek forms',
  },
]

export function GreekExercisesPage() {
  return (
    <div className="px-4">
      <div className="mb-8">
        <Link to="/greek" className="text-sm text-blue-600 hover:underline mb-2 inline-block">
          &larr; Ancient Greek
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">Ancient Greek Exercises</h1>
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
