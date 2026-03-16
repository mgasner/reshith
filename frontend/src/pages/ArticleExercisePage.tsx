import { useState } from 'react'
import { useQuery, useMutation } from '@apollo/client'
import { ExerciseRunner } from '@/components/ExerciseRunner'
import { GET_ARTICLE_EXERCISES, GRADE_ARTICLE_EXERCISE } from '@/graphql/operations'

type Direction = 'INDEFINITE_TO_DEFINITE' | 'DEFINITE_TO_INDEFINITE'

interface ArticleExercise {
  id: string
  hebrewIndefinite: string
  hebrewDefinite: string
  transliterationIndefinite: string
  transliterationDefinite: string
  englishIndefinite: string
  englishDefinite: string
  articleType: string
  direction: Direction
  prompt: string
  promptTransliteration: string
  answer: string
  answerTransliteration: string
}

export function ArticleExercisePage() {
  const [direction, setDirection] = useState<Direction>('INDEFINITE_TO_DEFINITE')
  const [maxLesson, setMaxLesson] = useState(5)

  const { data, loading, refetch } = useQuery(GET_ARTICLE_EXERCISES, {
    variables: { count: 10, direction, maxLesson },
    fetchPolicy: 'network-only',
  })

  const [gradeExercise] = useMutation(GRADE_ARTICLE_EXERCISE)

  const exercises: ArticleExercise[] = data?.articleExercises ?? []

  return (
    <ExerciseRunner
      title="Article Exercises"
      description="Practice adding and removing the Hebrew definite article (הַ) with its phonological variations."
      exercises={exercises}
      loading={loading}
      onRefetch={() => refetch()}
      inputMode="hebrew"
      renderPrompt={(ex) => (
        <>
          <p className="text-sm text-gray-500 mb-2">
            {direction === 'INDEFINITE_TO_DEFINITE' ? 'Make definite:' : 'Make indefinite:'}
          </p>
          <p className="text-4xl font-hebrew rtl">{ex.prompt}</p>
          <p className="text-lg text-gray-500 mt-2">{ex.promptTransliteration}</p>
          <p className="text-base text-gray-400 mt-1">
            {direction === 'INDEFINITE_TO_DEFINITE' ? ex.englishIndefinite : ex.englishDefinite}
          </p>
        </>
      )}
      onGrade={async (ex, answer) => {
        const result = await gradeExercise({
          variables: {
            input: {
              exerciseId: ex.id,
              submitted: answer,
              direction,
              expectedDefinite: ex.hebrewDefinite,
              expectedIndefinite: ex.hebrewIndefinite,
            },
          },
        })
        const r = result.data?.gradeArticleExercise
        return {
          correct: r.correct,
          feedback: r.feedback,
          expected: r.expected,
        }
      }}
      controls={
        <>
          <div>
            <label className="block text-sm text-gray-600 mb-1">Direction</label>
            <select
              value={direction}
              onChange={(e) => setDirection(e.target.value as Direction)}
              className="px-3 py-2 border rounded-lg"
            >
              <option value="INDEFINITE_TO_DEFINITE">Add article</option>
              <option value="DEFINITE_TO_INDEFINITE">Remove article</option>
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
              <option value={2}>Lessons 1–2</option>
              <option value={3}>Lessons 1–3</option>
              <option value={4}>Lessons 1–4</option>
              <option value={5}>Lessons 1–5</option>
            </select>
          </div>
        </>
      }
    />
  )
}
