import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@apollo/client'
import { useAuth } from '@/contexts/AuthContext'
import {
  ADVANCE_LESSON,
  GET_LESSON_PROGRESS,
  GET_MY_PROGRESS,
  SET_CURRENT_LESSON,
} from '@/graphql/operations'

interface LanguageStudyConfig {
  /** GraphQL LanguageCode enum value (e.g. "BIBLICAL_HEBREW"). */
  gqlLanguage: string
  /** Display name for headings. */
  displayName: string
  /** Path to the lesson page (lessonId is appended). */
  lessonPath: (lessonNum: string) => string
  /** Path to the exercises hub for this language. */
  exercisesPath: string
}

interface ProgressData {
  lessonProgress: {
    language: string
    currentLesson: number
    totalLessons: number
    vocabTotal: number
    vocabMastered: number
    masteryPercent: number
    dueCount: number
    isReadyToAdvance: boolean
  }
}

/** The self-paced lesson study landing page.
 *
 * Authenticated: shows progress, due review count, current-lesson shortcut,
 * the exercise grid, and an "Advance lesson" CTA that becomes recommended
 * once mastery hits the readiness threshold.
 *
 * Anonymous: degrades to a banner prompting login. The existing exercises
 * page remains accessible directly via its URL.
 */
export function LanguageStudyPage({
  gqlLanguage,
  displayName,
  lessonPath,
  exercisesPath,
}: LanguageStudyConfig) {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [confirmingAdvance, setConfirmingAdvance] = useState(false)

  const { data, loading } = useQuery<ProgressData>(GET_LESSON_PROGRESS, {
    variables: { language: gqlLanguage },
    skip: !user,
  })

  const [advance, { loading: advancing }] = useMutation(ADVANCE_LESSON, {
    refetchQueries: [
      { query: GET_LESSON_PROGRESS, variables: { language: gqlLanguage } },
      { query: GET_MY_PROGRESS },
    ],
  })
  const [setLesson] = useMutation(SET_CURRENT_LESSON, {
    refetchQueries: [
      { query: GET_LESSON_PROGRESS, variables: { language: gqlLanguage } },
      { query: GET_MY_PROGRESS },
    ],
  })

  if (!user) {
    return (
      <div className="px-4 max-w-3xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">{displayName}</h1>
        <div className="bg-blue-50 border border-blue-200 text-blue-900 rounded-xl p-4 mb-6">
          <p className="font-medium">Log in to track your progress.</p>
          <p className="text-sm text-blue-800 mt-1">
            Once signed in, this page will show your current lesson, due
            reviews, and SRS-weighted practice. You can still use the
            exercises directly below without an account.
          </p>
          <div className="mt-3 flex gap-2">
            <Link
              to="/login"
              className="inline-block bg-blue-600 text-white text-sm font-medium px-3 py-1.5 rounded-md hover:bg-blue-700"
            >
              Log in
            </Link>
            <Link
              to="/register"
              className="inline-block bg-white border border-blue-300 text-blue-700 text-sm font-medium px-3 py-1.5 rounded-md hover:bg-blue-50"
            >
              Sign up
            </Link>
          </div>
        </div>
        <Link
          to={exercisesPath}
          className="inline-block text-sm text-blue-700 hover:underline"
        >
          Browse {displayName} exercises →
        </Link>
      </div>
    )
  }

  if (loading || !data) {
    return (
      <div className="px-4 text-center py-12 text-gray-500">
        Loading your progress…
      </div>
    )
  }

  const p = data.lessonProgress
  const masteryPct = Math.round(p.masteryPercent * 100)
  const lessonStr = String(p.currentLesson).padStart(2, '0')

  return (
    <div className="px-4 max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{displayName}</h1>
        <p className="text-gray-600">
          Lesson {p.currentLesson} of {p.totalLessons} —{' '}
          {p.vocabMastered} / {p.vocabTotal} vocab mastered
        </p>
      </div>

      {/* Progress bar */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>Mastery</span>
          <span>{masteryPct}%</span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all"
            style={{ width: `${masteryPct}%` }}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Review queue */}
        <Link
          to="/study"
          className="block bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md hover:border-blue-300 transition-all"
        >
          <h2 className="text-lg font-semibold text-gray-900 mb-1">Review</h2>
          <p className="text-3xl font-bold text-blue-600">{p.dueCount}</p>
          <p className="text-sm text-gray-500">cards due now</p>
        </Link>

        {/* Continue lesson */}
        <Link
          to={lessonPath(lessonStr)}
          className="block bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md hover:border-blue-300 transition-all"
        >
          <h2 className="text-lg font-semibold text-gray-900 mb-1">
            Continue lesson
          </h2>
          <p className="text-3xl font-bold text-gray-900">L{p.currentLesson}</p>
          <p className="text-sm text-gray-500">flashcards & vocab</p>
        </Link>

        {/* Practice exercises */}
        <Link
          to={exercisesPath}
          className="block bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md hover:border-blue-300 transition-all"
        >
          <h2 className="text-lg font-semibold text-gray-900 mb-1">Practice</h2>
          <p className="text-3xl font-bold text-gray-900">→</p>
          <p className="text-sm text-gray-500">SRS-weighted exercises</p>
        </Link>
      </div>

      {/* Advance lesson */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Advance lesson</h2>
          <p className="text-sm text-gray-600">
            {p.currentLesson >= p.totalLessons
              ? "You're on the last available lesson."
              : p.isReadyToAdvance
                ? `You've mastered ${masteryPct}% — ready to move on.`
                : `${masteryPct}% mastered. You can advance anytime.`}
          </p>
        </div>
        <button
          onClick={() => setConfirmingAdvance(true)}
          disabled={advancing || p.currentLesson >= p.totalLessons}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
            p.isReadyToAdvance
              ? 'bg-green-600 text-white hover:bg-green-700'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          {p.isReadyToAdvance ? 'Advance (Recommended)' : 'Advance lesson'}
        </button>
      </div>

      {/* Manual jump back to a previous lesson — useful for review. */}
      {p.totalLessons > 1 && (
        <div className="text-sm text-gray-600">
          <span className="mr-2">Jump to:</span>
          {Array.from({ length: p.totalLessons }, (_, i) => i + 1).map((n) => (
            <button
              key={n}
              onClick={() => setLesson({ variables: { language: gqlLanguage, lesson: n } })}
              className={`mr-1 px-2 py-0.5 rounded text-xs transition-colors ${
                n === p.currentLesson
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              L{n}
            </button>
          ))}
        </div>
      )}

      {/* Confirm advance modal */}
      {confirmingAdvance && (
        <div
          className="fixed inset-0 bg-black/40 flex items-center justify-center z-20"
          onClick={() => setConfirmingAdvance(false)}
        >
          <div
            className="bg-white rounded-xl p-6 max-w-sm mx-4 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Advance to lesson {p.currentLesson + 1}?
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              New vocabulary and exercises will unlock. Existing SRS progress
              is preserved — you can jump back to lesson {p.currentLesson} at
              any time.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setConfirmingAdvance(false)}
                className="px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-100 rounded-md"
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  await advance({ variables: { language: gqlLanguage } })
                  setConfirmingAdvance(false)
                  navigate(lessonPath(String(p.currentLesson + 1).padStart(2, '0')))
                }}
                disabled={advancing}
                className="px-3 py-1.5 text-sm font-medium bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {advancing ? 'Advancing…' : 'Advance'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
