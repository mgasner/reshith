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
  const [handwriting, setHandwriting] = useState(false)
  const [swapVersion, setSwapVersion] = useState(0)

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
      case 'letter': {
        const fontKey = handwriting ? 'script' : 'print'
        const letterClass = `text-8xl leading-[1.6] ${handwriting ? 'font-hebrew-script' : 'font-hebrew'}`
        return (
          <div key={fontKey} className="flex gap-8 justify-center items-baseline rtl overflow-visible">
            <span className={letterClass}>{card.letter}</span>
            {card.finalForm && (
              <div className="flex flex-col items-center">
                <span className={`${letterClass} text-gray-400`}>{card.finalForm}</span>
                <span className="text-xs text-gray-400 mt-1 tracking-wide">final</span>
              </div>
            )}
          </div>
        )
      }
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
        className="bg-white rounded-xl shadow-lg p-8 min-h-[300px] flex flex-col cursor-pointer relative overflow-visible"
        onClick={handleNext}
      >
        <button
          onClick={(e) => { e.stopPropagation(); setHandwriting((v) => !v); setSwapVersion((n) => n + 1) }}
          className={`absolute top-3 right-3 p-1.5 rounded transition-colors ${
            handwriting ? 'text-blue-600 hover:text-blue-700' : 'text-gray-400 hover:text-gray-600'
          }`}
          title={handwriting ? 'Switch to print' : 'Switch to handwriting'}
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
          </svg>
        </button>

        <div className="flex-1 flex flex-col justify-center items-center overflow-visible">
          {renderFaceContent(currentFace)}
        </div>

        <div key={swapVersion} className="absolute inset-0 bg-white rounded-xl pointer-events-none glyph-swap" />

        <div className="flex items-center justify-between mt-4" onClick={(e) => e.stopPropagation()}>
          <SpeakButton text={card.letter} size="sm" />
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
