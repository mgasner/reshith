import { useState, useEffect } from 'react'
import { HebrewInput } from '@/components/HebrewInput'

export interface GradeResult {
  correct: boolean
  feedback: string
  expected?: string
}

interface ExerciseRunnerProps<T extends { id: string }> {
  title: string
  description?: string
  exercises: T[]
  loading: boolean
  onRefetch: () => void
  /** Render the question/prompt shown to the user */
  renderPrompt: (exercise: T) => React.ReactNode
  /** 'english' = plain text input, 'hebrew' = HebrewInput, 'reveal' = click-to-reveal (no grading) */
  inputMode: 'english' | 'hebrew' | 'reveal'
  onGrade?: (exercise: T, answer: string) => Promise<GradeResult>
  /** Content revealed on click when inputMode is 'reveal' */
  renderReveal?: (exercise: T) => React.ReactNode
  controls?: React.ReactNode
}

export function ExerciseRunner<T extends { id: string }>({
  title,
  description,
  exercises,
  loading,
  onRefetch,
  renderPrompt,
  inputMode,
  onGrade,
  renderReveal,
  controls,
}: ExerciseRunnerProps<T>) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [userAnswer, setUserAnswer] = useState('')
  const [feedback, setFeedback] = useState<GradeResult | null>(null)
  const [score, setScore] = useState({ correct: 0, total: 0 })
  const [revealed, setRevealed] = useState(false)

  useEffect(() => {
    setCurrentIndex(0)
    setUserAnswer('')
    setFeedback(null)
    setRevealed(false)
    setScore({ correct: 0, total: 0 })
  }, [exercises])

  const handleNewSet = () => {
    onRefetch()
    setCurrentIndex(0)
    setUserAnswer('')
    setFeedback(null)
    setRevealed(false)
    setScore({ correct: 0, total: 0 })
  }

  const handleSubmit = async () => {
    const exercise = exercises[currentIndex]
    if (!exercise || !onGrade || !userAnswer.trim()) return
    const result = await onGrade(exercise, userAnswer)
    setFeedback(result)
    setScore((prev) => ({
      correct: prev.correct + (result.correct ? 1 : 0),
      total: prev.total + 1,
    }))
  }

  const handleNext = () => {
    setCurrentIndex((i) => i + 1)
    setUserAnswer('')
    setFeedback(null)
    setRevealed(false)
  }

  if (loading) {
    return (
      <div className="px-4 text-center py-12">
        <p className="text-gray-500">Loading exercises...</p>
      </div>
    )
  }

  const exercise = exercises[currentIndex]

  if (!exercise) {
    return (
      <div className="px-4 text-center py-12">
        <p className="text-gray-500">No exercises available</p>
        <button
          onClick={handleNewSet}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Try Again
        </button>
      </div>
    )
  }

  const isComplete = currentIndex === exercises.length - 1 && (feedback !== null || revealed)

  return (
    <div className="px-4 max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
        {description && <p className="text-gray-600">{description}</p>}
      </div>

      {controls && <div className="mb-6 flex flex-wrap gap-4">{controls}</div>}

      <div className="mb-4 flex justify-between items-center">
        <span className="text-sm text-gray-600">
          {currentIndex + 1} / {exercises.length}
        </span>
        {inputMode !== 'reveal' && (
          <span className="text-sm text-gray-600">
            Score: {score.correct}/{score.total}
          </span>
        )}
      </div>

      <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
        <div className="text-center mb-6">{renderPrompt(exercise)}</div>

        {inputMode === 'reveal' ? (
          <div>
            {!revealed ? (
              <button
                onClick={() => setRevealed(true)}
                className="w-full py-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-400 hover:border-blue-400 hover:text-blue-500 transition-colors"
              >
                Click to reveal
              </button>
            ) : (
              <div className="p-4 bg-blue-50 rounded-lg text-center">
                {renderReveal?.(exercise)}
              </div>
            )}
          </div>
        ) : (
          <div className="mb-4">
            {inputMode === 'hebrew' ? (
              <HebrewInput
                value={userAnswer}
                onChange={setUserAnswer}
                placeholder="Type your answer..."
              />
            ) : (
              <input
                type="text"
                value={userAnswer}
                onChange={(e) => setUserAnswer(e.target.value)}
                placeholder="Type your answer..."
                className="w-full p-4 border-2 border-gray-300 rounded-lg text-xl focus:border-blue-500 focus:outline-none"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !feedback) handleSubmit()
                }}
              />
            )}
          </div>
        )}

        {feedback && (
          <div
            className={`p-4 rounded-lg mb-4 ${
              feedback.correct ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            }`}
          >
            <p className="font-medium">{feedback.feedback}</p>
            {!feedback.correct && feedback.expected && (
              <p className="text-sm mt-1 opacity-80">Expected: {feedback.expected}</p>
            )}
          </div>
        )}

        {inputMode !== 'reveal' && (
          <div className="flex justify-center gap-4">
            {!feedback ? (
              <button
                onClick={handleSubmit}
                disabled={!userAnswer.trim()}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Check Answer
              </button>
            ) : isComplete ? (
              <button
                onClick={handleNewSet}
                className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                New Set
              </button>
            ) : (
              <button
                onClick={handleNext}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Next
              </button>
            )}
          </div>
        )}

        {inputMode === 'reveal' && (
          <div className="flex justify-center gap-4 mt-4">
            {isComplete ? (
              <button
                onClick={handleNewSet}
                className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                New Set
              </button>
            ) : revealed ? (
              <button
                onClick={handleNext}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Next
              </button>
            ) : null}
          </div>
        )}
      </div>

      {isComplete && inputMode !== 'reveal' && (
        <div className="bg-blue-50 rounded-lg p-6 text-center">
          <h2 className="text-xl font-bold text-blue-900 mb-2">Set Complete!</h2>
          <p className="text-blue-800">
            {score.correct} / {score.total} correct (
            {score.total > 0 ? Math.round((score.correct / score.total) * 100) : 0}%)
          </p>
        </div>
      )}
    </div>
  )
}
