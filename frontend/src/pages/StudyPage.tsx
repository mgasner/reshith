import { useParams } from 'react-router-dom'

export function StudyPage() {
  const { deckId } = useParams()

  return (
    <div className="px-4">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Study Session</h1>

      <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
        {deckId ? (
          <p>Loading cards for deck {deckId}...</p>
        ) : (
          <p>Select a deck to start studying, or review all due cards.</p>
        )}
      </div>
    </div>
  )
}
