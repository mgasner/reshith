import { useState, useEffect } from 'react'
import { AlphabetCard, AlphabetCardData } from '@/components/AlphabetCard'

interface AlphabetDeck {
  id: string
  name: string
  description: string
  language: string
  cardType: string
  cards: AlphabetCardData[]
}

export function AlphabetPage() {
  const [deck, setDeck] = useState<AlphabetDeck | null>(null)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [completed, setCompleted] = useState<Set<number>>(new Set())
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/data/hebrew/alphabet.json')
      .then((res) => res.json())
      .then((data) => {
        setDeck(data)
        setLoading(false)
      })
      .catch((err) => {
        console.error('Failed to load alphabet data:', err)
        setLoading(false)
      })
  }, [])

  const handleReview = (quality: number) => {
    if (quality >= 3) {
      setCompleted((prev) => new Set([...prev, currentIndex]))
    }

    if (deck && currentIndex < deck.cards.length - 1) {
      setCurrentIndex(currentIndex + 1)
    }
  }

  const handleCardSelect = (index: number) => {
    setCurrentIndex(index)
  }

  if (loading) {
    return (
      <div className="px-4 text-center py-12">
        <p className="text-gray-500">Loading alphabet...</p>
      </div>
    )
  }

  if (!deck) {
    return (
      <div className="px-4 text-center py-12">
        <p className="text-red-500">Failed to load alphabet data</p>
      </div>
    )
  }

  const currentCard = deck.cards[currentIndex]
  const progress = (completed.size / deck.cards.length) * 100

  return (
    <div className="px-4">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{deck.name}</h1>
        <p className="text-gray-600">{deck.description}</p>
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
        {deck.cards.map((card, index) => (
          <button
            key={index}
            onClick={() => handleCardSelect(index)}
            className={`w-10 h-10 rounded-lg font-hebrew text-lg transition-colors ${
              index === currentIndex
                ? 'bg-blue-600 text-white'
                : completed.has(index)
                  ? 'bg-green-100 text-green-800 hover:bg-green-200'
                  : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
            }`}
            title={card.name}
          >
            {card.letter}
          </button>
        ))}
      </div>

      <AlphabetCard card={currentCard} onReview={handleReview} />

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
