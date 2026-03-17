import { useState, useCallback, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery, useLazyQuery, useMutation } from '@apollo/client'
import { gql } from '@apollo/client'
import { SYNTHESIZE_SPEECH } from '@/graphql/operations'

// ── GraphQL ──────────────────────────────────────────────────────────────────

const VULGATE_BOOKS = gql`
  query VulgateBooks {
    vulgateBooks {
      abbrev
      name
      chapters
    }
  }
`

const VULGATE_CHAPTER = gql`
  query VulgateChapter($book: String!, $chapter: Int!) {
    vulgateChapter(book: $book, chapter: $chapter) {
      ref
      book
      chapter
      verse
      token
      form
      lemma
      pos
      morphology
      relation
    }
  }
`

const VULGATE_CHAPTER_TRANSLATIONS = gql`
  query VulgateChapterTranslations($book: String!, $chapter: Int!) {
    vulgateChapterTranslations(book: $book, chapter: $chapter) {
      verse
      text
    }
  }
`

const VULGATE_SEARCH = gql`
  query VulgateSearch($query: String!, $limit: Int) {
    vulgateSearch(query: $query, limit: $limit) {
      ref
      book
      chapter
      verse
      token
      form
      lemma
      pos
      morphology
      relation
    }
  }
`

// ── Types ─────────────────────────────────────────────────────────────────────

interface VulgateToken {
  ref: string
  book: string
  chapter: number
  verse: number
  token: number
  form: string
  lemma: string
  pos: string
  morphology: string
  relation: string
}

interface BookInfo {
  abbrev: string
  name: string
  chapters: number
}

interface VerseTranslation {
  verse: number
  text: string
}

// ── Morphology decoder ────────────────────────────────────────────────────────

const POS_NAMES: Record<string, string> = {
  Nb: 'noun',
  Ne: 'proper noun',
  'V-': 'verb',
  'A-': 'adjective',
  Pp: 'personal pronoun',
  Pd: 'demonstrative pronoun',
  Pr: 'relative pronoun',
  Pt: 'interrogative pronoun',
  Pi: 'indefinite pronoun',
  Ps: 'possessive pronoun',
  Pk: 'reflexive pronoun',
  'R-': 'preposition',
  'C-': 'conjunction',
  'G-': 'subordinating conjunction',
  'D-': 'adverb',
  'I-': 'interjection',
  'N-': 'numeral',
  'M-': 'particle',
  'F-': 'foreign',
}

const PERSON: Record<string, string> = { '1': '1st', '2': '2nd', '3': '3rd' }
const NUMBER: Record<string, string> = { s: 'singular', p: 'plural', d: 'dual' }
const TENSE: Record<string, string> = {
  p: 'present', i: 'imperfect', r: 'perfect',
  l: 'pluperfect', f: 'future', t: 'future perfect',
}
const MOOD: Record<string, string> = {
  i: 'indicative', s: 'subjunctive', m: 'imperative',
  n: 'infinitive', p: 'participle', d: 'gerund', g: 'gerundive', u: 'supine',
}
const VOICE: Record<string, string> = { a: 'active', p: 'passive' }
const GENDER: Record<string, string> = { m: 'masculine', f: 'feminine', n: 'neuter' }
const CASE: Record<string, string> = {
  n: 'nominative', a: 'accusative', g: 'genitive',
  d: 'dative', b: 'ablative', v: 'vocative', l: 'locative',
}
const DEGREE: Record<string, string> = { p: 'positive', c: 'comparative', s: 'superlative' }

function decodeMorphology(morph: string): string[] {
  if (!morph || morph.length < 10) return []
  const [person, number, tense, mood, voice, gender, kase, degree] = morph.split('')
  const parts: string[] = []

  if (PERSON[person]) parts.push(PERSON[person])
  if (NUMBER[number]) parts.push(NUMBER[number])
  if (TENSE[tense]) parts.push(TENSE[tense])
  if (MOOD[mood]) parts.push(MOOD[mood])
  if (VOICE[voice]) parts.push(VOICE[voice])
  if (GENDER[gender]) parts.push(GENDER[gender])
  if (CASE[kase]) parts.push(CASE[kase])
  if (DEGREE[degree]) parts.push(DEGREE[degree])

  return parts
}

