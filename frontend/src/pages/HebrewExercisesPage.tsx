import { Link } from 'react-router-dom'

const EXERCISE_TYPES = [
  {
    path: '/exercises/hebrew/prepositions',
    title: 'Prepositions',
    description: 'Practice the inseparable prepositions בְּ לְ כְּ prefixed to nouns.',
    tag: 'Hebrew → English / English → Hebrew',
  },
  {
    path: '/exercises/hebrew/article',
    title: 'Definite Article',
    description: 'Add or remove the definite article הַ with its phonological variations.',
    tag: 'Hebrew forms',
  },
  {
    path: '/exercises/hebrew/sentences',
    title: 'Sentence Reading',
    description: 'Read Hebrew sentences and reveal the English translation.',
    tag: 'Read & reveal',
  },
  {
    path: '/exercises/hebrew/translation',
    title: 'Translation',
    description: 'Translate English sentences into Hebrew.',
    tag: 'English → Hebrew',
  },
  {
    path: '/exercises/hebrew/verbal',
    title: 'Verbal',
    description: 'Translate Hebrew verbal sentences to English.',
    tag: 'Hebrew → English',
  },
  {
    path: '/exercises/hebrew/comparative',
    title: 'Comparative',
    description: 'Translate comparative constructions using מִן.',
    tag: 'Hebrew → English',
  },
  {
    path: '/exercises/hebrew/relative-clauses',
    title: 'Relative Clauses',
    description: 'Translate relative clauses using אֲשֶׁר.',
    tag: 'Hebrew → English',
  },
  {
    path: '/exercises/hebrew/qal-paradigm',
    title: 'Verb Paradigms',
    description: 'Study full verb paradigm tables across all seven binyanim, or fill in worksheets with missing forms.',
    tag: 'Paradigm / Worksheet',
  },
]

export function HebrewExercisesPage() {
  return (
    <div className="px-4">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Biblical Hebrew Exercises</h1>
        <p className="text-gray-600">Choose an exercise type to practice.</p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
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
