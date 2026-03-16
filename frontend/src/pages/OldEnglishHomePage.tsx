import { Link } from 'react-router-dom'

export function OldEnglishHomePage() {
  return (
    <div className="px-4">
      <div className="text-center py-12">
        <h1 className="text-4xl font-bold text-stone-900 mb-4">Old English</h1>
        <p className="text-xl text-stone-600 mb-2">
          Read the oldest literature in the English tradition
        </p>
        <p className="text-sm text-stone-500 italic mb-8">
          Anglo-Saxon — the language of Beowulf, the Anglo-Saxon Chronicle, and the Venerable Bede
        </p>

        {/* Primary links */}
        <div className="mt-10">
          <h2 className="text-xl font-semibold text-stone-800 mb-4">Texts & Vocabulary</h2>
          <div className="flex flex-wrap justify-center gap-4">
            <Link
              to="/old-english/beowulf"
              className="inline-block px-6 py-3 bg-stone-700 text-white rounded-lg hover:bg-stone-800 transition-colors"
            >
              Beowulf — Interlinear Reader
            </Link>
            <Link
              to="/old-english/lesson/1"
              className="inline-block px-6 py-3 border border-stone-600 text-stone-700 rounded-lg hover:bg-stone-50 transition-colors"
            >
              Lesson 1: Vocabulary
            </Link>
          </div>
        </div>

        {/* Feature cards */}
        <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto mt-12">
          <div className="bg-white p-6 rounded-lg shadow-md border border-stone-100">
            <h3 className="text-lg font-semibold text-stone-800 mb-2">
              <span className="text-2xl mr-2 font-serif">þ ð æ</span>
              Runic Heritage
            </h3>
            <p className="text-stone-600 text-sm">
              Old English preserves three characters from the runic alphabet: thorn (þ), eth (ð),
              and ash (æ) — still present in Modern English as "th" and the short "a" vowel.
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md border border-stone-100">
            <h3 className="text-lg font-semibold text-stone-800 mb-2">Alliterative Verse</h3>
            <p className="text-stone-600 text-sm">
              Old English poetry is organized into pairs of half-lines (a-verse and b-verse)
              separated by a pause called a caesura. The half-lines are linked by alliteration
              on the first stressed syllable of the b-verse.
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md border border-stone-100">
            <h3 className="text-lg font-semibold text-stone-800 mb-2">Germanic Roots</h3>
            <p className="text-stone-600 text-sm">
              Old English is a West Germanic language closely related to Old Frisian, Old Saxon,
              and Old High German. Knowing it reveals the deep ancestry of core Modern English
              words: <em>cyning</em> (king), <em>mōd</em> (mood), <em>eorðe</em> (earth).
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