// ── Word card ─────────────────────────────────────────────────────────────────

function WordCard({ token }: { token: VulgateToken }) {
  const [expanded, setExpanded] = useState(false)
  const morphParts = decodeMorphology(token.morphology)
  const posName = POS_NAMES[token.pos] ?? token.pos

  return (
    <span
      className="inline-block m-1 cursor-pointer select-none"
      onClick={() => setExpanded((e) => !e)}
    >
      {expanded ? (
        <span className="inline-flex flex-col items-start bg-stone-100 border border-stone-300 rounded-lg px-3 py-2 text-sm shadow-sm min-w-[120px] max-w-xs">
          <span className="font-serif text-lg text-stone-900">{token.form}</span>
          <span className="text-stone-600 text-xs mt-0.5">
            {token.lemma} · {posName}
          </span>
          {morphParts.length > 0 && (
            <span className="text-stone-500 text-xs mt-1">{morphParts.join(', ')}</span>
          )}
          {token.relation && token.relation !== '_' && (
            <span className="text-stone-400 text-xs mt-0.5 italic">{token.relation}</span>
          )}
          <span className="text-stone-300 text-[10px] mt-1 font-mono">{token.ref}</span>
        </span>
      ) : (
        <span className="inline-flex flex-col items-center hover:bg-stone-100 rounded px-1.5 py-1 transition-colors">
          <span className="font-serif text-base text-stone-900">{token.form}</span>
          <span className="text-stone-400 text-[10px] leading-tight">{token.lemma}</span>
        </span>
      )}
    </span>
  )
}

// ── Verse display ─────────────────────────────────────────────────────────────

