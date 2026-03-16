import { useState, useCallback } from 'react'
import { useMutation } from '@apollo/client'
import { SYNTHESIZE_SPEECH } from '@/graphql/operations'

interface SpeakButtonProps {
  text: string
  language?: string
  className?: string
  size?: 'sm' | 'md' | 'lg'
}

export function SpeakButton({
  text,
  language = 'he-IL',
  className = '',
  size = 'md',
}: SpeakButtonProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [synthesizeSpeech] = useMutation(SYNTHESIZE_SPEECH)

  const speakWithWebSpeechAPI = useCallback((textToSpeak: string) => {
    if (!('speechSynthesis' in window)) {
      console.warn('Web Speech API not supported')
      return
    }

    const utterance = new SpeechSynthesisUtterance(textToSpeak)
    utterance.lang = language
    utterance.rate = 0.8

    const voices = speechSynthesis.getVoices()
    const hebrewVoice = voices.find((v) => v.lang.startsWith('he'))
    if (hebrewVoice) {
      utterance.voice = hebrewVoice
    }

    utterance.onend = () => setIsPlaying(false)
    utterance.onerror = () => setIsPlaying(false)

    speechSynthesis.speak(utterance)
  }, [language])

  const handleSpeak = useCallback(async () => {
    if (isPlaying) return

    setIsPlaying(true)

    try {
      const result = await synthesizeSpeech({
        variables: { text, language },
      })

      const data = result.data?.synthesizeSpeech

      if (data?.available && data.audioBase64) {
        const audioData = `data:audio/mp3;base64,${data.audioBase64}`
        const audio = new Audio(audioData)
        audio.onended = () => setIsPlaying(false)
        audio.onerror = () => {
          console.warn('Audio playback failed, falling back to Web Speech API')
          speakWithWebSpeechAPI(text)
        }
        audio.play()
      } else {
        speakWithWebSpeechAPI(text)
      }
    } catch (error) {
      console.warn('TTS API failed, falling back to Web Speech API:', error)
      speakWithWebSpeechAPI(text)
    }
  }, [text, language, isPlaying, synthesizeSpeech, speakWithWebSpeechAPI])

  const sizeClasses = {
    sm: 'w-6 h-6 p-1',
    md: 'w-8 h-8 p-1.5',
    lg: 'w-10 h-10 p-2',
  }

  return (
    <button
      onClick={handleSpeak}
      disabled={isPlaying}
      className={`inline-flex items-center justify-center rounded-full 
        bg-blue-100 text-blue-600 hover:bg-blue-200 
        disabled:opacity-50 disabled:cursor-not-allowed
        transition-colors ${sizeClasses[size]} ${className}`}
      title="Speak"
      aria-label={`Speak: ${text}`}
    >
      {isPlaying ? (
        <svg
          className="animate-pulse"
          fill="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path d="M12 3v18M6 8v8M18 8v8M3 11v2M21 11v2" 
            stroke="currentColor" 
            strokeWidth="2" 
            strokeLinecap="round"
            fill="none"
          />
        </svg>
      ) : (
        <svg
          fill="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path d="M11 5L6 9H2v6h4l5 4V5zM15.54 8.46a5 5 0 010 7.07M19.07 4.93a10 10 0 010 14.14"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
          />
        </svg>
      )}
    </button>
  )
}
