import { Link } from 'react-router-dom'

export function ExercisesPage() {
  return (
    <div className="px-4">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Exercises</h1>
        <p className="text-gray-600">Choose a language to practice.</p>
      </div>
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6 max-w-4xl">
        <Link
          to="/exercises/hebrew"
          className="block bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md hover:border-blue-300 transition-all"
        >
          <div className="flex items-center gap-3 mb-2">
            <span className="text-3xl font-hebrew">בְּ</span>
            <h2 className="text-lg font-semibold text-gray-900">Biblical Hebrew</h2>
          </div>
          <p className="text-sm text-gray-600">
            Prepositions, definite article, sentences, translation, verbal, comparative, and relative clause exercises.
          </p>
        </Link>
        <Link
          to="/exercises/latin"
          className="block bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md hover:border-blue-300 transition-all"
        >
          <div className="flex items-center gap-3 mb-2">
            <span className="text-3xl font-serif font-bold text-gray-700">L</span>
            <h2 className="text-lg font-semibold text-gray-900">Latin</h2>
          </div>
          <p className="text-sm text-gray-600">
            Noun declension and verb conjugation drills based on Wheelock's Latin vocabulary.
          </p>
        </Link>
        <Link
          to="/exercises/greek"
          className="block bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md hover:border-blue-300 transition-all"
        >
          <div className="flex items-center gap-3 mb-2">
            <span className="text-3xl font-serif font-bold text-gray-700">α</span>
            <h2 className="text-lg font-semibold text-gray-900">Ancient Greek</h2>
          </div>
          <p className="text-sm text-gray-600">
            Noun declension and verb conjugation drills for Attic Greek.
          </p>
        </Link>
        <Link
          to="/exercises/nt-greek"
          className="block bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md hover:border-blue-300 transition-all"
        >
          <div className="flex items-center gap-3 mb-2">
            <span className="text-3xl font-serif font-bold text-gray-700">κ</span>
            <h2 className="text-lg font-semibold text-gray-900">NT Greek</h2>
          </div>
          <p className="text-sm text-gray-600">
            Noun declension and verb conjugation drills for Koine Greek New Testament study.
          </p>
        </Link>
        <Link
          to="/exercises/sanskrit"
          className="block bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md hover:border-blue-300 transition-all"
        >
          <div className="flex items-center gap-3 mb-2">
            <span className="text-3xl font-serif font-bold text-gray-700">अ</span>
            <h2 className="text-lg font-semibold text-gray-900">Sanskrit</h2>
          </div>
          <p className="text-sm text-gray-600">
            Noun declension drills for Classical Sanskrit using IAST transliteration.
          </p>
        </Link>
        <Link
          to="/exercises/ecclesiastical-latin"
          className="block bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md hover:border-blue-300 transition-all"
        >
          <div className="flex items-center gap-3 mb-2">
            <span className="text-3xl font-serif font-bold text-gray-700">E</span>
            <h2 className="text-lg font-semibold text-gray-900">Ecclesiastical Latin</h2>
          </div>
          <p className="text-sm text-gray-600">
            Noun declension and verb conjugation drills for the Latin of the Vulgate and Church Fathers.
          </p>
        </Link>
      </div>
    </div>
  )
}
