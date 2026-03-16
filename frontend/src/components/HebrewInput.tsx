import { useState, useCallback } from 'react'
import { HebrewKeyboard } from './HebrewKeyboard'

interface HebrewInputProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  showKeyboard?: boolean
}

export function HebrewInput({
  value,
  onChange,
  placeholder = 'Type Hebrew here...',
  showKeyboard = true,
}: HebrewInputProps) {
  const [keyboardVisible, setKeyboardVisible] = useState(showKeyboard)

  const handleInput = useCallback(
    (char: string) => {
      onChange(value + char)
    },
    [value, onChange]
  )

  const handleBackspace = useCallback(() => {
    if (value.length > 0) {
      const chars = [...value]
      chars.pop()
      onChange(chars.join(''))
    }
  }, [value, onChange])

  const handleSpace = useCallback(() => {
    onChange(value + ' ')
  }, [value, onChange])

  const handleClear = useCallback(() => {
    onChange('')
  }, [onChange])

  return (
    <div className="w-full">
      <div className="mb-4">
        <div
          className="w-full min-h-[60px] p-4 bg-white border-2 border-gray-300 rounded-lg font-hebrew text-3xl rtl text-right focus-within:border-blue-500 cursor-text"
          onClick={() => setKeyboardVisible(true)}
        >
          {value || <span className="text-gray-400 text-xl">{placeholder}</span>}
          <span className="animate-pulse">|</span>
        </div>
      </div>

      {keyboardVisible && (
        <div className="relative">
          <button
            onClick={() => setKeyboardVisible(false)}
            className="absolute -top-2 -right-2 w-6 h-6 bg-gray-500 text-white rounded-full text-xs hover:bg-gray-600 z-10"
            title="Hide keyboard"
          >
            ×
          </button>
          <HebrewKeyboard
            onInput={handleInput}
            onBackspace={handleBackspace}
            onSpace={handleSpace}
            onClear={handleClear}
          />
        </div>
      )}

      {!keyboardVisible && (
        <button
          onClick={() => setKeyboardVisible(true)}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          Show keyboard
        </button>
      )}
    </div>
  )
}
