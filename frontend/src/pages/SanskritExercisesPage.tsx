import { Link } from 'react-router-dom'

const EXERCISE_TYPES = [
  {
    path: '/exercises/sanskrit/declension',
    title: 'Noun Declension',
    description: 'Practice a-stem noun forms across all eight cases in Sanskrit.',
    tag: 'Sanskrit forms',
  },
]

export function SanskritExercisesPage() {
  return (
    <div className="px-4">
      <div className="mb-8">
        <Link to="/sanskrit" className="text-sm text-blue-600 hover:underline mb-2 inline-block">
          &larr; Sanskrit
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">Sanskrit Exercises</h1>
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
