import { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery, useLazyQuery, useMutation } from '@apollo/client'
import { TAHOT_BOOKS, TAHOT_CHAPTER_VERSES, INTERLINEAR_PASSAGE, TAHOT_SEARCH, STRONGS_ENTRY, SYNTHESIZE_SPEECH } from '@/graphql/operations'
import { hebrewToLambdin } from '@/utils/hebrewTranslit'
import { SpeakButton } from '@/components/SpeakButton'

interface TahotBookInfo {
  abbrev: string
  chapters: number
}

interface TahotChapterInfo {
  chapter: number
  verseCount: number
}

// Used by the search mode (tahotSearch query — unchanged)
interface TahotWord {
  ref: string
  book: string
  chapter: number
  verse: number
  token: number
  textType: string
  hebrew: string
  transliteration: string
  translation: string
  dstrongs: string
  grammar: string
  rootStrongs: string
}

// Used by the browse mode (interlinearPassage query)
interface InterlinearWord {
  ref: string
  position: number
  textType: string
  native: string
  transliteration: string
  gloss: string
  morphology: string
  lemmaId: string
  lemma: string
  lemmaDefinition: string
}

interface InterlinearVerse {
  book: string
  chapter: number
  verse: number
  words: InterlinearWord[]
}

interface StrongsEntry {
  strongsId: string
  eStrongsId: string
  native: string
  transliteration: string
  morph: string
  gloss: string
  meaning: string
}

const TEXT_TYPE_LABELS: Record<string, { label: string; color: string }> = {
  L: { label: 'Leningrad', color: 'text-gray-400' },
  Q: { label: 'Qere', color: 'text-amber-600' },
  K: { label: 'Ketiv', color: 'text-blue-600' },
  R: { label: 'Restored', color: 'text-green-600' },
  X: { label: 'LXX', color: 'text-purple-600' },
}

const BOOK_NAMES: Record<string, string> = {
  Gen: 'Genesis', Exo: 'Exodus', Lev: 'Leviticus', Num: 'Numbers', Deu: 'Deuteronomy',
  Jos: 'Joshua', Jdg: 'Judges', '1Sa': '1 Samuel', '2Sa': '2 Samuel',
  '1Ki': '1 Kings', '2Ki': '2 Kings', '1Ch': '1 Chronicles', '2Ch': '2 Chronicles',
  Ezr: 'Ezra', Neh: 'Nehemiah', Est: 'Esther', Job: 'Job', Psa: 'Psalms',
  Pro: 'Proverbs', Ecc: 'Ecclesiastes', Sng: 'Song of Songs',
  Isa: 'Isaiah', Jer: 'Jeremiah', Lam: 'Lamentations', Ezk: 'Ezekiel',
  Dan: 'Daniel', Hos: 'Hosea', Jol: 'Joel', Amo: 'Amos', Oba: 'Obadiah',
  Jon: 'Jonah', Mic: 'Micah', Nah: 'Nahum', Hab: 'Habakkuk',
  Zep: 'Zephaniah', Hag: 'Haggai', Zec: 'Zechariah', Mal: 'Malachi',
}

const CANTILLATION_RE = /[\u0591-\u05AF\u05BD]/g
const VOWELS_RE = /[\u05B0-\u05BB\u05BC\u05C1\u05C2\u05C7]/g

// TAHOT abbreviation → filename in /data/hebrew/rashi/ (no .json)
// Chronicles intentionally absent — Rashi did not comment on them.
const TAHOT_TO_RASHI_FILE: Record<string, string> = {
  Gen: 'gen', Exo: 'exo', Lev: 'lev', Num: 'num', Deu: 'deu',
  Jos: 'jos', Jdg: 'jdg', '1Sa': '1sa', '2Sa': '2sa',
  '1Ki': '1ki', '2Ki': '2ki',
  Ezr: 'ezr', Neh: 'neh', Est: 'est',
  Job: 'job', Psa: 'psa', Pro: 'pro', Ecc: 'ecc', Sng: 'sng',
  Isa: 'isa', Jer: 'jer', Lam: 'lam', Ezk: 'ezk', Dan: 'dan',
  Hos: 'hos', Jol: 'jol', Amo: 'amo', Oba: 'oba', Jon: 'jon',
  Mic: 'mic', Nah: 'nah', Hab: 'hab', Zep: 'zep', Hag: 'hag', Zec: 'zec', Mal: 'mal',
}


