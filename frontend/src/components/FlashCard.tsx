import { useState } from 'react'

interface FlashCardProps {
  front: string
  back: string
  transliteration?: string | null
  notes?: string | null
  isRtl?: boolean
  onReview: (quality: number) => void
}

export function FlashCard({
  front,
  back,
  transliteration,
  notes,
  isRtl = false,
  onReview,
}: FlashCardProps) {
  const [isFlipped, setIsFlipped] = useState(false)

  const handleFlip = () => {
    setIsFlipped(!isFlipped)
  }

  const handleReview = (quality: number) => {
    onReview(quality)
    setIsFlipped(false)
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        className="bg-white rounded-xl shadow-lg p-8 min-h-[300px] flex flex-col cursor-pointer"
        onClick={handleFlip}
      >
        <div className="flex-1 flex flex-col justify-center">
          {!isFlipped ? (
            <div className={`text-center ${isRtl ? 'rtl hebrew-text' : ''}`}>
              <p className="text-3xl">{front}</p>
              {transliteration && (
                <p className="text-lg text-gray-500 mt-4">{transliteration}</p>
              )}
            </div>
          ) : (
            <div className="text-center">
              <p className="text-2xl mb-4">{back}</p>
              {notes && <p className="text-sm text-gray-600 mt-4">{notes}</p>}
            </div>
          )}
        </div>

        <div className="flex justify-end gap-1 mt-4" onClick={(e) => e.stopPropagation()}>
          <button
            onClick={() => setIsFlipped(false)}
            className={`px-2 py-0.5 text-xs rounded-full transition-colors ${
              !isFlipped ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Front
          </button>
          <button
            onClick={() => setIsFlipped(true)}
            className={`px-2 py-0.5 text-xs rounded-full transition-colors ${
              isFlipped ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Back
          </button>
        </div>
      </div>

      {isFlipped && (
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
