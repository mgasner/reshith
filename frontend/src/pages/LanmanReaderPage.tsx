import { useState, useEffect, useCallback, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'

// ── Types ─────────────────────────────────────────────────────────────────────

interface OcrSelection {
  num: number
  numeral: string
  title: string
  source: string
  bookPages: [number, number]
  devanagari: string
  iast: string
}

interface OcrData {
  selections: OcrSelection[]
}

interface Word {
  i: number
  form: string
  lemma: string | null
  upos: string | null
  feats: Record<string, string>
  unsandhied: string
  lemmaId: number | null
}

interface SandhiGroup {
  words: number[]  // indices into sentence.words
  form: string
}

interface Sentence {
  id: number
  text: string
  chapter: [number, number] | null
  words: Word[]
  sandhiGroups: SandhiGroup[]
}

interface DcsData {
  selectionNums: number[]
  title: string
  source: string
  dcsText: string
  note: string
  sentences: Sentence[]
}

interface LexiconEntry {
  hw: string
  gloss: string
}

type Lexicon = Record<string, LexiconEntry>

// ── DCS file mapping ───────────────────────────────────────────────────────────
// Maps selection numbers to their DCS JSON filename (stem)

const DCS_FILE: Record<number, string> = {
  1: '01',
  ...Object.fromEntries(Array.from({ length: 20 }, (_, i) => [i + 2, 'hitopadesa'])),
  28: '28',
  ...Object.fromEntries(Array.from({ length: 33 }, (_, i) => [i + 29, String(i + 29)])),
}

type DisplayMode = 'samhita' | 'padapatha' | 'analysis'
type ScriptMode = 'iast' | 'devanagari'

// ── IAST → Devanagari (basic table) ──────────────────────────────────────────
// Full conversion via lookup table rather than requiring an npm package

const IAST_VOWELS: [string, string][] = [
  ['ā', 'आ'], ['a', 'अ'],
  ['ī', 'ई'], ['i', 'इ'],
  ['ū', 'ऊ'], ['u', 'उ'],
  ['ṝ', 'ॠ'], ['ṛ', 'ऋ'],
  ['ḷ', 'ऌ'],
  ['ai', 'ऐ'], ['au', 'औ'],
  ['e', 'ए'], ['o', 'ओ'],
  ['ṃ', 'ं'], ['ḥ', 'ः'],
  ['m̐', 'ँ'],
]

const IAST_CONSONANTS: [string, string][] = [
  ['kh', 'ख'], ['k', 'क'],
  ['gh', 'घ'], ['g', 'ग'],
  ['ṅ', 'ङ'],
  ['ch', 'छ'], ['c', 'च'],
  ['jh', 'झ'], ['j', 'ज'],
  ['ñ', 'ञ'],
  ['ṭh', 'ठ'], ['ṭ', 'ट'],
  ['ḍh', 'ढ'], ['ḍ', 'ड'],
  ['ṇ', 'ण'],
  ['th', 'थ'], ['t', 'त'],
  ['dh', 'ध'], ['d', 'द'],
  ['n', 'न'],
  ['ph', 'फ'], ['p', 'प'],
  ['bh', 'भ'], ['b', 'ब'],
  ['m', 'म'],
  ['y', 'य'], ['r', 'र'], ['l', 'ल'], ['v', 'व'],
  ['ś', 'श'], ['ṣ', 'ष'], ['s', 'स'],
  ['h', 'ह'],
  ['ḻ', 'ळ'],
]

function iastToDevanagari(iast: string): string {
  // Simple syllable-level transliteration (best-effort for display)
  let out = ''
  let i = 0
  const s = iast.toLowerCase()

  while (i < s.length) {
    if (s[i] === ' ' || s[i] === '\n') { out += s[i]; i++; continue }
    if (s[i] === '|') { out += '।'; i++; continue }
    if (s[i] === '।' || s[i] === '॥') { out += s[i]; i++; continue }
    if (/\d/.test(s[i])) {
      // Convert digits to Devanagari numerals
      const deva = ['०','१','२','३','४','५','६','७','८','९']
      out += deva[parseInt(s[i])]
      i++; continue
    }

    // Try to match a consonant
    let cons = ''
    let consLen = 0
    for (const [lat, _dev] of IAST_CONSONANTS) {
      if (s.startsWith(lat, i) && lat.length > consLen) {
        cons = lat; consLen = lat.length
      }
    }

    if (cons) {
      const consDeva = IAST_CONSONANTS.find(([l]) => l === cons)![1]
      i += consLen

      // Try to match following vowel
      let vowelDeva = 'अ'  // inherent a
      let vowelLen = 0
      for (const [lat, dev] of IAST_VOWELS) {
        if (s.startsWith(lat, i) && lat.length > vowelLen) {
          vowelDeva = dev; vowelLen = lat.length
        }
      }

      if (s[i] === 'a' && s[i + 1] !== 'i' && s[i + 1] !== 'u') {
        // Inherent 'a' — no matra needed, virama not written
        out += consDeva
        i += 1
      } else if (vowelLen > 0) {
        i += vowelLen
        // Map independent vowel form to matra
        const matraMap: Record<string, string> = {
          'आ': 'ा', 'इ': 'ि', 'ई': 'ी', 'उ': 'ु', 'ऊ': 'ू',
          'ऋ': 'ृ', 'ॠ': 'ॄ', 'ए': 'े', 'ऐ': 'ै', 'ओ': 'ो', 'औ': 'ौ',
          'ं': 'ं', 'ः': 'ः',
        }
        if (vowelDeva === 'अ') {
          out += consDeva  // inherent a
        } else if (matraMap[vowelDeva]) {
          out += consDeva + matraMap[vowelDeva]
        } else {
          out += consDeva + '्' + vowelDeva
        }
      } else {
        // Consonant with virama (halant) — no following vowel
        out += consDeva + '्'
      }
    } else {
      // Try a standalone vowel
      let vowelDeva = ''
      let vowelLen = 0
      for (const [lat, dev] of IAST_VOWELS) {
        if (s.startsWith(lat, i) && lat.length > vowelLen) {
          vowelDeva = dev; vowelLen = lat.length
        }
      }
      if (vowelLen > 0) {
        out += vowelDeva
        i += vowelLen
      } else {
        out += s[i]; i++
      }
    }
  }
  return out
}

// ── Morphology display ────────────────────────────────────────────────────────

const UPOS_LABEL: Record<string, string> = {
  NOUN: 'noun', PROPN: 'proper noun', VERB: 'verb', ADJ: 'adj',
  ADV: 'adv', PRON: 'pron', DET: 'det', ADP: 'prep',
  CONJ: 'conj', SCONJ: 'conj', PART: 'part', NUM: 'num',
  PUNCT: 'punct', X: 'x', AUX: 'aux',
}

function morphGloss(feats: Record<string, string>): string {
  const parts: string[] = []
  const order = ['Person', 'Number', 'Tense', 'Mood', 'Voice', 'VerbForm',
                 'Gender', 'Case', 'Degree']
  for (const k of order) {
    if (feats[k]) parts.push(feats[k].toLowerCase())
  }
  return parts.join(' · ')
}

// ── Word card ─────────────────────────────────────────────────────────────────

function WordCard({
  word, displayMode, scriptMode, active, onClick, lexEntry,
}: {
  word: Word
  displayMode: DisplayMode
  scriptMode: ScriptMode
  active: boolean
  onClick: () => void
  lexEntry?: LexiconEntry
}) {
  const surface = displayMode === 'padapatha' ? word.unsandhied : word.form
  const display = scriptMode === 'devanagari' ? iastToDevanagari(surface) : surface
  const lemmaDisplay = scriptMode === 'devanagari' && word.lemma
    ? iastToDevanagari(word.lemma)
    : word.lemma
  const isVerb = word.upos === 'VERB' || word.upos === 'AUX'
  const isNoun = word.upos === 'NOUN' || word.upos === 'PROPN'
  const baseClass = isVerb ? 'text-blue-800' : isNoun ? 'text-stone-900' : 'text-stone-500'

  if (active) {
    return (
      <span
        onClick={onClick}
        className="inline-flex flex-col items-start mx-0.5 cursor-pointer
          bg-amber-50 border border-amber-300 rounded-lg px-3 py-2 text-sm
          shadow-sm max-w-xs align-top"
      >
        <span className="flex items-baseline gap-2 mb-1">
          <span className={`font-serif text-lg leading-tight ${baseClass}`}>{display}</span>
          {word.form !== word.unsandhied && (
            <span className="text-stone-400 text-xs">
              padap: <span className="font-serif">{
                scriptMode === 'devanagari' ? iastToDevanagari(word.unsandhied) : word.unsandhied
              }</span>
            </span>
          )}
        </span>
        {word.lemma && (
          <span className="text-stone-600 text-xs">
            <span className="text-stone-400">lemma</span>{' '}
            <span className="font-serif">{lemmaDisplay}</span>
          </span>
        )}
        {word.upos && (
          <span className="text-stone-500 text-xs mt-0.5">
            <span className="text-stone-400">pos</span>{' '}
            {UPOS_LABEL[word.upos] ?? word.upos}
          </span>
        )}
        {Object.keys(word.feats).length > 0 && (
          <span className="text-stone-500 text-xs mt-0.5">
            <span className="text-stone-400">morph</span>{' '}
            {morphGloss(word.feats)}
          </span>
        )}
        {lexEntry && (
          <span className="text-amber-800 text-xs mt-1 leading-snug border-t border-amber-200 pt-1">
            {lexEntry.gloss}
          </span>
        )}
      </span>
    )
  }

  if (displayMode === 'analysis') {
    return (
      <span
        onClick={onClick}
        className="inline-flex flex-col items-center mx-0.5 cursor-pointer
          px-1 py-0.5 rounded transition-colors hover:bg-stone-100"
      >
        <span className={`font-serif text-base leading-tight ${baseClass}`}>{display}</span>
        {word.lemma && (
          <span className="text-[10px] text-stone-400 leading-none mt-0.5">{word.lemma}</span>
        )}
      </span>
    )
  }

  return (
    <span
      onClick={onClick}
      className={`inline-block cursor-pointer mx-0.5 hover:text-amber-700
        transition-colors font-serif text-base ${baseClass}`}
    >
      {display}
    </span>
  )
}

// ── Sentence display ──────────────────────────────────────────────────────────

function SentenceDisplay({
  sentence, displayMode, scriptMode, activeWord, onWordClick, lexicon,
}: {
  sentence: Sentence
  displayMode: DisplayMode
  scriptMode: ScriptMode
  activeWord: number | null
  onWordClick: (wordIdx: number) => void
  lexicon: Lexicon
}) {
  // Build a map from word index to sandhi group it belongs to
  const wordToGroup = new Map<number, SandhiGroup>()
  for (const g of sentence.sandhiGroups) {
    for (const wi of g.words) wordToGroup.set(wi, g)
  }

  // Render words, collapsing sandhi groups in samhita mode
  const elements: React.ReactNode[] = []
  const rendered = new Set<number>()

  sentence.words.forEach((w, wi) => {
    if (rendered.has(wi)) return

    const group = wordToGroup.get(wi)
    if (group && displayMode === 'samhita') {
      // Render the whole sandhi compound as one token
      const groupActive = group.words.some(idx => activeWord === idx)
      const surface = scriptMode === 'devanagari'
        ? iastToDevanagari(group.form)
        : group.form
      elements.push(
        <span
          key={`g${wi}`}
          onClick={() => onWordClick(wi)}
          className={`inline-block cursor-pointer mx-0.5 font-serif text-base
            hover:text-amber-700 transition-colors
            ${groupActive ? 'text-amber-700 underline decoration-dotted' : 'text-stone-900'}`}
        >
          {surface}
        </span>
      )
      for (const idx of group.words) rendered.add(idx)
    } else {
      elements.push(
        <WordCard
          key={wi}
          word={w}
          displayMode={displayMode}
          scriptMode={scriptMode}
          active={activeWord === wi}
          onClick={() => onWordClick(wi)}
          lexEntry={w.lemma ? lexicon[w.lemma] : undefined}
        />
      )
      rendered.add(wi)
    }
  })

  const chRef = sentence.chapter
    ? `${sentence.chapter[0]}.${sentence.chapter[1]} `
    : ''

  return (
    <div className="mb-3">
      {chRef && (
        <span className="text-[10px] text-stone-300 mr-1 font-mono select-none">{chRef}</span>
      )}
      <span className="leading-loose">{elements}</span>
    </div>
  )
}

// ── OCR fallback text ─────────────────────────────────────────────────────────

function OcrTextBlock({ text, className }: { text: string; className?: string }) {
  return (
    <div className={className}>
      {text.split('\n\n').map((para, i) => (
        <p key={i} className="mb-4 leading-relaxed whitespace-pre-wrap">{para}</p>
      ))}
    </div>
  )
}

// ── Group OCR selections by source ────────────────────────────────────────────

function groupBySource(selections: OcrSelection[]) {
  const map = new Map<string, OcrSelection[]>()
  for (const s of selections) {
    if (!map.has(s.source)) map.set(s.source, [])
    map.get(s.source)!.push(s)
  }
  return map
}

// ── Main page ─────────────────────────────────────────────────────────────────

export function LanmanReaderPage() {
  const [searchParams, setSearchParams] = useSearchParams()

  // MW lexicon (loaded once)
  const lexiconRef = useRef<Lexicon>({})
  const [lexiconReady, setLexiconReady] = useState(false)

  useEffect(() => {
    fetch('/data/sanskrit/lanman_lexicon.json')
      .then(r => r.json())
      .then((d: Lexicon) => { lexiconRef.current = d; setLexiconReady(true) })
      .catch(() => setLexiconReady(true))  // fail silently — lexicon is optional
  }, [])

  // OCR index
  const [ocrData, setOcrData] = useState<OcrData | null>(null)
  const [ocrLoading, setOcrLoading] = useState(true)

  // DCS tokenized data
  const [dcsData, setDcsData] = useState<DcsData | null>(null)
  const [dcsLoading, setDcsLoading] = useState(false)
  const [dcsError, setDcsError] = useState<string | null>(null)

  const [selectedNum, setSelectedNum] = useState(() => Number(searchParams.get('sel')) || 1)
  const [displayMode, setDisplayMode] = useState<DisplayMode>('analysis')
  const [scriptMode, setScriptMode] = useState<ScriptMode>('iast')
  const [activeWord, setActiveWord] = useState<{ sentIdx: number; wordIdx: number } | null>(null)
  const [showOcr, setShowOcr] = useState(false)

  // Load OCR index
  useEffect(() => {
    fetch('/data/sanskrit/lanman.json')
      .then(r => r.json())
      .then((d: OcrData) => { setOcrData(d); setOcrLoading(false) })
      .catch(() => setOcrLoading(false))
  }, [])

  // Load DCS data when selection changes
  const loadDcs = useCallback((num: number) => {
    const stem = DCS_FILE[num]
    if (!stem) { setDcsData(null); return }
    setDcsLoading(true)
    setDcsError(null)
    setDcsData(null)
    setActiveWord(null)
    fetch(`/data/sanskrit/lanman/${stem}.json`)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then((d: DcsData) => { setDcsData(d); setDcsLoading(false) })
      .catch((e: Error) => {
        setDcsError(e.message)
        setDcsLoading(false)
      })
  }, [])

  useEffect(() => { loadDcs(selectedNum) }, [selectedNum, loadDcs])

  const ocrSelection = ocrData?.selections.find(s => s.num === selectedNum) ?? null
  const groups = ocrData ? groupBySource(ocrData.selections) : new Map<string, OcrSelection[]>()

  const handleSelect = (num: number) => {
    setSelectedNum(num)
    setShowOcr(false)
    setSearchParams({ sel: String(num) }, { replace: true })
    window.scrollTo({ top: 0 })
  }

  const handleWordClick = (sentIdx: number, wordIdx: number) => {
    setActiveWord(prev =>
      prev?.sentIdx === sentIdx && prev?.wordIdx === wordIdx ? null : { sentIdx, wordIdx }
    )
  }


  const hasDcs = !!DCS_FILE[selectedNum]

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-stone-800">Lanman's Sanskrit Reader</h1>
        <p className="text-sm text-stone-500 mt-1">
          Charles Rockwell Lanman, 1884 · 75 selections · DCS morphology (Hellwig, CC BY 4.0)
        </p>
      </div>

      <div className="flex gap-6">
        {/* Sidebar */}
        <aside className="w-52 flex-shrink-0 hidden md:block">
          <div className="sticky top-4 max-h-[calc(100vh-6rem)] overflow-y-auto pr-1">
            {ocrLoading && (
              <div className="text-stone-400 text-sm py-4 text-center">Loading…</div>
            )}
            {!ocrLoading && ocrData && (
              <div className="space-y-4">
                {Array.from(groups.entries()).map(([source, sels]) => (
                  <div key={source}>
                    <div className="text-[10px] uppercase tracking-wider text-stone-400 font-semibold mb-1 px-1">
                      {source}
                    </div>
                    {sels.map(s => (
                      <button
                        key={s.num}
                        onClick={() => handleSelect(s.num)}
                        className={`w-full text-left px-2 py-1 rounded text-sm transition-colors flex items-center gap-1.5 ${
                          s.num === selectedNum
                            ? 'bg-amber-100 text-amber-800 font-medium'
                            : 'text-stone-600 hover:bg-stone-100'
                        }`}
                      >
                        <span className="font-mono text-xs text-stone-400 flex-shrink-0">
                          {s.numeral}
                        </span>
                        <span className="truncate">{s.title}</span>
                        {DCS_FILE[s.num] && (
                          <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-emerald-400" title="DCS data available" />
                        )}
                      </button>
                    ))}
                  </div>
                ))}
              </div>
            )}
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 min-w-0">
          {/* Mobile dropdown */}
          <div className="md:hidden mb-4">
            <select
              value={selectedNum}
              onChange={e => handleSelect(Number(e.target.value))}
              className="w-full border border-stone-300 rounded-md px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-amber-400"
              disabled={ocrLoading}
            >
              {ocrData?.selections.map(s => (
                <option key={s.num} value={s.num}>
                  {s.numeral}. {s.title} ({s.source})
                </option>
              ))}
            </select>
          </div>

          {/* Header */}
          {ocrSelection && (
            <div className="mb-4">
              <h2 className="text-xl font-semibold text-stone-800">
                {ocrSelection.numeral}. {ocrSelection.title}
              </h2>
              <div className="flex items-center gap-3 mt-0.5">
                <span className="text-sm text-stone-500">{ocrSelection.source}</span>
                {dcsData?.note && (
                  <span className="text-xs text-stone-400 bg-stone-100 px-2 py-0.5 rounded">
                    {dcsData.note}
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Controls */}
          <div className="flex flex-wrap items-center gap-2 mb-5">
            {/* Nav */}
            <button
              onClick={() => { if (selectedNum > 1) handleSelect(selectedNum - 1) }}
              disabled={selectedNum <= 1}
              className="px-2.5 py-1.5 text-sm border border-stone-300 rounded-md disabled:opacity-40 hover:bg-stone-50 text-stone-600"
            >←</button>
            <button
              onClick={() => {
                if (ocrData && selectedNum < ocrData.selections.length) handleSelect(selectedNum + 1)
              }}
              disabled={!ocrData || selectedNum >= ocrData.selections.length}
              className="px-2.5 py-1.5 text-sm border border-stone-300 rounded-md disabled:opacity-40 hover:bg-stone-50 text-stone-600"
            >→</button>

            {/* Display mode */}
            {hasDcs && (
              <div className="flex rounded-md border border-stone-300 overflow-hidden text-xs ml-2">
                {(['samhita', 'padapatha', 'analysis'] as DisplayMode[]).map(m => (
                  <button
                    key={m}
                    onClick={() => setDisplayMode(m)}
                    className={`px-3 py-1.5 transition-colors ${
                      displayMode === m
                        ? 'bg-stone-700 text-white'
                        : 'bg-white text-stone-600 hover:bg-stone-50'
                    }`}
                    title={
                      m === 'samhita' ? 'Saṃhitā — sandhi as written'
                      : m === 'padapatha' ? 'Padapātha — words separated'
                      : 'Analysis — word-by-word with lemmas'
                    }
                  >
                    {m === 'samhita' ? 'Saṃhitā' : m === 'padapatha' ? 'Padapātha' : 'Analysis'}
                  </button>
                ))}
              </div>
            )}

            {/* Script mode */}
            <div className="flex rounded-md border border-stone-300 overflow-hidden text-xs">
              {(['iast', 'devanagari'] as ScriptMode[]).map(m => (
                <button
                  key={m}
                  onClick={() => setScriptMode(m)}
                  className={`px-3 py-1.5 transition-colors ${
                    scriptMode === m
                      ? 'bg-stone-700 text-white'
                      : 'bg-white text-stone-600 hover:bg-stone-50'
                  }`}
                >
                  {m === 'iast' ? 'IAST' : 'देव'}
                </button>
              ))}
            </div>

            {/* OCR fallback toggle */}
            <button
              onClick={() => setShowOcr(s => !s)}
              className={`ml-auto text-xs px-2.5 py-1.5 rounded border transition-colors ${
                showOcr
                  ? 'bg-amber-50 border-amber-300 text-amber-700'
                  : 'border-stone-300 text-stone-400 hover:bg-stone-50'
              }`}
              title="Show OCR scan text"
            >
              OCR
            </button>
          </div>

          {/* DCS text */}
          {hasDcs && (
            <div className="mb-6">
              {dcsLoading && (
                <div className="text-stone-400 text-sm py-6 text-center">Loading DCS data…</div>
              )}
              {dcsError && (
                <div className="text-amber-600 text-sm py-4">
                  DCS data not yet fetched for this selection.{' '}
                  <span className="text-stone-400">Run fetch_dcs.py to generate it.</span>
                </div>
              )}
              {!dcsLoading && !dcsError && dcsData && (
                <div className="leading-loose">
                  {dcsData.sentences.map((sent, si) => (
                    <SentenceDisplay
                      key={sent.id}
                      sentence={sent}
                      displayMode={displayMode}
                      scriptMode={scriptMode}
                      activeWord={activeWord?.sentIdx === si ? activeWord.wordIdx : null}
                      onWordClick={(wi) => handleWordClick(si, wi)}
                      lexicon={lexiconReady ? lexiconRef.current : {}}
                    />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Selections without DCS data */}
          {!hasDcs && ocrSelection && !showOcr && (
            <div className="py-4 text-stone-500 text-sm">
              DCS data not available for this selection. Showing OCR text.
            </div>
          )}

          {/* OCR text */}
          {(showOcr || !hasDcs) && ocrSelection && (
            <div className="mt-2 pt-4 border-t border-stone-100">
              <div className="text-xs text-stone-400 mb-3">OCR scan (Tesseract, may contain errors)</div>
              <div className="grid md:grid-cols-2 gap-6">
                <OcrTextBlock
                  text={ocrSelection.devanagari}
                  className="font-devanagari text-xl text-stone-900"
                />
                <OcrTextBlock
                  text={ocrSelection.iast}
                  className="font-serif text-base text-stone-700 italic"
                />
              </div>
            </div>
          )}
        </main>
      </div>

      <div className="mt-12 pt-4 border-t border-stone-100 text-xs text-stone-400 space-y-1">
        <div>
          DCS morphology: Oliver Hellwig,{' '}
          <em>Digital Corpus of Sanskrit</em>, CC BY 4.0 ·{' '}
          <span className="text-stone-300">[?] marks uncertain selection→hymn assignments</span>
        </div>
        <div>
          Lanman's Sanskrit Reader, C. R. Lanman, 1884 (public domain) · OCR via Tesseract
        </div>
      </div>
    </div>
  )
}
