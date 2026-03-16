import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation } from '@apollo/client'
import {
  GET_LATIN_DECLENSION_EXERCISES,
  GRADE_LATIN_DECLENSION_EXERCISE,
} from '@/graphql/operations'

interface Exercise {
  id: string
  dictForm: string
  definition: string
  case: string
  number: string
  prompt: string
  answer: string
  lesson: number
  variant: string
}

export function EcclesiasticalLatinDeclensionExercisePage() {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [userAnswer, setUserAnswer] = useState('')
  const [feedback, setFeedback] = useState<{ correct: boolean; message: string } | null>(null)
  const [score, setScore] = useState({ correct: 0, total: 0 })
  const [maxLesson, setMaxLesson] = useState(2)

  const { data, loading, refetch } = useQuery(GET_LATIN_DECLENSION_EXERCISES, {
    variables: { count: 10, maxLesson, variant: 'ECCLESIASTICAL' },
    fetchPolicy: 'network-only',
  })

  const [gradeExercise] = useMutation(GRADE_LATIN_DECLENSION_EXERCISE)

  const exercises: Exercise[] = data?.latinDeclensionExercises || []
  const currentExercise = exercises[currentIndex]

  useEffect(() => {
    setCurrentIndex(0)
    setUserAnswer('')
    setFeedback(null)
    setScore({ correct: 0, total: 0 })
  }, [maxLesson])

  const handleNewSet = () => {
    refetch()
    setCurrentIndex(0)
    setUserAnswer('')
    setFeedback(null)
    setScore({ correct: 0, total: 0 })
  }

  const handleSubmit = async () => {
    if (!currentExercise || !userAnswer.trim()) return
    try {
      const result = await gradeExercise({
        variables: {
          input: {
            exerciseId: currentExercise.id,
            submitted: userAnswer,
            expected: currentExercise.answer,
          },
        },
      })
      const gradeResult = result.data?.gradeLatinDeclensionExercise
      if (gradeResult) {
        setFeedback({ correct: gradeResult.correct, message: gradeResult.feedback })
        setScore((prev) => ({
          correct: prev.correct + (gradeResult.correct ? 1 : 0),
          total: prev.total + 1,
        }))
      }
    } catch (error) {
      console.error('Failed to grade exercise:', error)
    }
  }

  const handleNext = () => {
    if (currentIndex < exercises.length - 1) {
      setCurrentIndex(currentIndex + 1)
      setUserAnswer('')
      setFeedback(null)
    }
  }

  if (loading) {
    return (
      <div className="px-4 text-center py-12">
        <p className="text-gray-500">Loading exercises...</p>
      </div>
    )
  }

  if (!currentExercise) {
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

  const isComplete = currentIndex === exercises.length - 1 && feedback !== null

  return (
    <div className="px-4 max-w-2xl mx-auto">
      <div className="mb-6">
        <Link to="/exercises/ecclesiastical-latin" className="text-sm text-blue-600 hover:underline mb-2 block">
          ← Ecclesiastical Latin Exercises
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">Ecclesiastical Latin — Noun Declension</h1>
        <p className="text-gray-600">
          Produce the correct declined form for the given case and number.
        </p>
      </div>

      <div className="mb-6 flex flex-wrap gap-4">
        <div>
          <label className="block text-sm text-gray-600 mb-1">Vocabulary</label>
          <select
            value={maxLesson}
            onChange={(e) => setMaxLesson(Number(e.target.value))}
            className="px-3 py-2 border rounded-lg"
          >
            <option value={1}>Lesson 1 (1st declension)</option>
            <option value={2}>Lessons 1–2 (1st &amp; 2nd declension)</option>
            <option value={3}>Lessons 1–3 (all)</option>
          </select>
        </div>
        <div className="flex items-end">
          <button
            onClick={handleNewSet}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
          >
            New Set
          </button>
        </div>
      </div>

      <div className="mb-4 flex justify-between items-center">
        <span className="text-sm text-gray-600">
          Question {currentIndex + 1} of {exercises.length}
        </span>
        <span className="text-sm text-gray-600">
          Score: {score.correct}/{score.total}
        </span>
      </div>

      <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
        <div className="text-center mb-6">
          <p className="text-sm text-gray-500 mb-1">Dictionary form</p>
          <p className="text-2xl font-serif font-semibold">{currentExercise.dictForm}</p>
          <p className="text-sm text-gray-500 italic mt-1">{currentExercise.definition}</p>
          <p className="text-lg font-medium text-blue-700 mt-4">{currentExercise.prompt.replace(/^Give the/, 'Give the')}</p>
        </div>

        <div className="mb-4">
          <input
            type="text"
            value={userAnswer}
            onChange={(e) => setUserAnswer(e.target.value)}
            placeholder="Type the declined form..."
            className="w-full p-4 border-2 border-gray-300 rounded-lg text-xl font-serif focus:border-blue-500 focus:outline-none"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !feedback) handleSubmit()
            }}
            autoFocus
          />
          <p className="text-xs text-gray-400 mt-1">
            Macrons optional (e.g. "puellae" accepted for "puellae")
          </p>
        </div>

        {feedback && (
          <div
            className={`p-4 rounded-lg mb-4 ${
              feedback.correct ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            }`}
          >
            <p className="font-medium">{feedback.message}</p>
          </div>
        )}

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
              Start New Set
            </button>
          ) : (
            <button
              onClick={handleNext}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Next Question
            </button>
          )}
        </div>
      </div>

      {isComplete && (
        <div className="bg-blue-50 rounded-lg p-6 text-center">
          <h2 className="text-xl font-bold text-blue-900 mb-2">Set Complete!</h2>
          <p className="text-blue-800">
            You got {score.correct} out of {score.total} correct (
            {Math.round((score.correct / score.total) * 100)}%)
          </p>
        </div>
      )}
    </div>
  )
}
