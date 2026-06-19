import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation } from '@apollo/client'
import { useAuth } from '@/contexts/AuthContext'
import { GET_DECKS, IMPORT_LESSON_TO_DECK } from '@/graphql/operations'

interface Props {
  language: string         // GraphQL LanguageCode enum value (e.g. "BIBLICAL_HEBREW")
  lessonId: string         // e.g. "01" or "alphabet"
  deckName?: string
}

interface ImportedDeck {
  id: string
  name: string
  cardCount: number
}

export function AddToSRSButton({ language, lessonId, deckName }: Props) {
  const { user } = useAuth()
  const [importLesson, { loading }] = useMutation<{ importLesson: ImportedDeck }>(
    IMPORT_LESSON_TO_DECK,
    { refetchQueries: [{ query: GET_DECKS }] }
  )
  const [deck, setDeck] = useState<ImportedDeck | null>(null)
  const [error, setError] = useState<string | null>(null)

  if (!user) return null

  const onClick = async () => {
    setError(null)
    try {
      const res = await importLesson({
        variables: { input: { language, lessonId, deckName } },
      })
      if (res.data?.importLesson) setDeck(res.data.importLesson)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  return (
    <div className="flex items-center gap-3">
      <button
        onClick={onClick}
        disabled={loading}
        className="px-3 py-1.5 text-sm bg-emerald-600 text-white rounded hover:bg-emerald-700 disabled:opacity-50"
      >
        {loading ? 'Adding…' : 'Add to SRS'}
      </button>
      {deck && (
        <span className="text-sm text-gray-600">
          Imported {deck.cardCount} cards →{' '}
          <Link to={`/study/${deck.id}`} className="text-blue-600 hover:underline">
            Study now
          </Link>
        </span>
      )}
      {error && <span className="text-sm text-red-600">{error}</span>}
    </div>
  )
}
