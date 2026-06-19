import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useLazyQuery, useMutation, useQuery } from '@apollo/client'
import {
  CREATE_CARD,
  CREATE_DECK,
  GET_USER_API_KEYS,
  PRIMARY_DECK,
  SET_PRIMARY_DECK,
  SUGGEST_LEMMA_GLOSS,
} from '@/graphql/operations'
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

interface CreateDeckResult {
  createDeck: { id: string; name: string; language: string; isPrimary: boolean }
}

interface UserAPIKeysQueryResult {
  userApiKeys: {
    hasOpenaiKey: boolean
    hasAnthropicKey: boolean
    llmLemmaAssist: boolean
  }
}

interface SuggestLemmaGlossResult {
  suggestLemmaGloss: {
    available: boolean
    message: string | null
    lemma: string | null
    gloss: string | null
    transliteration: string | null
    notes: string | null
  }
}

interface AddToDeckButtonProps {
  language: keyof typeof LANGUAGE_LABELS | string
  /** Front of the card. May be empty when assist is expected to fill it. */
  front?: string
  /** Back of the card. May be empty when assist is expected to fill it. */
  back?: string
  transliteration?: string | null
  grammaticalInfo?: string | null
  notes?: string | null
  sourceReference?: string | null
  /**
   * Surface form of the token as it appears in the text. Used as input to
   * the LLM lemma/gloss assist and stashed in `notes` so the saved card
   * keeps track of how the user encountered the word.
   */
  surfaceForm?: string
  /**
   * Optional lemma hint from the morphological analyzer — passed to the LLM
   * assist when the corpus knows the lemma but not the gloss (Vulgate,
   * Lanman without an MW entry, etc.).
   */
  lemmaHint?: string | null
  /**
   * Surrounding text (typically the verse) for LLM disambiguation of
   * homographs. Optional but improves suggestion quality.
   */
  assistContext?: string | null
}

export function AddToDeckButton({
  language,
  front,
  back,
  transliteration,
  grammaticalInfo,
  notes,
  sourceReference,
  surfaceForm,
  lemmaHint,
  assistContext,
}: AddToDeckButtonProps) {
  const { user } = useAuth()
  const location = useLocation()
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const { data: apiKeysData } = useQuery<UserAPIKeysQueryResult>(
    GET_USER_API_KEYS,
    { skip: !user, fetchPolicy: 'cache-first' },
  )
  const llmAssistEnabled = !!apiKeysData?.userApiKeys?.llmLemmaAssist
    && (apiKeysData.userApiKeys.hasOpenaiKey
      || apiKeysData.userApiKeys.hasAnthropicKey)

  const [fetchPrimaryDeck] = useLazyQuery<PrimaryDeckResult>(PRIMARY_DECK, {
    variables: { language },
    fetchPolicy: 'network-only',
  })
  const [createDeck] = useMutation<CreateDeckResult>(CREATE_DECK, {
    refetchQueries: ['GetDecks', 'PrimaryDeck'],
    awaitRefetchQueries: true,
  })
  const [setPrimaryDeck] = useMutation(SET_PRIMARY_DECK, {
    refetchQueries: ['GetDecks', 'PrimaryDeck'],
    awaitRefetchQueries: true,
  })
  const [createCard] = useMutation(CREATE_CARD)
  const [suggestLemmaGloss] = useMutation<SuggestLemmaGlossResult>(
    SUGGEST_LEMMA_GLOSS,
  )

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
  const baseFront = front?.trim() ?? ''
  const baseBack = back?.trim() ?? ''
  const cardComplete = !!baseFront && !!baseBack
  // Hide the button entirely when we have nothing useful to offer: incomplete
  // card data AND assist is off. The viewer's "click to expand" panel still
  // shows the lemma/morphology — the user just can't save it as a card.
  if (!cardComplete && !llmAssistEnabled) {
    return null
  }

  const handleClick = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (submitting || saved) return
    setSubmitting(true)
    setError(null)
    try {
      // 1) Resolve target deck (auto-create primary if missing).
      const { data: primary } = await fetchPrimaryDeck()
      let deckId = primary?.primaryDeck?.id
      if (!deckId) {
        const created = await createDeck({
          variables: {
            input: {
              name: `${languageLabel} Vocab`,
              description: `Words saved from the ${languageLabel} reader`,
              language,
            },
          },
        })
        const newDeck = created.data?.createDeck
        if (!newDeck) throw new Error('Could not create deck')
        if (!newDeck.isPrimary) {
          await setPrimaryDeck({ variables: { deckId: newDeck.id } })
        }
        deckId = newDeck.id
      }

      // 2) Build the card. If the corpus didn't supply a clean lemma/gloss
      //    and the user has assist enabled, ask the LLM to fill the gaps.
      let cardFront = baseFront
      let cardBack = baseBack
      let cardTranslit = transliteration ?? null
      const cardGrammar = grammaticalInfo ?? null
      const noteParts: string[] = []
      if (notes) noteParts.push(notes)
      if (surfaceForm && surfaceForm !== cardFront) {
        noteParts.push(`Form: ${surfaceForm}`)
      }

      if ((!cardFront || !cardBack) && llmAssistEnabled) {
        const assistResp = await suggestLemmaGloss({
          variables: {
            input: {
              language,
              form: surfaceForm || cardFront || lemmaHint || '',
              lemmaHint: lemmaHint ?? null,
              context: assistContext ?? sourceReference ?? null,
            },
          },
        })
        const sug = assistResp.data?.suggestLemmaGloss
        if (sug && !sug.available) {
          throw new Error(sug.message || 'LLM assist unavailable')
        }
        if (sug?.lemma && !cardFront) cardFront = sug.lemma
        if (sug?.gloss && !cardBack) cardBack = sug.gloss
        if (sug?.transliteration && !cardTranslit) cardTranslit = sug.transliteration
        if (sug?.notes) noteParts.push(sug.notes)
      }

      if (!cardFront || !cardBack) {
        throw new Error('Need a lemma and gloss to save a card')
      }

      await createCard({
        variables: {
          input: {
            deckId,
            front: cardFront,
            back: cardBack,
            transliteration: cardTranslit,
            grammaticalInfo: cardGrammar,
            notes: noteParts.length > 0 ? noteParts.join(' · ') : null,
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

  const willUseAssist = !cardComplete && llmAssistEnabled
  const label = saved
    ? '✓ Saved'
    : submitting
      ? willUseAssist ? 'Asking LLM…' : 'Saving…'
      : willUseAssist
        ? '+ Add to deck (LLM)'
        : '+ Add to deck'

  return (
    <span className="inline-flex flex-col items-start gap-0.5">
      <button
        type="button"
        onClick={handleClick}
        disabled={submitting}
        className={`text-xs px-2 py-0.5 rounded border transition-colors ${
          saved
            ? 'bg-emerald-50 border-emerald-300 text-emerald-700'
            : willUseAssist
              ? 'bg-violet-50 border-violet-300 text-violet-700 hover:bg-violet-100 disabled:opacity-50'
              : 'bg-white border-stone-300 text-stone-600 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700 disabled:opacity-50'
        }`}
        title={
          willUseAssist
            ? `Save to primary ${languageLabel} deck (LLM will fill the gloss)`
            : `Save to primary ${languageLabel} deck`
        }
      >
        {label}
      </button>
      {error && (
        <span className="text-[11px] text-red-600">{error}</span>
      )}
    </span>
  )
}
