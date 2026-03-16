import { Routes, Route } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import { HomePage } from '@/pages/HomePage'
import { DecksPage } from '@/pages/DecksPage'
import { StudyPage } from '@/pages/StudyPage'
import { AlphabetPage } from '@/pages/AlphabetPage'
import { VowelsPage } from '@/pages/VowelsPage'
import { LessonPage } from '@/pages/LessonPage'
import { ExercisesPage } from '@/pages/ExercisesPage'
import { PrepositionExercisePage } from '@/pages/PrepositionExercisePage'
import { ArticleExercisePage } from '@/pages/ArticleExercisePage'
import { SentenceExercisePage } from '@/pages/SentenceExercisePage'
import { TranslationExercisePage } from '@/pages/TranslationExercisePage'
import { VerbalExercisePage } from '@/pages/VerbalExercisePage'
import { ComparativeExercisePage } from '@/pages/ComparativeExercisePage'
import { RelativeClauseExercisePage } from '@/pages/RelativeClauseExercisePage'

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
        <Route path="exercises" element={<ExercisesPage />} />
        <Route path="exercises/prepositions" element={<PrepositionExercisePage />} />
        <Route path="exercises/article" element={<ArticleExercisePage />} />
        <Route path="exercises/sentences" element={<SentenceExercisePage />} />
        <Route path="exercises/translation" element={<TranslationExercisePage />} />
        <Route path="exercises/verbal" element={<VerbalExercisePage />} />
        <Route path="exercises/comparative" element={<ComparativeExercisePage />} />
        <Route path="exercises/relative-clauses" element={<RelativeClauseExercisePage />} />
      </Route>
    </Routes>
  )
}

export default App