function VerseDisplay({
  verse,
  tokens,
  translation,
  showTranslation,
}: {
  verse: number
  tokens: VulgateToken[]
  translation?: string
  showTranslation: boolean
}) {
  const [isPlaying, setIsPlaying] = useState(false)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const [synthesizeSpeech] = useMutation(SYNTHESIZE_SPEECH)

  useEffect(() => {
    return () => {
      audioRef.current?.pause()
    }
  }, [])

  const handlePlayVerse = useCallback(async () => {
    if (isPlaying) {
      audioRef.current?.pause()
      audioRef.current = null
      setIsPlaying(false)
      return
    }

    setIsPlaying(true)
    const verseText = tokens.map((t) => t.form).join(' ')

    try {
      const result = await synthesizeSpeech({ variables: { text: verseText, language: 'la' } })
      const data = result.data?.synthesizeSpeech
      if (data?.available && data.audioBase64) {
        const mimeType = data.mimeType ?? 'audio/wav'
        const audio = new Audio(`data:${mimeType};base64,${data.audioBase64}`)
        audioRef.current = audio
        audio.onended = () => { audioRef.current = null; setIsPlaying(false) }
        audio.onerror = () => { audioRef.current = null; setIsPlaying(false) }
        audio.play().catch(() => setIsPlaying(false))
      } else {
        setIsPlaying(false)
      }
    } catch {
      setIsPlaying(false)
    }
  }, [tokens, isPlaying, synthesizeSpeech])

  return (
    <div id={`verse-${verse}`} className="mb-4">
      <span className="text-xs font-bold text-stone-400 mr-1 select-none">{verse}</span>
      <button
        onClick={handlePlayVerse}
        className={`inline-flex items-center justify-center w-5 h-5 rounded-full mr-1 transition-colors
          ${isPlaying ? 'bg-amber-200 text-amber-700 hover:bg-amber-300' : 'bg-stone-100 text-stone-400 hover:bg-stone-200'}`}
        title={isPlaying ? 'Stop' : 'Speak verse'}
        aria-label={isPlaying ? 'Stop verse playback' : 'Speak verse'}
      >
        {isPlaying ? (
          <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
            <rect x="6" y="6" width="4" height="12" />
            <rect x="14" y="6" width="4" height="12" />
          </svg>
        ) : (
          <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
            <polygon points="5,3 19,12 5,21" />
          </svg>
        )}
      </button>
      <span className="inline flex-wrap">
        {tokens.map((tok) => (
          <WordCard key={tok.ref} token={tok} />
        ))}
      </span>
      {showTranslation && translation && (
        <div className="mt-1 mb-2 ml-6 text-sm text-stone-500 italic leading-snug">
          {translation}
        </div>
      )}
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export function VulgateViewerPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [mode, setMode] = useState<'browse' | 'search'>('browse')
  const [selectedBook, setSelectedBook] = useState(() => searchParams.get('book') ?? 'MATT')
  const [selectedChapter, setSelectedChapter] = useState(() => Number(searchParams.get('ch')) || 1)
  const [searchQuery, setSearchQuery] = useState('')
  const [submittedQuery, setSubmittedQuery] = useState('')
  const initialVerseRef = useRef<number | null>(Number(searchParams.get('v')) || null)
  const lastVerseRef = useRef<number | null>(null)
  const didScrollRef = useRef(false)
  // Refs so the observer callback always sees current values without being in deps
  const selectedBookRef = useRef(selectedBook)
  const selectedChapterRef = useRef(selectedChapter)
  selectedBookRef.current = selectedBook
  selectedChapterRef.current = selectedChapter

  const { data: booksData, loading: booksLoading } = useQuery(VULGATE_BOOKS)
  const books: BookInfo[] = booksData?.vulgateBooks ?? []
  const currentBook = books.find((b) => b.abbrev === selectedBook)

  const [showTranslation, setShowTranslation] = useState(false)

  const [loadChapter, { data: chapterData, loading: chapterLoading }] =
    useLazyQuery(VULGATE_CHAPTER)
  const [loadTranslations, { data: translationsData }] =
    useLazyQuery(VULGATE_CHAPTER_TRANSLATIONS)
  const [runSearch, { data: searchData, loading: searchLoading }] =
    useLazyQuery(VULGATE_SEARCH)

  const translationMap = new Map<number, string>()
  for (const t of (translationsData?.vulgateChapterTranslations ?? []) as VerseTranslation[]) {
    translationMap.set(t.verse, t.text)
  }

  const doLoad = useCallback(
    (book: string, chapter: number) => {
      loadChapter({ variables: { book, chapter } })
      loadTranslations({ variables: { book, chapter } })
    },
    [loadChapter, loadTranslations],
  )

  // Initial load — also write book+ch into the URL if missing
  useEffect(() => {
    doLoad(selectedBook, selectedChapter)
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev)
        if (!next.has('book')) next.set('book', selectedBook)
        if (!next.has('ch')) next.set('ch', String(selectedChapter))
        return next
      },
      { replace: true },
    )
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const handleBookChange = (abbrev: string) => {
    setSelectedBook(abbrev)
    setSelectedChapter(1)
    didScrollRef.current = false
    initialVerseRef.current = null
    doLoad(abbrev, 1)
    setSearchParams({ book: abbrev, ch: '1' }, { replace: true })
  }

  const handleChapterChange = (ch: number) => {
    setSelectedChapter(ch)
    didScrollRef.current = false
    initialVerseRef.current = null
    doLoad(selectedBook, ch)
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev)
        next.set('ch', String(ch))
        next.delete('v')
        return next
      },
      { replace: true },
    )
  }

  // Search when submitted query changes
  useEffect(() => {
    if (mode === 'search' && submittedQuery.trim()) {
      runSearch({ variables: { query: submittedQuery.trim(), limit: 100 } })
    }
  }, [mode, submittedQuery, runSearch])

  // Group tokens by verse
  const tokens: VulgateToken[] = chapterData?.vulgateChapter ?? []
