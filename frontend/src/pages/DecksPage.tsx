const LANGUAGE_NAMES: Record<string, string> = {
  hbo: 'Biblical Hebrew',
  lat: 'Latin',
  grc: 'Ancient Greek',
  san: 'Sanskrit',
  pli: 'Pali',
  bhs: 'Buddhist Hybrid Sanskrit',
  arc: 'Aramaic',
  heb: 'Midrashic Hebrew',
}

export function DecksPage() {
  return (
    <div className="px-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Your Decks</h1>
        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          Create Deck
        </button>
      </div>

      <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
        <p>No decks yet. Create your first deck to get started!</p>
        <p className="mt-4 text-sm">
          Supported languages: {Object.values(LANGUAGE_NAMES).join(', ')}
        </p>
      </div>
    </div>
  )
}
