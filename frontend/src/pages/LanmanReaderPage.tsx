import { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'

// ── Types ─────────────────────────────────────────────────────────────────────

interface Selection {
  num: number
  numeral: string
  title: string
  source: string
  bookPages: [number, number]
  devanagari: string
  iast: string
}

interface LanmanData {
  selections: Selection[]
}

type DisplayMode = 'devanagari' | 'iast' | 'both'

// Group selections by source
function groupBySource(selections: Selection[]): Map<string, Selection[]> {
  const map = new Map<string, Selection[]>()
  for (const s of selections) {
    if (!map.has(s.source)) map.set(s.source, [])
    map.get(s.source)!.push(s)
  }
  return map
}

// ── Text display ──────────────────────────────────────────────────────────────

function TextBlock({ text, className }: { text: string; className?: string }) {
  return (
    <div className={className}>
      {text.split('\n\n').map((para, i) => (
        <p key={i} className="mb-4 leading-relaxed whitespace-pre-wrap">
          {para}
        </p>
      ))}
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export function LanmanReaderPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [data, setData] = useState<LanmanData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedNum, setSelectedNum] = useState(() => Number(searchParams.get('sel')) || 1)
  const [displayMode, setDisplayMode] = useState<DisplayMode>('devanagari')
  const sidebarRef = useRef<HTMLDivElement>(null)

  // Load data
  useEffect(() => {
    fetch('/data/sanskrit/lanman.json')
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then((d: LanmanData) => {
        setData(d)
        setLoading(false)
      })
      .catch((e: Error) => {
        setError(e.message)
        setLoading(false)
      })
  }, [])

  const selection = data?.selections.find((s) => s.num === selectedNum) ?? null

  const handleSelect = (num: number) => {
    setSelectedNum(num)
    setSearchParams({ sel: String(num) }, { replace: true })
    window.scrollTo({ top: 0 })
  }

  const groups = data ? groupBySource(data.selections) : new Map<string, Selection[]>()

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-stone-800">Lanman's Sanskrit Reader</h1>
        <p className="text-sm text-stone-500 mt-1">
          Charles Rockwell Lanman, 1884 · 75 selections from classical and Vedic Sanskrit
        </p>
      </div>

      <div className="flex gap-6">
        {/* Sidebar — selection list */}
        <aside
          ref={sidebarRef}
          className="w-56 flex-shrink-0 hidden md:block"
        >
          <div className="sticky top-4 max-h-[calc(100vh-6rem)] overflow-y-auto pr-1">
            {loading && (
              <div className="text-stone-400 text-sm py-4 text-center">Loading…</div>
            )}
            {!loading && data && (
              <div className="space-y-4">
                {Array.from(groups.entries()).map(([source, sels]) => (
                  <div key={source}>
                    <div className="text-[10px] uppercase tracking-wider text-stone-400 font-semibold mb-1 px-1">
                      {source}
                    </div>
                    {sels.map((s) => (
                      <button
                        key={s.num}
                        onClick={() => handleSelect(s.num)}
                        className={`w-full text-left px-2 py-1 rounded text-sm transition-colors ${
                          s.num === selectedNum
                            ? 'bg-amber-100 text-amber-800 font-medium'
                            : 'text-stone-600 hover:bg-stone-100'
                        }`}
                      >
                        <span className="font-mono text-xs text-stone-400 mr-1.5">
                          {s.numeral}
                        </span>
                        {s.title}
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
          {/* Mobile selection dropdown */}
          <div className="md:hidden mb-4">
            <select
              value={selectedNum}
              onChange={(e) => handleSelect(Number(e.target.value))}
              className="w-full border border-stone-300 rounded-md px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-amber-400"
              disabled={loading}
            >
              {data?.selections.map((s) => (
                <option key={s.num} value={s.num}>
                  {s.numeral}. {s.title} ({s.source})
                </option>
              ))}
            </select>
          </div>

          {loading && (
            <div className="text-stone-400 text-sm py-8 text-center">Loading…</div>
          )}

          {error && (
            <div className="text-red-500 text-sm py-8 text-center">
              Error loading data: {error}
            </div>
          )}

          {!loading && !error && selection && (
            <>
              {/* Header */}
              <div className="flex flex-wrap items-start justify-between gap-3 mb-5">
                <div>
                  <h2 className="text-xl font-semibold text-stone-800">
                    {selection.numeral}. {selection.title}
                  </h2>
                  <div className="text-sm text-stone-500 mt-0.5">
                    {selection.source}
                    {selection.bookPages[0] !== selection.bookPages[1]
                      ? ` · pp. ${selection.bookPages[0]}–${selection.bookPages[1]}`
                      : ` · p. ${selection.bookPages[0]}`}
                  </div>
                </div>

                {/* Display mode toggle */}
                <div className="flex rounded-md border border-stone-300 overflow-hidden text-sm">
                  {(['devanagari', 'iast', 'both'] as DisplayMode[]).map((m) => (
                    <button
                      key={m}
                      onClick={() => setDisplayMode(m)}
                      className={`px-3 py-1.5 transition-colors capitalize ${
                        displayMode === m
                          ? 'bg-amber-600 text-white'
                          : 'bg-white text-stone-600 hover:bg-stone-50'
                      }`}
                    >
                      {m === 'devanagari' ? 'देवनागरी' : m === 'iast' ? 'IAST' : 'Both'}
                    </button>
                  ))}
                </div>
              </div>

              {/* Nav buttons */}
              <div className="flex gap-2 mb-6">
                <button
                  onClick={() => {
                    const prev = data?.selections.find((s) => s.num === selectedNum - 1)
                    if (prev) handleSelect(prev.num)
                  }}
                  disabled={selectedNum <= 1}
                  className="px-3 py-1.5 text-sm border border-stone-300 rounded-md disabled:opacity-40 hover:bg-stone-50 text-stone-600"
                >
                  ← Previous
                </button>
                <button
                  onClick={() => {
                    const next = data?.selections.find((s) => s.num === selectedNum + 1)
                    if (next) handleSelect(next.num)
                  }}
                  disabled={!data || selectedNum >= data.selections.length}
                  className="px-3 py-1.5 text-sm border border-stone-300 rounded-md disabled:opacity-40 hover:bg-stone-50 text-stone-600"
                >
                  Next →
                </button>
              </div>

              {/* Text */}
              <div className={displayMode === 'both' ? 'grid md:grid-cols-2 gap-6' : ''}>
                {(displayMode === 'devanagari' || displayMode === 'both') && (
                  <div>
                    {displayMode === 'both' && (
                      <div className="text-xs uppercase tracking-wider text-stone-400 font-semibold mb-3">
                        देवनागरी
                      </div>
                    )}
                    <TextBlock
                      text={selection.devanagari}
                      className="font-devanagari text-xl text-stone-900"
                    />
                  </div>
                )}

                {(displayMode === 'iast' || displayMode === 'both') && (
                  <div>
                    {displayMode === 'both' && (
                      <div className="text-xs uppercase tracking-wider text-stone-400 font-semibold mb-3">
                        IAST
                      </div>
                    )}
                    <TextBlock
                      text={selection.iast || '(IAST not available)'}
                      className="font-serif text-base text-stone-800 italic"
                    />
                  </div>
                )}
              </div>
            </>
          )}
        </main>
      </div>

      <div className="mt-12 pt-4 border-t border-stone-100 text-xs text-stone-400">
        Lanman's Sanskrit Reader, C. R. Lanman, 1884 (public domain) · OCR text via Tesseract ·
        IAST via indic-transliteration
      </div>
    </div>
  )
}
