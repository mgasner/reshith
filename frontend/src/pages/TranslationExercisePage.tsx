import { useState } from 'react'
import { useQuery, useMutation } from '@apollo/client'
import { ExerciseRunner } from '@/components/ExerciseRunner'
import { GET_TRANSLATION_EXERCISES, GRADE_TRANSLATION_EXERCISE } from '@/graphql/operations'

interface TranslationExercise {
  id: string
  pattern: string
  english: string
  hebrewAnswer: string
  transliterationAnswer: string
  components: string
}

export function TranslationExercisePage() {
  const [maxLesson, setMaxLesson] = useState(5)

  const { data, loading, refetch } = useQuery(GET_TRANSLATION_EXERCISES, {
    variables: { count: 10, maxLesson, patterns: null },
    fetchPolicy: 'network-only',
  })

  const [gradeExercise] = useMutation(GRADE_TRANSLATION_EXERCISE)

  const exercises: TranslationExercise[] = data?.translationExercises ?? []

  return (
    <ExerciseRunner
      title="Translation Exercises"
      description="Translate English sentences into Hebrew."
      exercises={exercises}
      loading={loading}
      onRefetch={() => refetch()}
      inputMode="hebrew"
      renderPrompt={(ex) => (
        <>
          <p className="text-sm text-gray-500 mb-2">Translate to Hebrew:</p>
          <p className="text-2xl text-gray-900">{ex.english}</p>
        </>
      )}
      onGrade={async (ex, answer) => {
        const result = await gradeExercise({
          variables: {
            input: {
              exerciseId: ex.id,
              submitted: answer,
              expectedHebrew: ex.hebrewAnswer,
              expectedTransliteration: ex.transliterationAnswer,
            },
          },
        })
        const r = result.data?.gradeTranslationExercise
        return {
          correct: r.correct,
          feedback: r.feedback,
          expected: `${r.expected} (${r.transliteration})`,
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
