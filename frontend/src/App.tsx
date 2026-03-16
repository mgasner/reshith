import { Routes, Route } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import { HomePage } from '@/pages/HomePage'
import { DecksPage } from '@/pages/DecksPage'
import { StudyPage } from '@/pages/StudyPage'
import { AlphabetPage } from '@/pages/AlphabetPage'
import { VowelsPage } from '@/pages/VowelsPage'
import { LessonPage } from '@/pages/LessonPage'
import { PrepositionExercisePage } from '@/pages/PrepositionExercisePage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="decks" element={<DecksPage />} />
        <Route path="study/:deckId?" element={<StudyPage />} />
        <Route path="alphabet" element={<AlphabetPage />} />
        <Route path="vowels" element={<VowelsPage />} />
        <Route path="lesson/:lessonId?" element={<LessonPage />} />
        <Route path="exercises/prepositions" element={<PrepositionExercisePage />} />
      </Route>
    </Routes>
  )
}

export default App
