import { useCallback } from 'react'

interface HebrewKeyboardProps {
  onInput: (char: string) => void
  onBackspace: () => void
  onSpace: () => void
  onClear?: () => void
}

const CONSONANTS = [
  ['א', 'ב', 'ג', 'ד', 'ה', 'ו', 'ז', 'ח', 'ט', 'י'],
  ['כ', 'ך', 'ל', 'מ', 'ם', 'נ', 'ן', 'ס', 'ע', 'פ'],
  ['ף', 'צ', 'ץ', 'ק', 'ר', 'שׁ', 'שׂ', 'ת'],
]

const VOWELS = [
  { char: '\u05B0', name: 'sheva', display: 'בְ' },
  { char: '\u05B1', name: 'hatef segol', display: 'בֱ' },
  { char: '\u05B2', name: 'hatef patah', display: 'בֲ' },
  { char: '\u05B3', name: 'hatef qamats', display: 'בֳ' },
  { char: '\u05B4', name: 'hiriq', display: 'בִ' },
  { char: '\u05B5', name: 'tsere', display: 'בֵ' },
  { char: '\u05B6', name: 'segol', display: 'בֶ' },
  { char: '\u05B7', name: 'patah', display: 'בַ' },
  { char: '\u05B8', name: 'qamats', display: 'בָ' },
  { char: '\u05B9', name: 'holam', display: 'בֹ' },
  { char: '\u05BB', name: 'qubuts', display: 'בֻ' },
]

const DAGESH = { char: '\u05BC', name: 'dagesh', display: 'בּ' }

const SPECIAL = [
  { char: '\u05BE', name: 'maqaf', display: '־' },
  { char: '\u05C1', name: 'shin dot', display: 'שׁ' },
  { char: '\u05C2', name: 'sin dot', display: 'שׂ' },
]

export function HebrewKeyboard({
  onInput,
  onBackspace,
  onSpace,
  onClear,
}: HebrewKeyboardProps) {
  const handleKey = useCallback(
    (char: string) => {
      onInput(char)
    },
    [onInput]
  )

  return (
    <div className="bg-gray-100 rounded-lg p-4 select-none">
      <div className="mb-3">
        <div className="text-xs text-gray-500 mb-1">Consonants</div>
        {CONSONANTS.map((row, rowIndex) => (
          <div key={rowIndex} className="flex justify-center gap-1 mb-1">
            {row.map((char) => (
              <button
                key={char}
                onClick={() => handleKey(char)}
                className="w-10 h-10 bg-white rounded-lg shadow-sm hover:bg-gray-50 active:bg-gray-100 font-hebrew text-xl rtl"
              >
                {char}
              </button>
            ))}
          </div>
        ))}
      </div>

      <div className="mb-3">
        <div className="text-xs text-gray-500 mb-1">Vowels</div>
        <div className="flex flex-wrap justify-center gap-1">
          {VOWELS.map((vowel) => (
            <button
              key={vowel.name}
              onClick={() => handleKey(vowel.char)}
              className="w-10 h-10 bg-white rounded-lg shadow-sm hover:bg-gray-50 active:bg-gray-100 font-hebrew text-xl rtl"
              title={vowel.name}
            >
              {vowel.display}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-3">
        <div className="text-xs text-gray-500 mb-1">Marks</div>
        <div className="flex justify-center gap-1">
          <button
            onClick={() => handleKey(DAGESH.char)}
            className="w-10 h-10 bg-white rounded-lg shadow-sm hover:bg-gray-50 active:bg-gray-100 font-hebrew text-xl rtl"
            title={DAGESH.name}
          >
            {DAGESH.display}
          </button>
          {SPECIAL.map((mark) => (
            <button
              key={mark.name}
              onClick={() => handleKey(mark.char)}
              className="w-10 h-10 bg-white rounded-lg shadow-sm hover:bg-gray-50 active:bg-gray-100 font-hebrew text-xl rtl"
              title={mark.name}
            >
              {mark.display}
            </button>
          ))}
        </div>
      </div>

      <div className="flex justify-center gap-2">
        <button
          onClick={onBackspace}
          className="px-4 h-10 bg-gray-300 rounded-lg hover:bg-gray-400 active:bg-gray-500 text-sm font-medium"
        >
          Backspace
        </button>
        <button
          onClick={onSpace}
          className="px-8 h-10 bg-white rounded-lg shadow-sm hover:bg-gray-50 active:bg-gray-100 text-sm font-medium"
        >
          Space
        </button>
        {onClear && (
          <button
            onClick={onClear}
            className="px-4 h-10 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 active:bg-red-300 text-sm font-medium"
          >
            Clear
          </button>
        )}
      </div>
    </div>
  )
}
