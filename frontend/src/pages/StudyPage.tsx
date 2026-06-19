import { useMemo, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation } from '@apollo/client'
import { FlashCard } from '@/components/FlashCard'
import { VocabularyCard } from '@/components/VocabularyCard'
import { useAuth } from '@/contexts/AuthContext'
import { GET_DUE_CARDS, SUBMIT_REVIEW } from '@/graphql/operations'

interface DueCard {
  card: {
    id: string
    deckId: string
    front: string
    back: string
    notes?: string | null
    transliteration?: string | null
    grammaticalInfo?: string | null
  }
}

const RTL_FRONTS = /[\u0590-\u05FF]/  // Hebrew block

export function StudyPage() {
  const { deckId } = useParams()
  const { user } = useAuth()
  const [index, setIndex] = useState(0)

  const { data, loading, error, refetch } = useQuery<{ dueCards: DueCard[] }>(GET_DUE_CARDS, {
    variables: { deckId: deckId ?? null, limit: 50 },
    fetchPolicy: 'network-only',
    skip: !user,
  })

  const [submitReview, { loading: submitting }] = useMutation(SUBMIT_REVIEW)

  const cards = data?.dueCards ?? []
  const current = cards[index]

  const useVocabularyCard = useMemo(
    () => !!current?.card.transliteration,
    [current]
  )

  if (!user) {
    return (
      <div className="px-4 text-center py-12 text-gray-600">
        <p>You need to log in to study.</p>
      </div>
    )
  }

  if (loading) {
    return <div className="px-4 text-center py-12 text-gray-500">Loading cards…</div>
  }

  if (error) {
    return (
      <div className="px-4 text-center py-12 text-red-600">
        Failed to load due cards: {error.message}
      </div>
    )
  }

  if (cards.length === 0 || index >= cards.length) {
    return (
      <div className="px-4 text-center py-12">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">All caught up!</h1>
        <p className="text-gray-600 mb-6">No cards are due right now.</p>
        <Link
          to="/decks"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Back to decks
        </Link>
      </div>
    )
  }

  const onReview = async (quality: number) => {
    if (submitting || !current) return
    await submitReview({
      variables: { input: { cardId: current.card.id, quality } },
    })
    if (index + 1 < cards.length) {
      setIndex(index + 1)
    } else {
      // Refetch the queue so newly-due cards (e.g. on lapse) reappear.
      setIndex(0)
      await refetch()
    }
  }

  const isRtl = RTL_FRONTS.test(current.card.front)

  return (
    <div className="px-4">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Study</h1>
        <div className="text-sm text-gray-500">
          Card {index + 1} of {cards.length}
        </div>
      </div>

      {useVocabularyCard ? (
        <VocabularyCard
          key={current.card.id}
          card={{
            category: current.card.grammaticalInfo ?? 'other',
            word: current.card.front,
            hebrew: isRtl ? current.card.front : undefined,
            transliteration: current.card.transliteration ?? '',
            definition: current.card.back,
            notes: current.card.notes ?? undefined,
          }}
          onReview={onReview}
          language={isRtl ? 'hbo' : 'lat'}
        />
      ) : (
        <FlashCard
          key={current.card.id}
          front={current.card.front}
          back={current.card.back}
          transliteration={current.card.transliteration}
          notes={current.card.notes}
          isRtl={isRtl}
          onReview={onReview}
        />
      )}
    </div>
  )
}
