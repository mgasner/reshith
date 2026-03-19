import { useState, useCallback, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery, useLazyQuery } from '@apollo/client'
import { gql } from '@apollo/client'

// ── GraphQL ───────────────────────────────────────────────────────────────────

const GNT_BOOKS = gql`
  query GNTBooks {
    gntBooks {
      abbrev
      name
      chapters
    }
  }
`

const GNT_CHAPTER = gql`
  query GNTChapter($book: String!, $chapter: Int!) {
    gntChapter(book: $book, chapter: $chapter) {
      ref
      book
      chapter
      verse
      token
      textType
      greek
      transliteration
      translation
      dstrongs
      grammar
      expanded
    }
  }
`

const GNT_CHAPTER_TRANSLATIONS = gql`
  query GNTChapterTranslations($book: String!, $chapter: Int!) {
    gntChapterTranslations(book: $book, chapter: $chapter) {
      verse
      text
    }
  }
`

const GNT_SEARCH = gql`
  query GNTSearch($query: String!, $limit: Int) {
    gntSearch(query: $query, limit: $limit) {
      ref
      book
      chapter
      verse
      token
      textType
      greek
      transliteration
      translation
      dstrongs
      grammar
      expanded
    }
  }
`

// ── Types ─────────────────────────────────────────────────────────────────────

