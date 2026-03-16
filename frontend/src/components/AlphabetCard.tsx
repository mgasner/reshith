import { useState } from 'react'
import { SpeakButton } from './SpeakButton'

export interface AlphabetCardData {
  name: string
  letter: string
  finalForm?: string
  transcription: string
  phoneticValue: string
}

type CardFace = 'letter' | 'name' | 'transcription' | 'phonetic'

interface AlphabetCardProps {
  card: AlphabetCardData
  onReview: (quality: number) => void
}

const FACE_ORDER: CardFace[] = ['letter', 'name', 'transcription', 'phonetic']

const FACE_LABELS: Record<CardFace, string> = {
  letter: 'Letter',
  name: 'Name',
  transcription: 'Transcription',
  phonetic: 'Phonetic Value',
}

export function AlphabetCard({ card, onReview }: AlphabetCardProps) {
  const [currentFaceIndex, setCurrentFaceIndex] = useState(0)
  const [revealedFaces, setRevealedFaces] = useState<Set<CardFace>>(new Set(['letter']))

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
    setRevealedFaces(new Set(['letter']))
  }

  const renderFaceContent = (face: CardFace) => {
    switch (face) {
      case 'letter':
        return (
          <div className="text-center">
            <p className="text-8xl font-hebrew rtl">{card.letter}</p>
            {card.finalForm && (
              <p className="text-4xl font-hebrew rtl text-gray-500 mt-4">
                final: {card.finalForm}
              </p>
            )}
          </div>
        )
      case 'name':
        return <p className="text-4xl capitalize">{card.name}</p>
      case 'transcription':
        return <p className="text-5xl font-mono">{card.transcription}</p>
      case 'phonetic':
        return <p className="text-3xl">{card.phoneticValue}</p>
    }
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        className="bg-white rounded-xl shadow-lg p-8 min-h-[300px] flex flex-col cursor-pointer"
        onClick={handleNext}
      >
        <div className="flex justify-center gap-2 mb-4" onClick={(e) => e.stopPropagation()}>
          {FACE_ORDER.map((face, index) => (
            <button
              key={face}
              onClick={() => {
                setCurrentFaceIndex(index)
                setRevealedFaces((prev) => new Set([...prev, face]))
              }}
              className={`px-3 py-1 text-sm rounded-full transition-colors ${
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

        <div className="flex-1 flex flex-col justify-center items-center">
          {renderFaceContent(currentFace)}
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
