import { useState } from 'react'
import { useQuery, useMutation } from '@apollo/client'
import { ExerciseRunner } from '@/components/ExerciseRunner'
import { GET_VERBAL_EXERCISES, GRADE_VERBAL_EXERCISE } from '@/graphql/operations'

interface VerbalExercise {
  id: string
  pattern: string
  hebrew: string
  transliteration: string
  englishAnswer: string
  components: string
}

export function VerbalExercisePage() {
  const [maxLesson, setMaxLesson] = useState(5)

  const { data, loading, refetch } = useQuery(GET_VERBAL_EXERCISES, {
    variables: { count: 10, maxLesson, patterns: null },
    fetchPolicy: 'network-only',
  })

  const [gradeExercise] = useMutation(GRADE_VERBAL_EXERCISE)

  const exercises: VerbalExercise[] = data?.verbalExercises ?? []

  return (
    <ExerciseRunner
      title="Verbal Exercises"
      description="Translate Hebrew verbal sentences to English."
      exercises={exercises}
      loading={loading}
      onRefetch={() => refetch()}
      inputMode="english"
      renderPrompt={(ex) => (
        <>
          <p className="text-sm text-gray-500 mb-2">Translate to English:</p>
          <p className="text-4xl font-hebrew rtl">{ex.hebrew}</p>
          <p className="text-lg text-gray-500 mt-2">{ex.transliteration}</p>
        </>
      )}
      onGrade={async (ex, answer) => {
        const result = await gradeExercise({
          variables: {
            input: {
              exerciseId: ex.id,
              submitted: answer,
              expectedEnglish: ex.englishAnswer,
            },
          },
        })
        const r = result.data?.gradeVerbalExercise
        return {
          correct: r.correct,
          feedback: r.feedback,
          expected: r.expected,
        }
      }}
      controls={
        <div>
          <label className="block text-sm text-gray-600 mb-1">Vocabulary</label>
          <select
            value={maxLesson}
            onChange={(e) => setMaxLesson(Number(e.target.value))}
            className="px-3 py-2 border rounded-lg"
          >
            <option value={1}>Lesson 1 only</option>
            <option value={2}>Lessons 1–2</option>
            <option value={3}>Lessons 1–3</option>
            <option value={4}>Lessons 1–4</option>
            <option value={5}>Lessons 1–5</option>
          </select>
        </div>
      }
    />
  )
}
