import { useState } from 'react'
import { SpeakButton } from './SpeakButton'

export interface VowelCardData {
  name: string
  hebrewExample: string
  transliteration: string
}

type CardFace = 'example' | 'name' | 'transliteration'

interface VowelCardProps {
  card: VowelCardData
  onReview: (quality: number) => void
}

const FACE_ORDER: CardFace[] = ['example', 'name', 'transliteration']

const FACE_LABELS: Record<CardFace, string> = {
  example: 'Example',
  name: 'Name',
  transliteration: 'Transliteration',
}

export function VowelCard({ card, onReview }: VowelCardProps) {
  const [currentFaceIndex, setCurrentFaceIndex] = useState(0)
  const [revealedFaces, setRevealedFaces] = useState<Set<CardFace>>(new Set(['example']))

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
    setRevealedFaces(new Set(['example']))
  }

  const renderFaceContent = (face: CardFace) => {
    switch (face) {
      case 'example':
        return <p className="text-4xl sm:text-8xl font-hebrew rtl">{card.hebrewExample}</p>
      case 'name':
        return <p className="text-xl sm:text-3xl">{card.name}</p>
      case 'transliteration':
        return <p className="text-2xl sm:text-4xl font-mono">{card.transliteration}</p>
    }
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        className="bg-white rounded-xl shadow-lg p-4 sm:p-8 min-h-[200px] sm:min-h-[300px] flex flex-col cursor-pointer"
        onClick={handleNext}
      >
        <div className="flex-1 flex flex-col justify-center items-center">
          {renderFaceContent(currentFace)}
        </div>

        <div className="flex items-center justify-between mt-4" onClick={(e) => e.stopPropagation()}>
          <SpeakButton text={card.hebrewExample} size="sm" />
          <div className="flex gap-1">
            {FACE_ORDER.map((face, index) => (
              <button
                key={face}
                onClick={() => {
                  setCurrentFaceIndex(index)
                  setRevealedFaces((prev) => new Set([...prev, face]))
                }}
                className={`px-2 py-0.5 text-xs rounded-full transition-colors ${
                  currentFace === face
                    ? 'bg-blue-600 text-white'
                    : revealedFaces.has(face)
                      ? 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      : 'bg-gray-100 text-gray-400 hover:bg-gray-200 hover:text-gray-600'
                }`}
              >
                {FACE_LABELS[face]}
              </button>
            ))}
          </div>
        </div>
      </div>

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