const verseMap = new Map<number, VulgateToken[]>()
  for (const tok of tokens) {
    if (!verseMap.has(tok.verse)) verseMap.set(tok.verse, [])
    verseMap.get(tok.verse)!.push(tok)
  }

  const searchResults: VulgateToken[] = searchData?.vulgateSearch ?? []

  // Scroll to the verse encoded in the URL on initial chapter load
  useEffect(() => {
    if (mode !== 'browse' || chapterLoading || tokens.length === 0) return
    if (didScrollRef.current || !initialVerseRef.current) return
    didScrollRef.current = true
    const v = initialVerseRef.current
    setTimeout(() => {
      document.getElementById(`verse-${v}`)?.scrollIntoView({ block: 'start' })
    }, 50)
  }, [mode, chapterLoading, chapterData])  // eslint-disable-line react-hooks/exhaustive-deps

  // Track topmost visible verse via IntersectionObserver → keep URL in sync
  useEffect(() => {
    if (mode !== 'browse' || chapterLoading || tokens.length === 0) return
    const visible = new Set<number>()
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          const v = Number(entry.target.id.replace('verse-', ''))
          if (!v) continue
          if (entry.isIntersecting) visible.add(v)
          else visible.delete(v)
        }
        if (visible.size > 0) {
          const min = Math.min(...visible)
          if (min !== lastVerseRef.current) {
            lastVerseRef.current = min
            // Use replaceState directly to avoid a React re-render (which resets scroll)
            const url = new URL(window.location.href)
            url.searchParams.set('book', selectedBookRef.current)
            url.searchParams.set('ch', String(selectedChapterRef.current))
            url.searchParams.set('v', String(min))
            window.history.replaceState(window.history.state, '', url)
          }
        }
      },
      { rootMargin: '-10% 0px -80% 0px', threshold: 0 },
    )
    document.querySelectorAll('[id^="verse-"]').forEach((el) => observer.observe(el))
    return () => observer.disconnect()
  }, [mode, chapterLoading, chapterData])  // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-stone-800">Vulgata Latina</h1>
        <p className="text-sm text-stone-500 mt-1">
          Latin Vulgate — interlinear morphological viewer
        </p>
      </div>

      {/* Mode tabs */}
      <div className="flex gap-2 mb-6 border-b border-stone-200">
        {(['browse', 'search'] as const).map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors capitalize
              ${
                mode === m
                  ? 'border-amber-600 text-amber-700'
                  : 'border-transparent text-stone-500 hover:text-stone-700'
              }`}
          >
            {m}
          </button>
        ))}
      </div>

      {mode === 'browse' && (
        <>
          {/* Book + chapter nav */}
          <div className="flex flex-wrap items-center gap-3 mb-6">
            <select
              value={selectedBook}
              onChange={(e) => handleBookChange(e.target.value)}
              className="border border-stone-300 rounded-md px-3 py-1.5 text-sm bg-white text-stone-800 focus:outline-none focus:ring-2 focus:ring-amber-400"
              disabled={booksLoading}
            >
              {books.map((b) => (
                <option key={b.abbrev} value={b.abbrev}>
                  {b.name}
                </option>
              ))}
            </select>

            <div className="flex items-center gap-1">
              <button
                onClick={() => {
                  if (selectedChapter > 1) handleChapterChange(selectedChapter - 1)
                }}
                disabled={selectedChapter <= 1}
                className="px-2 py-1 text-sm border border-stone-300 rounded-md disabled:opacity-40 hover:bg-stone-50"
              >
                ‹
              </button>
              <select
                value={selectedChapter}
                onChange={(e) => handleChapterChange(Number(e.target.value))}
                className="border border-stone-300 rounded-md px-2 py-1.5 text-sm bg-white text-stone-800 focus:outline-none focus:ring-2 focus:ring-amber-400"
              >
                {currentBook &&
                  Array.from({ length: currentBook.chapters }, (_, i) => i + 1).map((ch) => (
                    <option key={ch} value={ch}>
                      Ch. {ch}
                    </option>
                  ))}
              </select>
              <button
                onClick={() => {
                  if (currentBook && selectedChapter < currentBook.chapters)
                    handleChapterChange(selectedChapter + 1)
                }}
                disabled={!currentBook || selectedChapter >= currentBook.chapters}
                className="px-2 py-1 text-sm border border-stone-300 rounded-md disabled:opacity-40 hover:bg-stone-50"
              >
                ›
              </button>
            </div>

            <span className="text-xs text-stone-400 ml-1">Click a word to expand morphology</span>

            <button
              onClick={() => setShowTranslation((s) => !s)}
              className={`ml-auto px-3 py-1 rounded-md text-xs border transition-colors ${
                showTranslation
                  ? 'bg-amber-100 border-amber-300 text-amber-700 hover:bg-amber-200'
                  : 'bg-white border-stone-300 text-stone-500 hover:bg-stone-50'
              }`}
              title="Toggle Douay-Rheims translation"
            >
              {showTranslation ? 'Hide translation' : 'Show translation'}
            </button>
          </div>

          {chapterLoading && (
            <div className="text-stone-400 text-sm py-8 text-center">Loading…</div>
          )}

          {!chapterLoading && tokens.length === 0 && (
            <div className="text-stone-400 text-sm py-8 text-center">No data</div>
          )}

          {!chapterLoading && verseMap.size > 0 && (
            <div>
              <div className="text-base font-semibold text-stone-600 mb-4">
                {currentBook?.name ?? selectedBook} {selectedChapter}
              </div>
              <div className="leading-relaxed">
                {Array.from(verseMap.entries()).map(([verse, vtoks]) => (
                  <VerseDisplay
                    key={verse}
                    verse={verse}
                    tokens={vtoks}
                    translation={translationMap.get(verse)}
                    showTranslation={showTranslation}
                  />
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {mode === 'search' && (
        <>
          <form
            className="flex gap-2 mb-6"
            onSubmit={(e) => {
              e.preventDefault()
              setSubmittedQuery(searchQuery)
            }}
          >
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search Latin form or lemma…"
              className="flex-1 border border-stone-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
            />
            <button
              type="submit"
              disabled={!searchQuery.trim()}
              className="px-4 py-2 bg-amber-600 text-white rounded-md text-sm hover:bg-amber-700 disabled:opacity-50"
            >
              Search
            </button>
          </form>

          {searchLoading && (
            <div className="text-stone-400 text-sm py-8 text-center">Searching…</div>
          )}

          {!searchLoading && submittedQuery && searchResults.length === 0 && (
            <div className="text-stone-400 text-sm py-8 text-center">No results found.</div>
          )}

          {!searchLoading && searchResults.length > 0 && (
            <div>
              <div className="text-xs text-stone-400 mb-4">
                {searchResults.length} token{searchResults.length !== 1 ? 's' : ''} matched
                {searchResults.length >= 100 ? ' (showing first 100)' : ''}
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm border-collapse">
                  <thead>
                    <tr className="border-b border-stone-200 text-left text-xs text-stone-500">
                      <th className="pb-2 pr-4">Ref</th>
                      <th className="pb-2 pr-4">Form</th>
                      <th className="pb-2 pr-4">Lemma</th>
                      <th className="pb-2 pr-4">POS</th>
                      <th className="pb-2">Morphology</th>
                    </tr>
                  </thead>
                  <tbody>
                    {searchResults.map((tok) => {
                      const morphParts = decodeMorphology(tok.morphology)
                      return (
                        <tr
                          key={tok.ref}
                          className="border-b border-stone-100 hover:bg-stone-50"
                        >
                          <td className="py-1.5 pr-4 text-stone-500 font-mono text-xs">
                            {tok.ref}
                          </td>
                          <td className="py-1.5 pr-4 font-serif text-stone-900">{tok.form}</td>
                          <td className="py-1.5 pr-4 text-stone-600">{tok.lemma}</td>
                          <td className="py-1.5 pr-4 text-stone-500">
                            {POS_NAMES[tok.pos] ?? tok.pos}
                          </td>
                          <td className="py-1.5 text-stone-500">
                            {morphParts.length > 0 ? morphParts.join(', ') : '—'}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      <div className="mt-12 pt-4 border-t border-stone-100 text-xs text-stone-400">
        PROIEL Treebank morphology · Translation: Douay-Rheims Challoner (public domain) · Click any word card to see full analysis
      </div>
    </div>
  )
}
