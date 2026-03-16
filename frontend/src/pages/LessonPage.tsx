import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { VocabularyCard, VocabularyCardData } from '@/components/VocabularyCard'

interface LessonDeck {
  id: string
  name: string
  description: string
  language: string
  cardType: string
  cards: VocabularyCardData[]
}

const CATEGORY_COLORS: Record<string, string> = {
  nouns: 'bg-blue-100 text-blue-800',
  prepositions: 'bg-purple-100 text-purple-800',
  adverbs: 'bg-green-100 text-green-800',
  conjunction: 'bg-orange-100 text-orange-800',
  verbs: 'bg-red-100 text-red-800',
  adjectives: 'bg-yellow-100 text-yellow-800',
  pronouns: 'bg-pink-100 text-pink-800',
  proper_names: 'bg-indigo-100 text-indigo-800',
  other: 'bg-gray-100 text-gray-800',
}

interface LessonPageProps {
  languageCode?: string
  dataDir?: string
}

export function LessonPage({ languageCode = 'hbo', dataDir = 'hebrew' }: LessonPageProps) {
  const { lessonId } = useParams()
  const [deck, setDeck] = useState<LessonDeck | null>(null)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [completed, setCompleted] = useState<Set<number>>(new Set())
  const [loading, setLoading] = useState(true)
  const [filterCategory, setFilterCategory] = useState<string | null>(null)

  useEffect(() => {
    const lessonNum = lessonId || '01'
    setDeck(null)
    setCurrentIndex(0)
    setCompleted(new Set())
    setLoading(true)
    fetch(`/data/${dataDir}/lesson${lessonNum}.json`)
      .then((res) => res.json())
      .then((data) => {
        setDeck(data)
        setLoading(false)
      })
      .catch((err) => {
        console.error('Failed to load lesson data:', err)
        setLoading(false)
      })
  }, [lessonId, dataDir])

  const handleReview = (quality: number) => {
    if (quality >= 3) {
      setCompleted((prev) => new Set([...prev, currentIndex]))
    }

    const filteredCards = getFilteredCards()
    const currentFilteredIndex = filteredCards.findIndex(
      (_, i) => getOriginalIndex(i) === currentIndex
    )
    if (currentFilteredIndex < filteredCards.length - 1) {
      setCurrentIndex(getOriginalIndex(currentFilteredIndex + 1))
    }
  }

  const getFilteredCards = () => {
    if (!deck) return []
    if (!filterCategory) return deck.cards
    return deck.cards.filter((card) => card.category === filterCategory)
  }

  const getOriginalIndex = (filteredIndex: number) => {
    if (!deck || !filterCategory) return filteredIndex
    let count = 0
    for (let i = 0; i < deck.cards.length; i++) {
      if (deck.cards[i].category === filterCategory) {
        if (count === filteredIndex) return i
        count++
      }
    }
    return 0
  }

  const handleCardSelect = (index: number) => {
    setCurrentIndex(index)
  }

  const getNativeWord = (card: VocabularyCardData) => card.word ?? card.hebrew ?? ''

  if (loading) {
    return (
      <div className="px-4 text-center py-12">
        <p className="text-gray-500">Loading lesson...</p>
      </div>
    )
  }

  if (!deck) {
    return (
      <div className="px-4 text-center py-12">
        <p className="text-red-500">Failed to load lesson data</p>
      </div>
    )
  }

  const categories = [...new Set(deck.cards.map((c) => c.category))]
  const filteredCards = getFilteredCards()
  const currentCard = deck.cards[currentIndex]
  const progress = (completed.size / deck.cards.length) * 100
  const isRtl = ['hbo', 'arc', 'heb'].includes(languageCode)

  return (
    <div className="px-4">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{deck.name}</h1>
        <p className="text-gray-600">{deck.description}</p>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        <button
          onClick={() => setFilterCategory(null)}
          className={`px-3 py-1 text-sm rounded-full transition-colors ${
            filterCategory === null
              ? 'bg-gray-800 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          All ({deck.cards.length})
        </button>
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setFilterCategory(cat)}
            className={`px-3 py-1 text-sm rounded-full transition-colors ${
              filterCategory === cat
                ? 'bg-gray-800 text-white'
                : CATEGORY_COLORS[cat] || 'bg-gray-100 text-gray-700'
            }`}
          >
            {cat} ({deck.cards.filter((c) => c.category === cat).length})
          </button>
        ))}
      </div>

      <div className="mb-6">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>Progress</span>
          <span>
            {completed.size} / {deck.cards.length} cards
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="mb-6 flex flex-wrap gap-2 justify-center">
        {filteredCards.map((card, filteredIndex) => {
          const originalIndex = getOriginalIndex(filteredIndex)
          return (
            <button
              key={originalIndex}
              onClick={() => handleCardSelect(originalIndex)}
              className={`px-3 py-2 rounded-lg text-sm transition-colors ${
                isRtl ? 'font-hebrew text-lg rtl' : 'font-mono'
              } ${
                originalIndex === currentIndex
                  ? 'bg-blue-600 text-white'
                  : completed.has(originalIndex)
                    ? 'bg-green-100 text-green-800 hover:bg-green-200'
                    : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
              }`}
              title={card.transliteration}
            >
              {getNativeWord(card)}
            </button>
          )
        })}
      </div>

      <VocabularyCard key={currentIndex} card={currentCard} onReview={handleReview} language={languageCode} />

      <div className="mt-8 flex justify-center gap-4">
        <button
          onClick={() => setCurrentIndex(Math.max(0, currentIndex - 1))}
          disabled={currentIndex === 0}
          className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Previous
        </button>
        <button
          onClick={() =>
            setCurrentIndex(Math.min(deck.cards.length - 1, currentIndex + 1))
          }
          disabled={currentIndex === deck.cards.length - 1}
          className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Next
        </button>
      </div>
    </div>
  )
}