function WordCard({
  word,
  showBreaks,
  showTranslit,
  showTranslation,
  showCantillation,
  showVowels,
  compact = false,
}: {
  word: InterlinearWord
  showBreaks: boolean
  showTranslit: boolean
  showTranslation: boolean
  showCantillation: boolean
  showVowels: boolean
  compact?: boolean
}) {
  const [showDetail, setShowDetail] = useState(false)
  const [fetchLexicon, { data: lexiconData, loading: lexiconLoading }] = useLazyQuery<{
    strongsEntry: StrongsEntry | null
  }>(STRONGS_ENTRY)

  const typeInfo = TEXT_TYPE_LABELS[word.textType] ?? { label: word.textType, color: 'text-gray-400' }
  const cleanNative = word.native.replace(/\\.*$/, '')
  let displayNative = showBreaks ? cleanNative : cleanNative.replace(/\//g, '')
  if (!showCantillation) displayNative = displayNative.replace(CANTILLATION_RE, '')
  if (!showVowels) displayNative = displayNative.replace(VOWELS_RE, '')
  const displayGloss = showBreaks
    ? word.gloss
    : word.gloss.replace(/\/ /g, ' ').replace(/\//g, '').trim()

  const handleClick = () => {
    if (!showDetail && word.lemmaId) {
      fetchLexicon({ variables: { strongsId: word.lemmaId } })
    }
    setShowDetail((v) => !v)
  }

  const lexEntry: StrongsEntry | null = lexiconData?.strongsEntry ?? null

  return (
    <div
      className={`inline-block cursor-pointer select-none text-center px-1 transition-colors
        ${showDetail
          ? 'rounded-lg border border-blue-400 bg-blue-50 shadow-md p-2'
          : 'hover:opacity-70'
        }`}
      onClick={handleClick}
    >
      {/* Native script */}
      <div className={`font-hebrew leading-none mb-0.5 text-gray-900 text-start ${compact ? 'text-base' : 'text-2xl'}`} dir="rtl">
        {displayNative}
      </div>
      {/* Lambdin transliteration */}
      {(showTranslit || showDetail) && (
        <div className="text-xs text-blue-700 font-mono leading-tight text-start">
          {hebrewToLambdin(word.native)}
        </div>
      )}
      {/* Gloss */}
      {(showTranslation || showDetail) && (
        <div className="text-xs text-gray-600 leading-tight mt-0.5 text-start">
          {displayGloss}
        </div>
      )}

      {showDetail && (
        <div className="mt-2 pt-2 border-t border-blue-200 text-left space-y-1" dir="ltr">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-hebrew text-xl leading-none" dir="rtl">{cleanNative.replace(/\//g, '')}</span>
            {/* stopPropagation so the speak click doesn't toggle the card */}
            <span onClick={(e) => e.stopPropagation()}>
              <SpeakButton text={cleanNative.replace(/\//g, '')} language="he-IL" size="sm" />
            </span>
          </div>
          {/* TBESH lexicon entry */}
          {lexiconLoading && (
            <div className="text-xs text-gray-400">Loading lexicon…</div>
          )}
          {lexEntry && (
            <div className="space-y-1">
              <div className="flex items-baseline gap-2">
                <span className="font-hebrew text-lg leading-none" dir="rtl">{lexEntry.native}</span>
                <span className="text-xs text-gray-500 font-mono">{lexEntry.transliteration}</span>
                <span className="text-xs text-blue-700 font-medium">{lexEntry.gloss}</span>
                <span className="text-xs text-gray-400 font-mono">{lexEntry.morph}</span>
              </div>
              <div
                className="text-xs text-gray-600 leading-relaxed"
                dangerouslySetInnerHTML={{ __html: lexEntry.meaning }}
              />
            </div>
          )}
          <div className="border-t border-blue-100 pt-1 space-y-0.5">
            {word.lemma && (
              <div className="text-xs text-gray-500">
                <span className="font-medium">Lemma:</span>{' '}
                <span className="font-hebrew">{word.lemma}</span>
                {word.lemmaDefinition && (
                  <span className="text-gray-400"> — {word.lemmaDefinition}</span>
                )}
              </div>
            )}
            <div className="text-xs text-gray-500">
              <span className="font-medium">Strong's:</span>{' '}
              <span className="font-mono">{word.lemmaId}</span>
            </div>
            <div className="text-xs text-gray-500">
              <span className="font-medium">Morphology:</span>{' '}
              <span className="font-mono">{word.morphology}</span>
            </div>
            <div className="text-xs text-gray-400">
              <span className="font-medium text-gray-500">TAHOT:</span>{' '}
              <span className="font-mono">{word.transliteration}</span>
            </div>
            {word.textType !== 'L' && (
              <div className={`text-xs font-medium ${typeInfo.color}`}>
                {typeInfo.label}
              </div>
            )}
            <div className="text-xs text-gray-400 font-mono">{word.ref}</div>
          </div>
        </div>
      )}
    </div>
  )
}

function VerseDisplay({
  verse,
  words,
  showBreaks,
  showTranslit,
  showTranslation,
  showCantillation,
  showVowels,
  showVariants,
}: {
  verse: number
  words: InterlinearWord[]
  showBreaks: boolean
  showTranslit: boolean
  showTranslation: boolean
  showCantillation: boolean
  showVowels: boolean
  showVariants: boolean
}) {
  const mainWords = words.filter((w) => w.textType === 'L')
  const variantWords = words.filter((w) => w.textType !== 'L')
  const cardProps = { showBreaks, showTranslit, showTranslation, showCantillation, showVowels }

  const [isPlaying, setIsPlaying] = useState(false)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const [synthesizeSpeech] = useMutation(SYNTHESIZE_SPEECH)

  useEffect(() => {
    return () => { audioRef.current?.pause() }
  }, [])

  const handlePlayVerse = async () => {
    if (isPlaying) {
      audioRef.current?.pause()
      audioRef.current = null
      setIsPlaying(false)
      return
    }

    setIsPlaying(true)
    // Preserve cantillation marks so Google TTS can honour pausal forms and
    // phrase boundaries encoded in the teamim.  Only strip TAHOT artefacts
    // (\׃ sof pasuq, \־ maqaf) and morpheme-break slashes.
    const verseText = mainWords
      .map((w) => w.native.replace(/\\.*$/, '').replace(/\//g, ''))
      .join(' ')

    const fallbackToWebSpeech = () => {
      if (!('speechSynthesis' in window)) { setIsPlaying(false); return }
      const utterance = new SpeechSynthesisUtterance(verseText)
      utterance.lang = 'he-IL'
      utterance.rate = 0.8
      const voices = speechSynthesis.getVoices()
      const heVoice = voices.find((v) => v.lang.startsWith('he'))
      if (heVoice) utterance.voice = heVoice
      utterance.onend = () => setIsPlaying(false)
      utterance.onerror = () => setIsPlaying(false)
      if (speechSynthesis.paused) speechSynthesis.resume()
      speechSynthesis.speak(utterance)
    }

    try {
      const result = await synthesizeSpeech({ variables: { text: verseText, language: 'he-IL' } })
      const data = result.data?.synthesizeSpeech
      if (data?.available && data.audioBase64) {
        const mimeType = data.mimeType ?? 'audio/mp3'
        const audio = new Audio(`data:${mimeType};base64,${data.audioBase64}`)
        audioRef.current = audio
        audio.onended = () => { audioRef.current = null; setIsPlaying(false) }
        audio.onerror = () => { audioRef.current = null; setIsPlaying(false) }
        audio.play().catch(() => setIsPlaying(false))
      } else {
        fallbackToWebSpeech()
      }
    } catch {
      fallbackToWebSpeech()
    }
  }

  return (
    <div id={`verse-${verse}`} className="mb-2">
      <div className="flex items-center gap-1.5 mb-1">
        <span className="text-xs font-bold text-gray-400 tracking-wide">v.{verse}</span>
        <button
          onClick={handlePlayVerse}
          className={`inline-flex items-center justify-center w-5 h-5 rounded-full transition-colors
            ${isPlaying
              ? 'bg-amber-100 text-amber-600 hover:bg-amber-200'
              : 'bg-gray-100 text-gray-400 hover:bg-gray-200 hover:text-gray-600'
            }`}
          title={isPlaying ? 'Stop' : 'Read verse aloud'}
        >
          {isPlaying ? (
            <svg className="w-full h-full p-0.5" fill="currentColor" viewBox="0 0 24 24">
              <rect x="6" y="6" width="4" height="12" rx="1" />
              <rect x="14" y="6" width="4" height="12" rx="1" />
            </svg>
          ) : (
            <svg className="w-full h-full p-0.5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5.14v14l11-7-11-7z" />
            </svg>
          )}
        </button>
      </div>
      <div className="flex flex-wrap gap-2" dir="rtl">
        {mainWords.map((w, i) => (
          <WordCard
            key={`${w.ref}-${i}`}
            word={w}
            {...cardProps}
          />
        ))}
      </div>
      {showVariants && variantWords.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-1 pt-1 border-t border-dashed border-gray-200" dir="rtl">
          {variantWords.map((w, i) => {
            const { color } = TEXT_TYPE_LABELS[w.textType] ?? { color: 'text-gray-400' }
            return (
              <div key={`${w.ref}-v-${i}`} className="flex flex-col items-end gap-0.5">
                <span className={`text-[10px] font-mono font-bold leading-none ${color}`}>
                  {w.textType}
                </span>
                <WordCard word={w} {...cardProps} compact />
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

// ── Rashi flow layout ────────────────────────────────────────────────────────
// Verse column is absolutely positioned left; ResizeObserver measures its height
// so the container never collapses. Rashi flows naturally in the right gutter
// and continues below the verse column when it overflows.

interface RashiFlowProps {
  verses: InterlinearVerse[]
  rashiData: Record<string, Record<string, string>> | null
  rashiLoading: boolean
  selectedChapter: number
  selectedBook: string
  showBreaks: boolean
  showTranslit: boolean
  showTranslation: boolean
  showCantillation: boolean
  showVowels: boolean
  showVariants: boolean
}

function RashiFlowLayout({
  verses, rashiData, rashiLoading, selectedChapter, selectedBook,
  showBreaks, showTranslit, showTranslation, showCantillation, showVowels, showVariants,
}: RashiFlowProps) {
  const verseColRef = useRef<HTMLDivElement>(null)
  const rashiColRef = useRef<HTMLDivElement>(null)
  const [verseColHeight, setVerseColHeight] = useState(0)
  const [rashiColHeight, setRashiColHeight] = useState(0)

  useEffect(() => {
    const pairs: [React.RefObject<HTMLDivElement | null>, (h: number) => void][] = [
      [verseColRef, setVerseColHeight],
      [rashiColRef, setRashiColHeight],
    ]
    const observers = pairs.map(([ref, set]) => {
      const el = ref.current
      if (!el) return null
      const ro = new ResizeObserver(([entry]) => set(entry.contentRect.height))
      ro.observe(el)
      return ro
    })
    return () => observers.forEach((ro) => ro?.disconnect())
  }, [verses])

  const rashiParas = verses.flatMap((v) => {
    const text = rashiData?.[String(selectedChapter)]?.[String(v.verse)]
    if (!text) return []
    return [{ verse: v.verse, text }]
  })

  // When Rashi is taller than the verse column, show the overflow below at full width.
  // We split by finding which paragraph indices fall within the verse column height by
  // measuring each paragraph's offsetTop in the Rashi column.
  const rashiParaRefs = useRef<(HTMLParagraphElement | null)[]>([])
  const overflowStart = (() => {
    if (verseColHeight === 0 || rashiColHeight <= verseColHeight) return null
    for (let i = 0; i < rashiParaRefs.current.length; i++) {
      const el = rashiParaRefs.current[i]
      if (el && el.offsetTop >= verseColHeight) return i
    }
    return null
  })()

  return (
    <>
      {/* Two-column grid: verse left, Rashi right, both top-aligned */}
      <div className="grid gap-7" style={{ gridTemplateColumns: '56fr 44fr', alignItems: 'start' }}>
        <div ref={verseColRef} className="space-y-1 min-w-0">
          {verses.map((v) => (
            <VerseDisplay
              key={v.verse}
              verse={v.verse}
              words={v.words}
              showBreaks={showBreaks}
              showTranslit={showTranslit}
              showTranslation={showTranslation}
              showCantillation={showCantillation}
              showVowels={showVowels}
              showVariants={showVariants}
            />
          ))}
        </div>

        <div
          ref={rashiColRef}
          className="font-rashi text-sm leading-relaxed text-gray-800 min-w-0"
          dir="rtl"
        >
          <div className="text-xs font-semibold text-amber-700 tracking-wide mb-2">רש״י</div>
          {rashiLoading && <div className="text-xs text-gray-400">Loading…</div>}
          {!rashiLoading && !TAHOT_TO_RASHI_FILE[selectedBook] && (
            <div className="text-xs text-gray-400">No Rashi on this book.</div>
          )}
          {!rashiLoading && TAHOT_TO_RASHI_FILE[selectedBook] && !rashiData && (
            <div className="text-xs text-red-400">Could not load — run fetch_rashi.py first.</div>
          )}
          {rashiData && rashiParas.map(({ verse, text }, i) => (
            <p
              key={verse}
              ref={(el) => { rashiParaRefs.current[i] = el }}
              className="mb-3 last:mb-0"
              style={overflowStart !== null && i >= overflowStart ? { visibility: 'hidden' } : undefined}
            >
              <span className="inline-block text-[10px] font-bold text-amber-600 ml-1 leading-none align-super">
                {verse}
              </span>
              <span dangerouslySetInnerHTML={{ __html: text }} />
            </p>
          ))}
        </div>
      </div>

      {/* Overflow paragraphs below both columns at full width */}
      {overflowStart !== null && (
        <div
          className="font-rashi text-sm leading-relaxed text-gray-800 mt-4 pt-4 border-t border-amber-100"
          dir="rtl"
        >
          {rashiParas.slice(overflowStart).map(({ verse, text }) => (
            <p key={verse} className="mb-3 last:mb-0">
              <span className="inline-block text-[10px] font-bold text-amber-600 ml-1 leading-none align-super">
                {verse}
              </span>
              <span dangerouslySetInnerHTML={{ __html: text }} />
            </p>
          ))}
        </div>
      )}
    </>
  )
}

export function TahotViewerPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [mode, setMode] = useState<'browse' | 'search'>('browse')
  const [selectedBook, setSelectedBook] = useState<string>(() => searchParams.get('book') ?? 'Gen')
  const [selectedChapter, setSelectedChapter] = useState<number>(() => Number(searchParams.get('ch')) || 1)
  const [searchQuery, setSearchQuery] = useState('')
  const [submittedQuery, setSubmittedQuery] = useState('')
  const [showBreaks, setShowBreaks] = useState(false)
  const [showTranslit, setShowTranslit] = useState(true)
  const [showTranslation, setShowTranslation] = useState(true)
  const [showMorphKey, setShowMorphKey] = useState(false)
  const [showVariants, setShowVariants] = useState(false)
  const [showCantillation, setShowCantillation] = useState(true)
  const [showVowels, setShowVowels] = useState(true)
  const [showRashi, setShowRashi] = useState(false)
  const [rashiLayout, setRashiLayout] = useState<'flow' | 'side'>('flow')
  const [rashiData, setRashiData] = useState<Record<string, Record<string, string>> | null>(null)
  const [rashiLoading, setRashiLoading] = useState(false)
  const searchInputRef = useRef<HTMLInputElement>(null)
  const initialVerseRef = useRef<number | null>(Number(searchParams.get('v')) || null)
  const lastVerseRef = useRef<number | null>(null)
  const didScrollRef = useRef(false)
  // Refs so the observer callback always sees current values without being in deps
  const selectedBookRef = useRef(selectedBook)
  const selectedChapterRef = useRef(selectedChapter)
  selectedBookRef.current = selectedBook
  selectedChapterRef.current = selectedChapter

  const handleBookChange = (book: string) => {
    setSelectedBook(book)
    setSelectedChapter(1)
    didScrollRef.current = false
    initialVerseRef.current = null
    setSearchParams({ book, ch: '1' }, { replace: true })
  }

  const handleChapterChange = (ch: number) => {
    setSelectedChapter(ch)
    didScrollRef.current = false
    initialVerseRef.current = null
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

  const { data: booksData, loading: booksLoading } = useQuery(TAHOT_BOOKS)

  const { data: chapterVersesData } = useQuery(TAHOT_CHAPTER_VERSES, {
    variables: { book: selectedBook },
    skip: !selectedBook,
  })

  const [fetchPassage, { data: passageData, loading: chapterLoading }] = useLazyQuery(INTERLINEAR_PASSAGE)

  const [fetchSearch, { data: searchData, loading: searchLoading }] = useLazyQuery(TAHOT_SEARCH)

  // Fetch chapter when selection changes; keep book+ch in URL
  useEffect(() => {
    if (mode === 'browse' && selectedBook && selectedChapter) {
      fetchPassage({
        variables: {
          source: 'TAHOT',
          book: selectedBook,
          startChapter: selectedChapter,
          startVerse: 1,
        },
      })
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev)
          next.set('book', selectedBook)
          next.set('ch', String(selectedChapter))
          return next
        },
        { replace: true },
      )
    }
  }, [mode, selectedBook, selectedChapter, fetchPassage, setSearchParams])

  // Search on submit
  useEffect(() => {
    if (mode === 'search' && submittedQuery.trim()) {
      fetchSearch({ variables: { query: submittedQuery.trim(), limit: 100 } })
    }
  }, [mode, submittedQuery, fetchSearch])

  const verses: InterlinearVerse[] = passageData?.interlinearPassage ?? []

  // Scroll to the verse encoded in the URL on initial chapter load
  useEffect(() => {
    if (mode !== 'browse' || chapterLoading || verses.length === 0) return
    if (didScrollRef.current || !initialVerseRef.current) return
    didScrollRef.current = true
    const v = initialVerseRef.current
    setTimeout(() => {
      document.getElementById(`verse-${v}`)?.scrollIntoView({ block: 'start' })
    }, 50)
  }, [mode, chapterLoading, passageData])  // eslint-disable-line react-hooks/exhaustive-deps

  // Track topmost visible verse via IntersectionObserver → keep URL in sync
  useEffect(() => {
    if (mode !== 'browse' || chapterLoading || verses.length === 0) return
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
  }, [mode, chapterLoading, passageData])  // eslint-disable-line react-hooks/exhaustive-deps

  // Fetch Rashi commentary when toggled on or book changes
  useEffect(() => {
    if (!showRashi) return
    const file = TAHOT_TO_RASHI_FILE[selectedBook]
    if (!file) { setRashiData(null); return }
    setRashiLoading(true)
    fetch(`/data/hebrew/rashi/${file}.json`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => { setRashiData(d); setRashiLoading(false) })
      .catch(() => { setRashiData(null); setRashiLoading(false) })
  }, [showRashi, selectedBook])

  const books: TahotBookInfo[] = booksData?.tahotBooks ?? []
  const chapterVerses: TahotChapterInfo[] = chapterVersesData?.tahotChapterVerses ?? []
  const currentChapterInfo = chapterVerses.find((cv) => cv.chapter === selectedChapter)
  const maxChapter =
    books.find((b) => b.abbrev === selectedBook)?.chapters ?? 1

  const searchResults: TahotWord[] = searchData?.tahotSearch ?? []

  return (
    <div className={`px-4 mx-auto ${showRashi && rashiLayout === 'side' ? 'max-w-[1400px]' : 'max-w-5xl'}`}>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">TAHOT Viewer</h1>
        <p className="text-sm text-gray-500 mt-1">
          Translators Amalgamated Hebrew OT — STEPBible.org CC BY 4.0
        </p>
      </div>

      {/* Mode tabs */}
      <div className="flex gap-2 mb-6 border-b border-gray-200">
        {(['browse', 'search'] as const).map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors capitalize
              ${mode === m
                ? 'border-blue-600 text-blue-700'
                : 'border-transparent text-gray-500 hover:text-gray-700'}`}
          >
            {m}
          </button>
        ))}
      </div>

      {mode === 'browse' && (
        <>
          {/* Navigation controls */}
          <div className="flex flex-wrap gap-3 mb-6 items-center">
            {/* Book selector */}
            <select
              value={selectedBook}
              onChange={(e) => handleBookChange(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-400"
              disabled={booksLoading}
            >
              {books.map((b) => (
                <option key={b.abbrev} value={b.abbrev}>
                  {BOOK_NAMES[b.abbrev] ?? b.abbrev}
                </option>
              ))}
            </select>

            {/* Chapter navigation */}
            <div className="flex items-center gap-1">
              <button
                onClick={() => handleChapterChange(Math.max(1, selectedChapter - 1))}
                disabled={selectedChapter <= 1}
                className="px-2 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-40 hover:bg-gray-50"
              >
                ‹
              </button>
              <select
                value={selectedChapter}
                onChange={(e) => handleChapterChange(Number(e.target.value))}
                className="border border-gray-300 rounded-md px-2 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-400"
              >
                {Array.from({ length: maxChapter }, (_, i) => i + 1).map((ch) => (
                  <option key={ch} value={ch}>
                    Ch. {ch}
                  </option>
                ))}
              </select>
              <button
                onClick={() => handleChapterChange(Math.min(maxChapter, selectedChapter + 1))}
                disabled={selectedChapter >= maxChapter}
                className="px-2 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-40 hover:bg-gray-50"
              >
                ›
              </button>
            </div>

            {currentChapterInfo && (
              <span className="text-xs text-gray-400">
                {currentChapterInfo.verseCount} verses
              </span>
            )}

            <div className="ml-auto flex gap-1.5">
              <button
                onClick={() => setShowCantillation((v) => !v)}
                className={`text-xs px-2.5 py-1 rounded-md border transition-colors ${
                  showCantillation
                    ? 'border-blue-400 bg-blue-50 text-blue-700'
                    : 'border-gray-300 text-gray-500 hover:border-gray-400'
                }`}
                title="Toggle cantillation marks"
              >
                accents
              </button>
              <button
                onClick={() => setShowVowels((v) => !v)}
                className={`text-xs px-2.5 py-1 rounded-md border transition-colors ${
                  showVowels
                    ? 'border-blue-400 bg-blue-50 text-blue-700'
                    : 'border-gray-300 text-gray-500 hover:border-gray-400'
                }`}
                title="Toggle vowel points (niqqud)"
              >
                niqqud
              </button>
              <button
                onClick={() => setShowTranslit((v) => !v)}
                className={`text-xs px-2.5 py-1 rounded-md border transition-colors ${
                  showTranslit
                    ? 'border-blue-400 bg-blue-50 text-blue-700'
                    : 'border-gray-300 text-gray-500 hover:border-gray-400'
                }`}
                title="Toggle transliteration"
              >
                translit
              </button>
              <button
                onClick={() => setShowTranslation((v) => !v)}
                className={`text-xs px-2.5 py-1 rounded-md border transition-colors ${
                  showTranslation
                    ? 'border-blue-400 bg-blue-50 text-blue-700'
                    : 'border-gray-300 text-gray-500 hover:border-gray-400'
                }`}
                title="Toggle translation/gloss"
              >
                gloss
              </button>
              <button
                onClick={() => setShowBreaks((v) => !v)}
                className={`text-xs px-2.5 py-1 rounded-md border transition-colors ${
                  showBreaks
                    ? 'border-blue-400 bg-blue-50 text-blue-700'
                    : 'border-gray-300 text-gray-500 hover:border-gray-400'
                }`}
                title="Toggle morpheme break markers (/)"
              >
                a/b
              </button>
              <button
                onClick={() => setShowMorphKey((v) => !v)}
                className={`text-xs px-2.5 py-1 rounded-md border transition-colors ${
                  showMorphKey
                    ? 'border-blue-400 bg-blue-50 text-blue-700'
                    : 'border-gray-300 text-gray-500 hover:border-gray-400'
                }`}
                title="Show morphology key"
              >
                morph key
              </button>
              <button
                onClick={() => setShowVariants((v) => !v)}
                className={`text-xs px-2.5 py-1 rounded-md border transition-colors ${
                  showVariants
                    ? 'border-blue-400 bg-blue-50 text-blue-700'
                    : 'border-gray-300 text-gray-500 hover:border-gray-400'
                }`}
                title="Show Ketiv/Qere and other text variants"
              >
                K/Q
              </button>
              <button
                onClick={() => setShowRashi((v) => !v)}
                className={`text-xs px-2.5 py-1 rounded-md border transition-colors ${
                  showRashi
                    ? 'border-amber-400 bg-amber-50 text-amber-700'
                    : 'border-gray-300 text-gray-500 hover:border-gray-400'
                }`}
                title="Toggle Rashi commentary"
              >
                Rashi
              </button>
              {showRashi && (
                <button
                  onClick={() => setRashiLayout((l) => (l === 'flow' ? 'side' : 'flow'))}
                  className="text-xs px-2.5 py-1 rounded-md border border-amber-300 bg-amber-50 text-amber-600 hover:bg-amber-100 transition-colors"
                  title={rashiLayout === 'flow' ? 'Switch to side-by-side layout' : 'Switch to flow layout'}
                >
                  {rashiLayout === 'flow' ? '⇌ side' : '⇌ flow'}
                </button>
              )}
            </div>
          </div>

          {/* Morphology key */}
          {showMorphKey && (
            <div className="text-xs text-gray-600 border border-gray-200 rounded-lg p-4 space-y-4 bg-gray-50 mb-4">
              <p className="text-gray-500">
                Codes follow the <span className="font-medium">ETCBC</span> system.
                Morphemes are separated by <code className="font-mono bg-gray-200 px-0.5 rounded">/</code>;
                each begins with a part-of-speech letter followed by feature letters.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <div className="font-semibold text-gray-700 mb-1">Parts of speech</div>
                  <table className="w-full">
                    <tbody className="divide-y divide-gray-100">
                      {[['A','Adjective'],['C','Conjunction'],['D','Adverb'],['N','Noun'],
                        ['P','Pronoun'],['R','Preposition'],['S','Pronominal suffix'],
                        ['T','Particle'],['V','Verb']].map(([c,l]) => (
                        <tr key={c}>
                          <td className="py-0.5 pr-3 font-mono font-bold text-gray-800 w-6">{c}</td>
                          <td className="py-0.5 text-gray-600">{l}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div>
                  <div className="font-semibold text-gray-700 mb-1">Noun / adjective — N[gender][number][state]</div>
                  <table className="w-full">
                    <tbody className="divide-y divide-gray-100">
                      <tr><td colSpan={2} className="py-0.5 font-semibold text-gray-500">Gender</td></tr>
                      {[['m','masculine'],['f','feminine'],['c','common']].map(([c,l]) => (
                        <tr key={c}><td className="py-0.5 pr-3 font-mono font-bold text-gray-800 w-6 pl-3">{c}</td><td className="py-0.5 text-gray-600">{l}</td></tr>
                      ))}
                      <tr><td colSpan={2} className="py-0.5 font-semibold text-gray-500 pt-2">Number</td></tr>
                      {[['s','singular'],['p','plural'],['d','dual']].map(([c,l]) => (
                        <tr key={c}><td className="py-0.5 pr-3 font-mono font-bold text-gray-800 w-6 pl-3">{c}</td><td className="py-0.5 text-gray-600">{l}</td></tr>
                      ))}
                      <tr><td colSpan={2} className="py-0.5 font-semibold text-gray-500 pt-2">State</td></tr>
                      {[['a','absolute'],['c','construct'],['d','determined']].map(([c,l]) => (
                        <tr key={`st-${c}`}><td className="py-0.5 pr-3 font-mono font-bold text-gray-800 w-6 pl-3">{c}</td><td className="py-0.5 text-gray-600">{l}</td></tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div>
                  <div className="font-semibold text-gray-700 mb-1">Verb stems — V[stem][aspect][person][gender][number]</div>
                  <table className="w-full">
                    <tbody className="divide-y divide-gray-100">
                      {[['q','Qal'],['N','Niphal'],['p','Piel'],['P','Pual'],
                        ['h','Hiphil'],['H','Hophal'],['t','Hithpael']].map(([c,l]) => (
                        <tr key={c}><td className="py-0.5 pr-3 font-mono font-bold text-gray-800 w-6">{c}</td><td className="py-0.5 text-gray-600">{l}</td></tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div>
                  <div className="font-semibold text-gray-700 mb-1">Verb aspect / form</div>
                  <table className="w-full">
                    <tbody className="divide-y divide-gray-100">
                      {[['q','perfect (qatal)'],['i','imperfect (yiqtol)'],['w','wayyiqtol'],
                        ['c','cohortative / inf. construct'],['j','jussive'],['v','imperative'],
                        ['r','participle (active)'],['s','participle (passive)'],
                        ['a','infinitive absolute']].map(([c,l]) => (
                        <tr key={`asp-${c}`}><td className="py-0.5 pr-3 font-mono font-bold text-gray-800 w-6">{c}</td><td className="py-0.5 text-gray-600">{l}</td></tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Chapter heading */}
          <div className="mb-4">
            <div className="text-lg font-semibold text-gray-700">
              {BOOK_NAMES[selectedBook] ?? selectedBook} {selectedChapter}
            </div>
          </div>

          {chapterLoading && (
            <div className="text-gray-400 text-sm py-8 text-center">Loading…</div>
          )}

          {!chapterLoading && verses.length === 0 && (
            <div className="text-gray-400 text-sm py-8 text-center">No data</div>
          )}

          {!chapterLoading && !showRashi && (
            <div>
              {verses.map((v) => (
                <VerseDisplay
                  key={v.verse}
                  verse={v.verse}
                  words={v.words}
                  showBreaks={showBreaks}
                  showTranslit={showTranslit}
                  showTranslation={showTranslation}
                  showCantillation={showCantillation}
                  showVowels={showVowels}
                  showVariants={showVariants}
                />
              ))}
            </div>
          )}

          {!chapterLoading && showRashi && rashiLayout === 'flow' && (
            <RashiFlowLayout
              verses={verses}
              rashiData={rashiData}
              rashiLoading={rashiLoading}
              selectedChapter={selectedChapter}
              selectedBook={selectedBook}
              showBreaks={showBreaks}
              showTranslit={showTranslit}
              showTranslation={showTranslation}
              showCantillation={showCantillation}
              showVowels={showVowels}
              showVariants={showVariants}
            />
          )}

          {!chapterLoading && showRashi && rashiLayout === 'side' && (
            /* Side-by-side layout: each verse paired with its Rashi */
            <div className="space-y-0">
              {verses.map((v) => (
                <div key={v.verse} className="flex gap-6 items-start border-b border-gray-100 pb-3 mb-3 last:border-0">
                  <div className="flex-1 min-w-0">
                    <VerseDisplay
                      verse={v.verse}
                      words={v.words}
                      showBreaks={showBreaks}
                      showTranslit={showTranslit}
                      showTranslation={showTranslation}
                      showCantillation={showCantillation}
                      showVowels={showVowels}
                      showVariants={showVariants}
                    />
                  </div>
                  <div className="w-80 xl:w-96 flex-shrink-0 pt-5">
                    {rashiLoading && <div className="text-xs text-gray-400">Loading…</div>}
                    {!rashiLoading && !TAHOT_TO_RASHI_FILE[selectedBook] && v.verse === 1 && (
                      <div className="text-xs text-gray-400">No Rashi on this book.</div>
                    )}
                    {!rashiLoading && TAHOT_TO_RASHI_FILE[selectedBook] && !rashiData && v.verse === 1 && (
                      <div className="text-xs text-red-400">Could not load — run fetch_rashi.py first.</div>
                    )}
                    {rashiData?.[String(selectedChapter)]?.[String(v.verse)] && (
                      <div
                        className="font-rashi text-sm leading-relaxed text-gray-800"
                        dir="rtl"
                        dangerouslySetInnerHTML={{
                          __html: rashiData[String(selectedChapter)][String(v.verse)],
                        }}
                      />
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {mode === 'search' && (
        <>
          {/* Search input */}
          <form
            className="flex gap-2 mb-6"
            onSubmit={(e) => {
              e.preventDefault()
              setSubmittedQuery(searchQuery)
            }}
          >
            <input
              ref={searchInputRef}
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Hebrew, transliteration, gloss, or Strong's (e.g. H1254A)"
              className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              dir="auto"
            />
            <button
              type="submit"
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              disabled={!searchQuery.trim()}
            >
              Search
            </button>
          </form>

          {searchLoading && (
            <div className="text-gray-400 text-sm py-8 text-center">Searching…</div>
          )}

          {!searchLoading && submittedQuery && searchResults.length === 0 && (
            <div className="text-gray-400 text-sm py-8 text-center">No results</div>
          )}

          {!searchLoading && searchResults.length > 0 && (
            <div>
              <div className="text-xs text-gray-400 mb-4">
                {searchResults.length} token{searchResults.length !== 1 ? 's' : ''} matched
                {searchResults.length >= 100 ? ' (showing first 100)' : ''}
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm border-collapse">
                  <thead>
                    <tr className="border-b border-gray-200 text-left text-xs text-gray-500">
                      <th className="pb-2 pr-4">Reference</th>
                      <th className="pb-2 pr-4">Hebrew</th>
                      <th className="pb-2 pr-4">Lambdin</th>
                      <th className="pb-2 pr-4">Translation</th>
                      <th className="pb-2 pr-4">Strong's</th>
                      <th className="pb-2">Grammar</th>
                    </tr>
                  </thead>
                  <tbody>
                    {searchResults.map((w, i) => {
                      let searchHebrew = w.hebrew.replace(/\\.*$/, '')
                      if (!showCantillation) searchHebrew = searchHebrew.replace(CANTILLATION_RE, '')
                      if (!showVowels) searchHebrew = searchHebrew.replace(VOWELS_RE, '')
                      return (
                      <tr
                        key={`${w.ref}-${i}`}
                        className="border-b border-gray-100 hover:bg-gray-50"
                      >
                        <td className="py-1.5 pr-4 font-mono text-xs text-gray-500">{w.ref}</td>
                        <td className="py-1.5 pr-4 font-hebrew text-xl" dir="rtl">{searchHebrew}</td>
                        <td className="py-1.5 pr-4 font-mono text-xs text-blue-700">{hebrewToLambdin(w.hebrew)}</td>
                        <td className="py-1.5 pr-4 text-gray-700">
                          {showBreaks ? w.translation : w.translation.replace(/\/ /g, ' ').replace(/\//g, '').trim()}
                        </td>
                        <td className="py-1.5 pr-4 font-mono text-xs text-gray-500">{w.rootStrongs || w.dstrongs}</td>
                        <td className="py-1.5 font-mono text-xs text-gray-400">{w.grammar}</td>
                      </tr>
                    )})}

                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {/* Legend */}
      <div className="mt-12 pt-4 border-t border-gray-100 flex flex-wrap gap-4 text-xs text-gray-400">
        <span className="font-medium text-gray-500">Text types:</span>
        {Object.entries(TEXT_TYPE_LABELS).map(([k, v]) => (
          <span key={k} className={v.color}>{k} = {v.label}</span>
        ))}
        <span className="ml-4">Click a word card for details.</span>
      </div>
    </div>
  )
}
