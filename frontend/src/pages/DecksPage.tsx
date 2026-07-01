import { FormEvent, useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery } from '@apollo/client'
import {
  CREATE_DECK,
  CREATE_DECK_FROM_PASSAGE,
  GET_DECKS,
  SET_PRIMARY_DECK,
} from '@/graphql/operations'

const LANGUAGE_NAMES: Record<string, string> = {
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

interface Deck {
  id: string
  name: string
  description: string | null
  language: string
  isPrimary: boolean
  cardCount: number
}

export function DecksPage() {
  const { data, loading, error, refetch } = useQuery<{ decks: Deck[] }>(GET_DECKS)
  const [createDeck, { loading: creating }] = useMutation(CREATE_DECK)
  const [createFromPassage, { loading: generating }] = useMutation(
    CREATE_DECK_FROM_PASSAGE,
  )
  const [setPrimaryDeck] = useMutation(SET_PRIMARY_DECK)
  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [language, setLanguage] = useState('BIBLICAL_HEBREW')
  const [formError, setFormError] = useState<string | null>(null)

  // Passage-based deck generation.
  const [showPassageForm, setShowPassageForm] = useState(false)
  const [reference, setReference] = useState('')
  const [passageName, setPassageName] = useState('')
  const [setPrimary, setSetPrimary] = useState(false)
  const [passageError, setPassageError] = useState<string | null>(null)
  const [passageNotice, setPassageNotice] = useState<string | null>(null)

  async function handleCreate(e: FormEvent) {
    e.preventDefault()
    setFormError(null)
    try {
      await createDeck({
        variables: {
          input: { name, description: description || null, language },
        },
      })
      setName('')
      setDescription('')
      setLanguage('BIBLICAL_HEBREW')
      setShowForm(false)
      await refetch()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to create deck.')
    }
  }

  async function handleCreateFromPassage(e: FormEvent) {
    e.preventDefault()
    setPassageError(null)
    setPassageNotice(null)
    try {
      const res = await createFromPassage({
        variables: {
          input: { reference, name: passageName || null, setPrimary },
        },
      })
      const result = res.data?.createDeckFromPassage
      setReference('')
      setPassageName('')
      setSetPrimary(false)
      setShowPassageForm(false)
      if (result) {
        setPassageNotice(
          `Created \u201c${result.deck.name}\u201d \u2014 ${result.cardCount} word` +
            `${result.cardCount === 1 ? '' : 's'} from ${result.reference}.`,
        )
      }
      await refetch()
    } catch (err) {
      setPassageError(
        err instanceof Error ? err.message : 'Failed to build deck from passage.',
      )
    }
  }

  const decks = data?.decks ?? []

  return (
    <div className="px-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Your Decks</h1>
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setShowPassageForm((v) => !v)
              setShowForm(false)
              setPassageNotice(null)
            }}
            className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700"
          >
            {showPassageForm ? 'Cancel' : 'Deck from passage'}
          </button>
          <button
            onClick={() => {
              setShowForm((v) => !v)
              setShowPassageForm(false)
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            {showForm ? 'Cancel' : 'Create Deck'}
          </button>
        </div>
      </div>

      {passageNotice && !showPassageForm && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg px-4 py-3 mb-6 text-sm">
          {passageNotice}
        </div>
      )}

      {showPassageForm && (
        <form
          onSubmit={handleCreateFromPassage}
          className="bg-white rounded-lg shadow p-6 mb-6 space-y-4"
        >
          <p className="text-sm text-gray-600">
            Auto-build a vocabulary deck from any Hebrew OT or Greek NT passage.
            One card per distinct word (lemma), glossed and parsed.
          </p>
          <div>
            <label
              className="block text-sm font-medium text-gray-700 mb-1"
              htmlFor="passage-ref"
            >
              Passage reference
            </label>
            <input
              id="passage-ref"
              className="w-full border rounded px-3 py-2"
              placeholder="e.g. Genesis 1:1-2:3, John 1:1-18, Psalm 23"
              value={reference}
              onChange={(e) => setReference(e.target.value)}
              required
            />
            <p className="text-xs text-gray-400 mt-1">
              Book + chapter (whole chapter), or a verse range. Hebrew OT and
              Greek NT only.
            </p>
          </div>
          <div>
            <label
              className="block text-sm font-medium text-gray-700 mb-1"
              htmlFor="passage-name"
            >
              Deck name{' '}
              <span className="text-gray-400 font-normal">(optional)</span>
            </label>
            <input
              id="passage-name"
              className="w-full border rounded px-3 py-2"
              placeholder="Defaults to &ldquo;Vocab: &lt;passage&gt;&rdquo;"
              value={passageName}
              onChange={(e) => setPassageName(e.target.value)}
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={setPrimary}
              onChange={(e) => setSetPrimary(e.target.checked)}
            />
            Make this my primary deck for its language
          </label>
          {passageError && <p className="text-sm text-red-600">{passageError}</p>}
          <button
            type="submit"
            disabled={generating}
            className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50"
          >
            {generating ? 'Building\u2026' : 'Build deck'}
          </button>
        </form>
      )}

      {showForm && (
        <form
          onSubmit={handleCreate}
          className="bg-white rounded-lg shadow p-6 mb-6 space-y-4"
        >
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="deck-name">
              Name
            </label>
            <input
              id="deck-name"
              className="w-full border rounded px-3 py-2"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="deck-desc">
              Description <span className="text-gray-400 font-normal">(optional)</span>
            </label>
            <textarea
              id="deck-desc"
              className="w-full border rounded px-3 py-2"
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="deck-lang">
              Language
            </label>
            <select
              id="deck-lang"
              className="w-full border rounded px-3 py-2"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              {Object.entries(LANGUAGE_NAMES).map(([code, label]) => (
                <option key={code} value={code}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          {formError && <p className="text-sm text-red-600">{formError}</p>}
          <button
            type="submit"
            disabled={creating}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {creating ? 'Creating…' : 'Create'}
          </button>
        </form>
      )}

      {loading ? (
        <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
          Loading…
        </div>
      ) : error ? (
        <div className="bg-white rounded-lg shadow p-8 text-center text-red-600">
          {error.message}
        </div>
      ) : decks.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
          <p>No decks yet. Create one above, or open a lesson page and click
            "Add to SRS" to import a vocabulary set.</p>
        </div>
      ) : (
        <ul className="space-y-3">
          {decks.map((deck) => (
            <li
              key={deck.id}
              className="bg-white rounded-lg shadow p-4 flex justify-between items-center gap-3"
            >
              <div className="flex items-start gap-2 min-w-0">
                <button
                  type="button"
                  onClick={async () => {
                    if (deck.isPrimary) return
                    await setPrimaryDeck({ variables: { deckId: deck.id } })
                    await refetch()
                  }}
                  disabled={deck.isPrimary}
                  className={`text-lg leading-none mt-0.5 transition-colors ${
                    deck.isPrimary
                      ? 'text-amber-500 cursor-default'
                      : 'text-stone-300 hover:text-amber-500'
                  }`}
                  title={
                    deck.isPrimary
                      ? `Primary ${LANGUAGE_NAMES[deck.language] ?? deck.language} deck`
                      : `Make primary ${LANGUAGE_NAMES[deck.language] ?? deck.language} deck`
                  }
                  aria-label={deck.isPrimary ? 'Primary deck' : 'Set as primary deck'}
                >
                  {deck.isPrimary ? '★' : '☆'}
                </button>
                <div className="min-w-0">
                  <h2 className="text-lg font-semibold text-gray-900 truncate">{deck.name}</h2>
                  <p className="text-sm text-gray-500">
                    {LANGUAGE_NAMES[deck.language] ?? deck.language} · {deck.cardCount} card
                    {deck.cardCount === 1 ? '' : 's'}
                  </p>
                  {deck.description && (
                    <p className="text-sm text-gray-600 mt-1 truncate">{deck.description}</p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-3 flex-shrink-0">
                <Link
                  to={`/study/${deck.id}`}
                  className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Study
                </Link>
                <Link
                  to={`/decks/${deck.id}/settings`}
                  className="px-3 py-1.5 text-sm bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
                >
                  Settings
                </Link>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
