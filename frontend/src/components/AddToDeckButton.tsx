import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useLazyQuery, useMutation } from '@apollo/client'
import { CREATE_CARD, PRIMARY_DECK } from '@/graphql/operations'
import { useAuth } from '@/contexts/AuthContext'

const LANGUAGE_LABELS: Record<string, string> = {
  BIBLICAL_HEBREW: 'Biblical Hebrew',
  LATIN: 'Latin',
  ECCLESIASTICAL_LATIN: 'Ecclesiastical Latin',
  ANCIENT_GREEK: 'Ancient Greek',
  NT_GREEK: 'NT Greek',
  SANSKRIT: 'Sanskrit',
  PALI: 'Pali',
  BUDDHIST_HYBRID_SANSKRIT: 'Buddhist Hybrid Sanskrit',
  ARAMAIC: 'Aramaic',
  MIDRASHIC_HEBREW: 'Midrashic Hebrew',
}

interface PrimaryDeckResult {
  primaryDeck: { id: string; name: string; language: string } | null
}

interface AddToDeckButtonProps {
  language: keyof typeof LANGUAGE_LABELS | string
  front: string
  back: string
  transliteration?: string | null
  grammaticalInfo?: string | null
  notes?: string | null
  sourceReference?: string | null
}

export function AddToDeckButton({
  language,
  front,
  back,
  transliteration,
  grammaticalInfo,
  notes,
  sourceReference,
}: AddToDeckButtonProps) {
  const { user } = useAuth()
  const location = useLocation()
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [noPrimary, setNoPrimary] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const [fetchPrimaryDeck] = useLazyQuery<PrimaryDeckResult>(PRIMARY_DECK, {
    variables: { language },
    fetchPolicy: 'network-only',
  })
  const [createCard] = useMutation(CREATE_CARD)

  if (!user) {
    return (
      <span onClick={(e) => e.stopPropagation()}>
        <Link
          to="/login"
          state={{ from: location.pathname + location.search }}
          className="text-xs text-stone-400 hover:text-blue-600 underline"
        >
          Sign in to save
        </Link>
      </span>
    )
  }

  const languageLabel = LANGUAGE_LABELS[language] ?? language

  const handleClick = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (submitting || saved) return
    setSubmitting(true)
    setError(null)
    setNoPrimary(false)
    try {
      const { data } = await fetchPrimaryDeck()
      const primary = data?.primaryDeck
      if (!primary) {
        setNoPrimary(true)
        return
      }
      await createCard({
        variables: {
          input: {
            deckId: primary.id,
            front,
            back,
            transliteration: transliteration ?? null,
            grammaticalInfo: grammaticalInfo ?? null,
            notes: notes ?? null,
            sourceReference: sourceReference ?? null,
          },
        },
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 1500)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <span className="inline-flex flex-col items-start gap-0.5">
      <button
        type="button"
        onClick={handleClick}
        disabled={submitting}
        className={`text-xs px-2 py-0.5 rounded border transition-colors ${
          saved
            ? 'bg-emerald-50 border-emerald-300 text-emerald-700'
            : 'bg-white border-stone-300 text-stone-600 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700 disabled:opacity-50'
        }`}
        title={`Save to primary ${languageLabel} deck`}
      >
        {saved ? '✓ Saved' : submitting ? 'Saving…' : '+ Add to deck'}
      </button>
      {noPrimary && (
        <span className="text-[11px] text-stone-500" onClick={(e) => e.stopPropagation()}>
          No primary deck for {languageLabel}.{' '}
          <Link to="/decks" className="text-blue-600 hover:underline">
            Set one on the Decks page
          </Link>
          .
        </span>
      )}
      {error && (
        <span className="text-[11px] text-red-600">{error}</span>
      )}
    </span>
  )
}
