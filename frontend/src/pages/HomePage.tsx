import { Link } from 'react-router-dom'

export function HomePage() {
  return (
    <div className="px-4">
      <div className="text-center py-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Reshith</h1>
        <p className="text-xl text-gray-600 mb-2">
          Master classical languages through spaced repetition
        </p>
        <p className="text-sm text-gray-500 italic mb-8">
          "The fear of the LORD is the beginning (reshith) of knowledge" — Proverbs 1:7
        </p>

        <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto mt-12">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Flashcards</h3>
            <p className="text-gray-600 text-sm">
              Build vocabulary with spaced repetition using the SM-2 algorithm
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Translation Drills</h3>
            <p className="text-gray-600 text-sm">
              Practice translation with LLM-powered exercises and feedback
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Multiple Languages</h3>
            <p className="text-gray-600 text-sm">
              Biblical Hebrew, Latin, Greek, Sanskrit, Pali, and more
            </p>
          </div>
        </div>

        <div className="mt-16 grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {/* Biblical Hebrew */}
          <div className="bg-white rounded-xl shadow-md p-8 text-left">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-3xl font-hebrew">בְּ</span>
              <div>
                <h2 className="text-xl font-bold text-gray-900">Biblical Hebrew</h2>
                <p className="text-xs text-gray-500">Lambdin's Introduction</p>
              </div>
            </div>
            <p className="text-gray-600 text-sm mb-5">
              Read the Hebrew Bible in the original. Learn the alphabet, vowel
              pointing, and vocabulary lesson by lesson.
            </p>
            <div className="flex flex-col gap-2">
              <Link
                to="/hebrew/alphabet"
                className="text-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
              >
                Learn the Alphabet
              </Link>
              <Link
                to="/hebrew/lesson/01"
                className="text-center px-4 py-2 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 text-sm"
              >
                Lesson 1 Vocabulary
              </Link>
              <Link
                to="/exercises/hebrew"
                className="text-center px-4 py-2 border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-50 text-sm"
              >
                Grammar Exercises
              </Link>
            </div>
          </div>

          {/* Latin */}
          <div className="bg-white rounded-xl shadow-md p-8 text-left">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-3xl font-serif font-bold text-gray-700">L</span>
              <div>
                <h2 className="text-xl font-bold text-gray-900">Latin</h2>
                <p className="text-xs text-gray-500">Wheelock's Latin</p>
              </div>
            </div>
            <p className="text-gray-600 text-sm mb-5">
              Read Caesar, Cicero, and Virgil. Build vocabulary from Wheelock's
              Latin through flashcards and spaced repetition.
            </p>
            <div className="flex flex-col gap-2">
              <Link
                to="/latin/lesson/01"
                className="text-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
              >
                Lesson 1 Vocabulary
              </Link>
              <Link
                to="/latin/lesson/02"
                className="text-center px-4 py-2 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 text-sm"
              >
                Lesson 2 Vocabulary
              </Link>
              <Link
                to="/exercises/latin"
                className="text-center px-4 py-2 border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-50 text-sm"
              >
                Grammar Exercises
              </Link>
            </div>
          </div>

          {/* Ancient Greek */}
          <div className="bg-white rounded-xl shadow-md p-8 text-left">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-3xl font-serif font-bold text-gray-700">α</span>
              <div>
                <h2 className="text-xl font-bold text-gray-900">Ancient Greek</h2>
                <p className="text-xs text-gray-500">Attic dialect</p>
              </div>
            </div>
            <p className="text-gray-600 text-sm mb-5">
              Read Plato, Thucydides, and Sophocles. Master Attic Greek grammar
              through vocabulary lessons and declension drills.
            </p>
            <div className="flex flex-col gap-2">
              <Link
                to="/greek/lesson/1"
                className="text-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
              >
                Lesson 1 Vocabulary
              </Link>
              <Link
                to="/greek/lesson/2"
                className="text-center px-4 py-2 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 text-sm"
              >
                Lesson 2 Vocabulary
              </Link>
              <Link
                to="/exercises/greek"
                className="text-center px-4 py-2 border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-50 text-sm"
              >
                Grammar Exercises
              </Link>
            </div>
          </div>

          {/* NT Greek */}
          <div className="bg-white rounded-xl shadow-md p-8 text-left">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-3xl font-serif font-bold text-gray-700">κ</span>
              <div>
                <h2 className="text-xl font-bold text-gray-900">NT Greek</h2>
                <p className="text-xs text-gray-500">Koine dialect</p>
              </div>
            </div>
            <p className="text-gray-600 text-sm mb-5">
              Read the New Testament in the original Greek. Learn Koine vocabulary
              and grammar through lessons and conjugation drills.
            </p>
            <div className="flex flex-col gap-2">
              <Link
                to="/nt-greek/lesson/1"
                className="text-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
              >
                Lesson 1 Vocabulary
              </Link>
              <Link
                to="/nt-greek/lesson/2"
                className="text-center px-4 py-2 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 text-sm"
              >
                Lesson 2 Vocabulary
              </Link>
              <Link
                to="/exercises/nt-greek"
                className="text-center px-4 py-2 border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-50 text-sm"
              >
                Grammar Exercises
              </Link>
            </div>
          </div>

          {/* Sanskrit */}
          <div className="bg-white rounded-xl shadow-md p-8 text-left">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-3xl font-serif font-bold text-gray-700">अ</span>
              <div>
                <h2 className="text-xl font-bold text-gray-900">Sanskrit</h2>
                <p className="text-xs text-gray-500">Classical Sanskrit</p>
              </div>
            </div>
            <p className="text-gray-600 text-sm mb-5">
              Read the Bhagavad Gita and Upanishads. Learn Devanagari script and
              Classical Sanskrit grammar through IAST-based exercises.
            </p>
            <div className="flex flex-col gap-2">
              <Link
                to="/sanskrit/lesson/1"
                className="text-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
              >
                Lesson 1 Vocabulary
              </Link>
              <Link
                to="/sanskrit/lesson/2"
                className="text-center px-4 py-2 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 text-sm"
              >
                Lesson 2 Vocabulary
              </Link>
              <Link
                to="/exercises/sanskrit"
                className="text-center px-4 py-2 border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-50 text-sm"
              >
                Grammar Exercises
              </Link>
            </div>
          </div>

          {/* Ecclesiastical Latin */}
          <div className="bg-white rounded-xl shadow-md p-8 text-left">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-3xl font-serif font-bold text-gray-700">E</span>
              <div>
                <h2 className="text-xl font-bold text-gray-900">Ecclesiastical Latin</h2>
                <p className="text-xs text-gray-500">Jerome's Vulgate &amp; Church Fathers</p>
              </div>
            </div>
            <p className="text-gray-600 text-sm mb-5">
              Read the Vulgate Bible and the Church Fathers. Learn the Latin of
              the Christian tradition through vocabulary and grammar drills.
            </p>
            <div className="flex flex-col gap-2">
              <Link
                to="/ecclesiastical-latin/lesson/1"
                className="text-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
              >
                Lesson 1 Vocabulary
              </Link>
              <Link
                to="/ecclesiastical-latin/lesson/2"
                className="text-center px-4 py-2 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 text-sm"
              >
                Lesson 2 Vocabulary
              </Link>
              <Link
                to="/exercises/ecclesiastical-latin"
                className="text-center px-4 py-2 border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-50 text-sm"
              >
                Grammar Exercises
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
