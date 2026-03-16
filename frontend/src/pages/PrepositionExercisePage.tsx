import { useState, useEffect } from 'react'
import { useQuery, useMutation } from '@apollo/client'
import { HebrewInput } from '@/components/HebrewInput'
import {
  GET_PREPOSITION_EXERCISES,
  GRADE_PREPOSITION_EXERCISE,
} from '@/graphql/operations'

interface Exercise {
  id: string
  hebrew: string
  transliteration: string
  english: string
  preposition: string
  nounHebrew: string
  nounDefinition: string
  direction: string
  prompt: string
  answer: string
}

type ExerciseDirection = 'HEBREW_TO_ENGLISH' | 'ENGLISH_TO_HEBREW'

export function PrepositionExercisePage() {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [userAnswer, setUserAnswer] = useState('')
  const [feedback, setFeedback] = useState<{
    correct: boolean
    message: string
  } | null>(null)
  const [score, setScore] = useState({ correct: 0, total: 0 })
  const [direction, setDirection] = useState<ExerciseDirection>('HEBREW_TO_ENGLISH')
  const [maxLesson, setMaxLesson] = useState(1)

  const { data, loading, refetch } = useQuery(GET_PREPOSITION_EXERCISES, {
    variables: {
      count: 10,
      direction,
      maxLesson,
    },
    fetchPolicy: 'network-only',
  })

  const [gradeExercise] = useMutation(GRADE_PREPOSITION_EXERCISE)

  const exercises: Exercise[] = data?.prepositionExercises || []
  const currentExercise = exercises[currentIndex]

  useEffect(() => {
    setCurrentIndex(0)
    setUserAnswer('')
    setFeedback(null)
    setScore({ correct: 0, total: 0 })
  }, [direction, maxLesson])

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
            direction: direction,
            expectedHebrew: currentExercise.hebrew,
            expectedEnglish: currentExercise.english,
          },
        },
      })

      const gradeResult = result.data?.gradePrepositionExercise
      if (gradeResult) {
        setFeedback({
          correct: gradeResult.correct,
          message: gradeResult.feedback,
        })
        setScore((prev) => ({
          correct: prev.correct + (gradeResult.correct ? 1 : 0),
          total: prev.total + 1,
        }))
      }
    } catch (error) {
      console.error('Failed to grade exercise:', error)
      setFeedback({
        correct: false,
        message: 'Failed to grade exercise. Please try again.',
      })
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
  const isHebrewToEnglish = direction === 'HEBREW_TO_ENGLISH'

  return (
    <div className="px-4 max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Preposition Exercises</h1>
        <p className="text-gray-600">
          Practice the inseparable prepositions: בְּ (bə-, in), לְ (lə-, to), כְּ (kə-, like)
        </p>
      </div>

      <div className="mb-6 flex flex-wrap gap-4">
        <div>
          <label className="block text-sm text-gray-600 mb-1">Direction</label>
          <select
            value={direction}
            onChange={(e) => setDirection(e.target.value as ExerciseDirection)}
            className="px-3 py-2 border rounded-lg"
          >
            <option value="HEBREW_TO_ENGLISH">Hebrew → English</option>
            <option value="ENGLISH_TO_HEBREW">English → Hebrew</option>
          </select>
        </div>
        <div>
          <label className="block text-sm text-gray-600 mb-1">Vocabulary</label>
          <select
            value={maxLesson}
            onChange={(e) => setMaxLesson(Number(e.target.value))}
            className="px-3 py-2 border rounded-lg"
          >
            <option value={1}>Lesson 1 only</option>
            <option value={2}>Lessons 1-2</option>
            <option value={3}>Lessons 1-3</option>
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
          <p className="text-sm text-gray-500 mb-2">Translate:</p>
          <p
            className={`text-4xl ${isHebrewToEnglish ? 'font-hebrew rtl' : ''}`}
          >
            {currentExercise.prompt}
          </p>
          {isHebrewToEnglish && (
            <p className="text-lg text-gray-500 mt-2">
              ({currentExercise.transliteration})
            </p>
          )}
        </div>

        <div className="mb-4">
          {!isHebrewToEnglish ? (
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
                if (e.key === 'Enter' && !feedback) {
                  handleSubmit()
                }
              }}
            />
          )}
        </div>

        {feedback && (
          <div
            className={`p-4 rounded-lg mb-4 ${
              feedback.correct
                ? 'bg-green-100 text-green-800'
                : 'bg-red-100 text-red-800'
            }`}
          >
            <p className="font-medium">{feedback.message}</p>
            {!feedback.correct && !isHebrewToEnglish && (
              <p className="text-sm mt-1 font-hebrew rtl">
                {currentExercise.answer}
              </p>
            )}
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