interface GreekToken {
  ref: string
  book: string
  chapter: number
  verse: number
  token: number
  textType: string
  greek: string
  transliteration: string
  translation: string
  dstrongs: string
  grammar: string
  expanded: string
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
//
// TAGNT grammar codes:
//   Full-word (no dash): CONJ, PREP, ADV, PRT, INJ, COND
//   Single-char prefix + dash: N-NSM, V-AAI-3S, A-APF, T-NSM, P-GSM (personal pron.), etc.

const POS_NAMES: Record<string, string> = {
  // Single-char prefixes
  N: 'noun', V: 'verb', A: 'adjective', D: 'adverb',
  P: 'personal pronoun', R: 'relative pronoun', C: 'conjunction',
  T: 'article', I: 'interrogative pronoun', X: 'particle',
  F: 'reflexive pronoun', S: 'possessive pronoun',
  K: 'correlative', Q: 'interrogative',
  // Full-word codes
  CONJ: 'conjunction', PREP: 'preposition', ADV: 'adverb',
  PRT: 'particle', INJ: 'interjection', COND: 'conditional',
  NEG: 'negative',
}

const CASE_NAMES: Record<string, string> = {
  N: 'nominative', G: 'genitive', D: 'dative', A: 'accusative', V: 'vocative',
}
const NUMBER_NAMES: Record<string, string> = { S: 'singular', P: 'plural' }
const GENDER_NAMES: Record<string, string> = { M: 'masculine', F: 'feminine', N: 'neuter' }
const TENSE_NAMES: Record<string, string> = {
  P: 'present', I: 'imperfect', F: 'future',
  A: 'aorist', X: 'perfect', Y: 'pluperfect', L: '2nd perfect',
}
const VOICE_NAMES: Record<string, string> = {
  A: 'active', M: 'middle', P: 'passive',
  D: 'middle (deponent)', O: 'passive (deponent)', N: 'middle/passive',
}
const MOOD_NAMES: Record<string, string> = {
  I: 'indicative', D: 'imperative', S: 'subjunctive',
  O: 'optative', N: 'infinitive', P: 'participle',
}
const PERSON_NAMES: Record<string, string> = {
  '1': '1st person', '2': '2nd person', '3': '3rd person',
}

function decodeGrammar(grammar: string): string[] {
  if (!grammar) return []
  const parts: string[] = []

  // TAGNT may have compound codes like "CONJ + G1437=COND"; use just the first token
  const primary = grammar.split(' + ')[0].trim()

  const dashIdx = primary.indexOf('-')
  if (dashIdx < 0) {
    // Full-word code: CONJ, PREP, ADV, PRT, INJ, COND, or single-char
    const name = POS_NAMES[primary]
    return name ? [name] : [primary.toLowerCase()]
  }

  const pos = primary.slice(0, dashIdx)
  const detail = primary.slice(dashIdx + 1)
  if (POS_NAMES[pos]) parts.push(POS_NAMES[pos])
  if (!detail) return parts

  if (pos === 'V') {
    // Verb: tense+voice+mood[-person+number]  e.g. AAI-3S  PAP-NSM
    const segments = detail.split('-')
    const tvm = segments[0] ?? ''
    const pn = segments[1] ?? ''
    if (tvm[0] && TENSE_NAMES[tvm[0]]) parts.push(TENSE_NAMES[tvm[0]])
    if (tvm[1] && VOICE_NAMES[tvm[1]]) parts.push(VOICE_NAMES[tvm[1]])
    if (tvm[2] && MOOD_NAMES[tvm[2]]) parts.push(MOOD_NAMES[tvm[2]])
    if (tvm[2] === 'P') {
      // Participle: pn = case+number+gender
      if (pn[0] && CASE_NAMES[pn[0]]) parts.push(CASE_NAMES[pn[0]])
      if (pn[1] && NUMBER_NAMES[pn[1]]) parts.push(NUMBER_NAMES[pn[1]])
      if (pn[2] && GENDER_NAMES[pn[2]]) parts.push(GENDER_NAMES[pn[2]])
    } else {
      if (pn[0] && PERSON_NAMES[pn[0]]) parts.push(PERSON_NAMES[pn[0]])
      if (pn[1] && NUMBER_NAMES[pn[1]]) parts.push(NUMBER_NAMES[pn[1]])
    }
  } else {
    // Nominal (noun, adj, pronoun, article): case+number+gender  e.g. NSM, APF
    if (detail[0] && CASE_NAMES[detail[0]]) parts.push(CASE_NAMES[detail[0]])
    if (detail[1] && NUMBER_NAMES[detail[1]]) parts.push(NUMBER_NAMES[detail[1]])
    if (detail[2] && GENDER_NAMES[detail[2]]) parts.push(GENDER_NAMES[detail[2]])
  }
  return parts
}

// ── Word card ─────────────────────────────────────────────────────────────────

function WordCard({ token }: { token: GreekToken }) {
  const [expanded, setExpanded] = useState(false)
  const morphParts = decodeGrammar(token.grammar)

  return (
    <span
      className="inline-block m-1 cursor-pointer select-none"
      onClick={() => setExpanded((e) => !e)}
    >
      {expanded ? (
        <span className="inline-flex flex-col items-start bg-blue-50 border border-blue-200 rounded-lg px-3 py-2 text-sm shadow-sm min-w-[130px] max-w-xs">
          <span className="font-serif text-lg text-stone-900">{token.greek}</span>
          <span className="text-stone-500 text-xs mt-0.5 italic">{token.transliteration}</span>
          <span className="text-stone-700 text-xs mt-1 font-medium">{token.translation}</span>
          {morphParts.length > 0 && (
            <span className="text-stone-500 text-xs mt-1">{morphParts.join(', ')}</span>
          )}
          {token.dstrongs && (
            <span className="text-blue-400 text-[10px] mt-0.5 font-mono">{token.dstrongs}</span>
          )}
          <span className="text-stone-300 text-[10px] mt-1 font-mono">{token.ref}</span>
        </span>
      ) : (
        <span className="inline-flex flex-col items-center hover:bg-blue-50 rounded px-1.5 py-1 transition-colors">
          <span className="font-serif text-base text-stone-900">{token.greek}</span>
          <span className="text-stone-400 text-[10px] leading-tight">{token.translation}</span>
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
  tokens: GreekToken[]
  translation?: string
  showTranslation: boolean
}) {
  return (
    <div id={`verse-${verse}`} className="mb-4">
      <span className="text-xs font-bold text-stone-400 mr-2 select-none">{verse}</span>
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

export function GNTViewerPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [mode, setMode] = useState<'browse' | 'search'>('browse')
  const [selectedBook, setSelectedBook] = useState(() => searchParams.get('book') ?? 'Mat')
  const [selectedChapter, setSelectedChapter] = useState(() => Number(searchParams.get('ch')) || 1)
  const [searchQuery, setSearchQuery] = useState('')
  const [submittedQuery, setSubmittedQuery] = useState('')
  const [showTranslation, setShowTranslation] = useState(false)
  const initialVerseRef = useRef<number | null>(Number(searchParams.get('v')) || null)
  const lastVerseRef = useRef<number | null>(null)
  const didScrollRef = useRef(false)
  const selectedBookRef = useRef(selectedBook)
  const selectedChapterRef = useRef(selectedChapter)
  selectedBookRef.current = selectedBook
  selectedChapterRef.current = selectedChapter

  const { data: booksData, loading: booksLoading } = useQuery(GNT_BOOKS)
  const books: BookInfo[] = booksData?.gntBooks ?? []
  const currentBook = books.find((b) => b.abbrev === selectedBook)

  const [loadChapter, { data: chapterData, loading: chapterLoading }] =
    useLazyQuery(GNT_CHAPTER)
  const [loadTranslations, { data: translationsData }] =
    useLazyQuery(GNT_CHAPTER_TRANSLATIONS)
  const [runSearch, { data: searchData, loading: searchLoading }] =
    useLazyQuery(GNT_SEARCH)

  const translationMap = new Map<number, string>()
  for (const t of (translationsData?.gntChapterTranslations ?? []) as VerseTranslation[]) {
    translationMap.set(t.verse, t.text)
  }

  const doLoad = useCallback(
    (book: string, chapter: number) => {
      loadChapter({ variables: { book, chapter } })
      loadTranslations({ variables: { book, chapter } })
    },
    [loadChapter, loadTranslations],
  )

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

  useEffect(() => {
    if (mode === 'search' && submittedQuery.trim()) {
      runSearch({ variables: { query: submittedQuery.trim(), limit: 100 } })
    }
  }, [mode, submittedQuery, runSearch])

  const tokens: GreekToken[] = chapterData?.gntChapter ?? []
  const verseMap = new Map<number, GreekToken[]>()
  for (const tok of tokens) {
    if (!verseMap.has(tok.verse)) verseMap.set(tok.verse, [])
    verseMap.get(tok.verse)!.push(tok)
  }

  const searchResults: GreekToken[] = searchData?.gntSearch ?? []

  useEffect(() => {
    if (mode !== 'browse' || chapterLoading || tokens.length === 0) return
    if (didScrollRef.current || !initialVerseRef.current) return
    didScrollRef.current = true
    const v = initialVerseRef.current
    setTimeout(() => {
      document.getElementById(`verse-${v}`)?.scrollIntoView({ block: 'start' })
    }, 50)
  }, [mode, chapterLoading, chapterData]) // eslint-disable-line react-hooks/exhaustive-deps

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
  }, [mode, chapterLoading, chapterData]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-stone-800">Greek New Testament</h1>
        <p className="text-sm text-stone-500 mt-1">
          SBLGNT · STEPBible TANTT morphology — interlinear word analysis
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
                  ? 'border-blue-600 text-blue-700'
                  : 'border-transparent text-stone-500 hover:text-stone-700'
              }`}
          >
            {m}
          </button>
        ))}
      </div>

      {mode === 'browse' && (
        <>
          <div className="flex flex-wrap items-center gap-3 mb-6">
            <select
              value={selectedBook}
              onChange={(e) => handleBookChange(e.target.value)}
              className="border border-stone-300 rounded-md px-3 py-1.5 text-sm bg-white text-stone-800 focus:outline-none focus:ring-2 focus:ring-blue-400"
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
                onClick={() => { if (selectedChapter > 1) handleChapterChange(selectedChapter - 1) }}
                disabled={selectedChapter <= 1}
                className="px-2 py-1 text-sm border border-stone-300 rounded-md disabled:opacity-40 hover:bg-stone-50"
              >
                ‹
              </button>
              <select
                value={selectedChapter}
                onChange={(e) => handleChapterChange(Number(e.target.value))}
                className="border border-stone-300 rounded-md px-2 py-1.5 text-sm bg-white text-stone-800 focus:outline-none focus:ring-2 focus:ring-blue-400"
              >
                {currentBook &&
                  Array.from({ length: currentBook.chapters }, (_, i) => i + 1).map((ch) => (
                    <option key={ch} value={ch}>Ch. {ch}</option>
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
                  ? 'bg-blue-100 border-blue-300 text-blue-700 hover:bg-blue-200'
                  : 'bg-white border-stone-300 text-stone-500 hover:bg-stone-50'
              }`}
              title="Toggle KJV translation"
            >
              {showTranslation ? 'Hide translation' : 'Show translation'}
            </button>
          </div>

          {chapterLoading && (
            <div className="text-stone-400 text-sm py-8 text-center">Loading…</div>
          )}

          {!chapterLoading && tokens.length === 0 && (
            <div className="text-stone-400 text-sm py-8 text-center">No data for this passage.</div>
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
              placeholder="Search Greek word, transliteration, gloss, or Strong's…"
              className="flex-1 border border-stone-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
            <button
              type="submit"
              disabled={!searchQuery.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-50"
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
                      <th className="pb-2 pr-4">Greek</th>
                      <th className="pb-2 pr-4">Transliteration</th>
                      <th className="pb-2 pr-4">Gloss</th>
                      <th className="pb-2 pr-4">Strong's</th>
                      <th className="pb-2">Morphology</th>
                    </tr>
                  </thead>
                  <tbody>
                    {searchResults.map((tok) => {
                      const morphParts = decodeGrammar(tok.grammar)
                      return (
                        <tr
                          key={tok.ref}
                          className="border-b border-stone-100 hover:bg-stone-50"
                        >
                          <td className="py-1.5 pr-4 text-stone-500 font-mono text-xs">
                            {tok.ref}
                          </td>
                          <td className="py-1.5 pr-4 font-serif text-stone-900">{tok.greek}</td>
                          <td className="py-1.5 pr-4 text-stone-600 italic">{tok.transliteration}</td>
                          <td className="py-1.5 pr-4 text-stone-600">{tok.translation}</td>
                          <td className="py-1.5 pr-4 text-blue-500 font-mono text-xs">{tok.dstrongs}</td>
                          <td className="py-1.5 text-stone-500 text-xs">
                            {morphParts.length > 0 ? morphParts.join(', ') : tok.grammar || '—'}
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
        SBLGNT text · STEPBible TANTT morphology (CC BY 4.0) · Translation: KJV (public domain) · Click any word to see full analysis
      </div>
    </div>
  )
}
