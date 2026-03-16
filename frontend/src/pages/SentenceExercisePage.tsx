import { useState } from 'react'
import { useQuery } from '@apollo/client'
import { ExerciseRunner } from '@/components/ExerciseRunner'
import { GET_SENTENCE_EXERCISES } from '@/graphql/operations'

interface SentenceExercise {
  id: string
  pattern: string
  hebrew: string
  transliteration: string
  english: string
  components: string
}

export function SentenceExercisePage() {
  const [maxLesson, setMaxLesson] = useState(5)

  const { data, loading, refetch } = useQuery(GET_SENTENCE_EXERCISES, {
    variables: { count: 10, maxLesson, patterns: null },
    fetchPolicy: 'network-only',
  })

  const exercises: SentenceExercise[] = data?.sentenceExercises ?? []

  return (
    <ExerciseRunner
      title="Sentence Reading"
      description="Read Hebrew sentences and reveal the English translation."
      exercises={exercises}
      loading={loading}
      onRefetch={() => refetch()}
      inputMode="reveal"
      renderPrompt={(ex) => (
        <>
          <p className="text-3xl font-hebrew rtl leading-relaxed">{ex.hebrew}</p>
          <p className="text-base text-gray-500 mt-3">{ex.transliteration}</p>
        </>
      )}
      renderReveal={(ex) => (
        <p className="text-xl text-blue-900">{ex.english}</p>
      )}
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
