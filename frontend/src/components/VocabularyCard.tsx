import { useState } from 'react'
import { SpeakButton } from './SpeakButton'

export interface VocabularyCardData {
  category: string
  hebrew: string
  transliteration: string
  definition: string
  notes?: string
}

type CardFace = 'hebrew' | 'transliteration' | 'definition'

const CATEGORY_COLORS: Record<string, string> = {
  nouns: 'bg-blue-100 text-blue-800',
  prepositions: 'bg-purple-100 text-purple-800',
  adverbs: 'bg-green-100 text-green-800',
  conjunction: 'bg-orange-100 text-orange-800',
  verbs: 'bg-red-100 text-red-800',
  adjectives: 'bg-yellow-100 text-yellow-800',
  pronouns: 'bg-pink-100 text-pink-800',
  proper_names: 'bg-indigo-100 text-indigo-800',
  other: 'bg-gray-200 text-gray-700',
}

const formatCategoryName = (category: string): string => {
  return category.replace(/_/g, ' ')
}

interface VocabularyCardProps {
  card: VocabularyCardData
  onReview: (quality: number) => void
}

const FACE_ORDER: CardFace[] = ['hebrew', 'transliteration', 'definition']

const FACE_LABELS: Record<CardFace, string> = {
  hebrew: 'Hebrew',
  transliteration: 'Transliteration',
  definition: 'Definition',
}

export function VocabularyCard({ card, onReview }: VocabularyCardProps) {
  const [currentFaceIndex, setCurrentFaceIndex] = useState(0)
  const [revealedFaces, setRevealedFaces] = useState<Set<CardFace>>(new Set(['hebrew']))

  const currentFace = FACE_ORDER[currentFaceIndex]
  const allRevealed = revealedFaces.size === FACE_ORDER.length

  const handleNext = () => {
    const nextIndex = (currentFaceIndex + 1) % FACE_ORDER.length
    const nextFace = FACE_ORDER[nextIndex]
    setCurrentFaceIndex(nextIndex)
    setRevealedFaces((prev) => new Set([...prev, nextFace]))
  }

  const handleReview = (quality: number) => {
    onReview(quality)
    setCurrentFaceIndex(0)
    setRevealedFaces(new Set(['hebrew']))
  }

  const renderFaceContent = (face: CardFace) => {
    switch (face) {
      case 'hebrew':
        return (
          <div className="text-center">
            <div className="flex items-center justify-center gap-3 mb-4">
              <p className="text-7xl font-hebrew rtl">{card.hebrew}</p>
              <SpeakButton text={card.hebrew} size="lg" />
            </div>
            <span className={`inline-block px-3 py-1 text-sm rounded-full ${CATEGORY_COLORS[card.category] || 'bg-gray-100 text-gray-600'}`}>
              {formatCategoryName(card.category)}
            </span>
          </div>
        )
      case 'transliteration':
        return <p className="text-4xl font-mono">{card.transliteration}</p>
      case 'definition':
        return (
          <div className="text-center max-w-lg">
            <p className="text-2xl">{card.definition}</p>
            {card.notes && (
              <p className="text-sm text-gray-500 mt-3 italic">{card.notes}</p>
            )}
          </div>
        )
    }
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="flex justify-center gap-2 mb-4">
        {FACE_ORDER.map((face, index) => (
          <button
            key={face}
            onClick={() => {
              if (revealedFaces.has(face)) {
                setCurrentFaceIndex(index)
              }
            }}
            className={`px-3 py-1 text-sm rounded-full transition-colors ${
              currentFace === face
                ? 'bg-blue-600 text-white'
                : revealedFaces.has(face)
                  ? 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  : 'bg-gray-100 text-gray-400'
            }`}
          >
            {FACE_LABELS[face]}
          </button>
        ))}
      </div>

      <div
        className="bg-white rounded-xl shadow-lg p-8 min-h-[300px] flex flex-col justify-center items-center cursor-pointer"
        onClick={handleNext}
      >
        {renderFaceContent(currentFace)}
      </div>

      <p className="text-center text-gray-400 mt-4 text-sm">
        {allRevealed ? 'All sides revealed' : 'Click card to reveal next side'}
      </p>

      {allRevealed && (
        <div className="mt-6 flex justify-center gap-2">
          <button
            onClick={() => handleReview(1)}
            className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
          >
            Again
          </button>
          <button
            onClick={() => handleReview(3)}
            className="px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600"
          >
            Hard
          </button>
          <button
            onClick={() => handleReview(4)}
            className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
          >
            Good
          </button>
          <button
            onClick={() => handleReview(5)}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            Easy
          </button>
        </div>
      )}
    </div>
  )
}
