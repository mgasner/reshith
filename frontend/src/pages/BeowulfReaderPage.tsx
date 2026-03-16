import { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'

// ── Types ─────────────────────────────────────────────────────────────────────

interface BeowulfLine {
  num: number
  a: string
  b: string
  translation: string
}

interface BeowulfSection {
  id: string
  num: string
  title: string
  lineStart: number
  lineEnd: number
  lines: BeowulfLine[]
}

interface BeowulfData {
  title: string
  date: string
  manuscript: string
  sections: BeowulfSection[]
}

// ── Main page ─────────────────────────────────────────────────────────────────

export function BeowulfReaderPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [data, setData] = useState<BeowulfData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState<string>(
    () => searchParams.get('fitt') || 'fitt-1',
  )
  const [showTranslation, setShowTranslation] = useState(true)
  const [showHalfLines, setShowHalfLines] = useState(true)
  const sidebarRef = useRef<HTMLDivElement>(null)

  // Load data
  useEffect(() => {
    fetch('/data/old_english/beowulf.json')
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then((d: BeowulfData) => {
        setData(d)
        setLoading(false)
      })
      .catch((e: Error) => {
        setError(e.message)
        setLoading(false)
      })
  }, [])

  const section = data?.sections.find((s) => s.id === selectedId) ?? null

  const handleSelect = (id: string) => {
    setSelectedId(id)
    setSearchParams({ fitt: id }, { replace: true })
    window.scrollTo({ top: 0 })
  }

  const currentIndex = data?.sections.findIndex((s) => s.id === selectedId) ?? -1
  const prevSection = currentIndex > 0 ? data?.sections[currentIndex - 1] : null
  const nextSection =
    data && currentIndex < data.sections.length - 1
      ? data.sections[currentIndex + 1]
      : null

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Page header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-stone-800">Beowulf</h1>
        {data && (
          <p className="text-sm text-stone-500 mt-1">
            {data.date} · {data.manuscript}
          </p>
        )}
      </div>

      <div className="flex gap-6">
        {/* Sidebar — fitt list */}
        <aside ref={sidebarRef} className="w-52 flex-shrink-0 hidden md:block">
          <div className="sticky top-4 max-h-[calc(100vh-6rem)] overflow-y-auto pr-1">
            {loading && (
              <div className="text-stone-400 text-sm py-4 text-center">Loading…</div>
            )}
            {!loading && data && (
              <div className="space-y-1">
                <div className="text-[10px] uppercase tracking-wider text-stone-400 font-semibold mb-2 px-1">
                  Fitts
                </div>
                {data.sections.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => handleSelect(s.id)}
                    className={`w-full text-left px-2 py-1.5 rounded text-sm transition-colors ${
                      s.id === selectedId
                        ? 'bg-stone-200 text-stone-900 font-medium'
                        : 'text-stone-600 hover:bg-stone-100'
                    }`}
                  >
                    <span className="font-mono text-xs text-stone-400 mr-1.5">{s.num}</span>
                    {s.title}
                    <span className="block text-[10px] text-stone-400 ml-4">
                      ll. {s.lineStart}–{s.lineEnd}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 min-w-0">
          {/* Mobile fitt selector */}
          <div className="md:hidden mb-4">
            <select
              value={selectedId}
              onChange={(e) => handleSelect(e.target.value)}
              className="w-full border border-stone-300 rounded-md px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-stone-400"
              disabled={loading}
            >
              {data?.sections.map((s) => (
                <option key={s.id} value={s.id}>
                  Fitt {s.num}: {s.title} (ll. {s.lineStart}–{s.lineEnd})
                </option>
              ))}
            </select>
          </div>

          {loading && (
            <div className="text-stone-400 text-sm py-8 text-center">Loading…</div>
          )}

          {error && (
            <div className="text-red-500 text-sm py-8 text-center">
              Error loading Beowulf data: {error}
            </div>
          )}

          {!loading && !error && section && (
            <>
              {/* Section header + toggles */}
              <div className="flex flex-wrap items-start justify-between gap-3 mb-5">
                <div>
                  <h2 className="text-xl font-semibold text-stone-800">
                    Fitt {section.num}: {section.title}
                  </h2>
                  <div className="text-sm text-stone-500 mt-0.5">
                    Lines {section.lineStart}–{section.lineEnd}
                  </div>
                </div>

                {/* Toggles */}
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => setShowTranslation((v) => !v)}
                    className={`px-3 py-1.5 text-sm rounded-md border transition-colors ${
                      showTranslation
                        ? 'bg-stone-700 text-white border-stone-700'
                        : 'bg-white text-stone-600 border-stone-300 hover:bg-stone-50'
                    }`}
                  >
                    Translation
                  </button>
                  <button
                    onClick={() => setShowHalfLines((v) => !v)}
                    className={`px-3 py-1.5 text-sm rounded-md border transition-colors ${
                      showHalfLines
                        ? 'bg-stone-700 text-white border-stone-700'
                        : 'bg-white text-stone-600 border-stone-300 hover:bg-stone-50'
                    }`}
                  >
                    Half-lines
                  </button>
                </div>
              </div>

              {/* Prev/Next nav */}
              <div className="flex gap-2 mb-6">
                <button
                  onClick={() => prevSection && handleSelect(prevSection.id)}
                  disabled={!prevSection}
                  className="px-3 py-1.5 text-sm border border-stone-300 rounded-md disabled:opacity-40 hover:bg-stone-50 text-stone-600 transition-colors"
                >
                  ← Previous
                </button>
                <button
                  onClick={() => nextSection && handleSelect(nextSection.id)}
                  disabled={!nextSection}
                  className="px-3 py-1.5 text-sm border border-stone-300 rounded-md disabled:opacity-40 hover:bg-stone-50 text-stone-600 transition-colors"
                >
                  Next →
                </button>
              </div>

              {/* Lines */}
              <div className="space-y-4">
                {section.lines.map((line) => (
                  <div key={line.num} className="group">
                    <div className="flex gap-3 items-baseline">
                      {/* Line number */}
                      <span className="w-8 flex-shrink-0 text-xs text-stone-400 tabular-nums text-right pt-0.5 select-none">
                        {line.num}
                      </span>

                      {/* OE text */}
                      <div className="flex-1">
                        {showHalfLines ? (
                          <div className="grid grid-cols-2 gap-x-4">
                            <span className="font-serif text-stone-900 text-base leading-relaxed">
                              {line.a}
                            </span>
                            <span className="font-serif text-stone-900 text-base leading-relaxed">
                              {line.b}
                            </span>
                          </div>
                        ) : (
                          <span className="font-serif text-stone-900 text-base leading-relaxed">
                            {line.a}
                            {' '}
                            <span className="text-stone-400 select-none mx-1">|</span>
                            {' '}
                            {line.b}
                          </span>
                        )}

                        {/* Translation */}
                        {showTranslation && line.translation && (
                          <p className="text-sm text-stone-500 italic mt-1 leading-snug">
                            {line.translation}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Bottom nav */}
              <div className="flex gap-2 mt-8 pt-4 border-t border-stone-100">
                <button
                  onClick={() => prevSection && handleSelect(prevSection.id)}
                  disabled={!prevSection}
                  className="px-3 py-1.5 text-sm border border-stone-300 rounded-md disabled:opacity-40 hover:bg-stone-50 text-stone-600 transition-colors"
                >
                  ← {prevSection ? `Fitt ${prevSection.num}` : 'Previous'}
                </button>
                <button
                  onClick={() => nextSection && handleSelect(nextSection.id)}
                  disabled={!nextSection}
                  className="px-3 py-1.5 text-sm border border-stone-300 rounded-md disabled:opacity-40 hover:bg-stone-50 text-stone-600 transition-colors"
                >
                  {nextSection ? `Fitt ${nextSection.num}` : 'Next'} →
                </button>
              </div>
            </>
          )}
        </main>
      </div>

      {/* Footer */}
      <div className="mt-12 pt-4 border-t border-stone-100 text-xs text-stone-400">
        Beowulf, Old English text after Klaeber's Beowulf, 4th ed., ed. Fulk, Bjork & Niles
        (University of Toronto Press, 2008) · Translations original
      </div>
    </div>
  )
}
