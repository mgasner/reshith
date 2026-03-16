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
import { LatinLessonPage } from '@/pages/LatinLessonPage'
import { LatinHomePage } from '@/pages/LatinHomePage'
import { LatinExercisesPage } from '@/pages/LatinExercisesPage'
import { HebrewExercisesPage } from '@/pages/HebrewExercisesPage'
import { LatinDeclensionExercisePage } from '@/pages/LatinDeclensionExercisePage'
import { LatinConjugationExercisePage } from '@/pages/LatinConjugationExercisePage'
import { TahotViewerPage } from '@/pages/TahotViewerPage'
import { GreekHomePage } from '@/pages/GreekHomePage'
import { GreekLessonPage } from '@/pages/GreekLessonPage'
import { GreekExercisesPage } from '@/pages/GreekExercisesPage'
import { GreekDeclensionExercisePage } from '@/pages/GreekDeclensionExercisePage'
import { GreekConjugationExercisePage } from '@/pages/GreekConjugationExercisePage'
import { NTGreekHomePage } from '@/pages/NTGreekHomePage'
import { NTGreekLessonPage } from '@/pages/NTGreekLessonPage'
import { NTGreekExercisesPage } from '@/pages/NTGreekExercisesPage'
import { NTGreekDeclensionExercisePage } from '@/pages/NTGreekDeclensionExercisePage'
import { NTGreekConjugationExercisePage } from '@/pages/NTGreekConjugationExercisePage'
import { SanskritHomePage } from '@/pages/SanskritHomePage'
import { SanskritLessonPage } from '@/pages/SanskritLessonPage'
import { SanskritExercisesPage } from '@/pages/SanskritExercisesPage'
import { SanskritDeclensionExercisePage } from '@/pages/SanskritDeclensionExercisePage'
import { LanmanReaderPage } from '@/pages/LanmanReaderPage'
import { EcclesiasticalLatinHomePage } from '@/pages/EcclesiasticalLatinHomePage'
import { EcclesiasticalLatinLessonPage } from '@/pages/EcclesiasticalLatinLessonPage'
import { EcclesiasticalLatinExercisesPage } from '@/pages/EcclesiasticalLatinExercisesPage'
import { EcclesiasticalLatinDeclensionExercisePage } from '@/pages/EcclesiasticalLatinDeclensionExercisePage'
import { EcclesiasticalLatinConjugationExercisePage } from '@/pages/EcclesiasticalLatinConjugationExercisePage'
import { VulgateViewerPage } from '@/pages/VulgateViewerPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="decks" element={<DecksPage />} />
        <Route path="study/:deckId?" element={<StudyPage />} />

        {/* Hebrew */}
        <Route path="hebrew/alphabet" element={<AlphabetPage />} />
        <Route path="hebrew/vowels" element={<VowelsPage />} />
        <Route path="hebrew/lesson/:lessonId?" element={<LessonPage />} />
        <Route path="hebrew/tahot" element={<TahotViewerPage />} />

        {/* Latin */}
        <Route path="latin" element={<LatinHomePage />} />
        <Route path="latin/lesson/:lessonId?" element={<LatinLessonPage />} />

        {/* Exercises hub */}
        <Route path="exercises" element={<ExercisesPage />} />

        {/* Hebrew exercises */}
        <Route path="exercises/hebrew" element={<HebrewExercisesPage />} />
        <Route path="exercises/hebrew/prepositions" element={<PrepositionExercisePage />} />
        <Route path="exercises/hebrew/article" element={<ArticleExercisePage />} />
        <Route path="exercises/hebrew/sentences" element={<SentenceExercisePage />} />
        <Route path="exercises/hebrew/translation" element={<TranslationExercisePage />} />
        <Route path="exercises/hebrew/verbal" element={<VerbalExercisePage />} />
        <Route path="exercises/hebrew/comparative" element={<ComparativeExercisePage />} />
        <Route path="exercises/hebrew/relative-clauses" element={<RelativeClauseExercisePage />} />

        {/* Latin exercises */}
        <Route path="exercises/latin" element={<LatinExercisesPage />} />
        <Route path="exercises/latin/declension" element={<LatinDeclensionExercisePage />} />
        <Route path="exercises/latin/conjugation" element={<LatinConjugationExercisePage />} />

        {/* Greek (Ancient) */}
        <Route path="greek" element={<GreekHomePage />} />
        <Route path="greek/lesson/:lessonId?" element={<GreekLessonPage />} />

        {/* NT Greek */}
        <Route path="nt-greek" element={<NTGreekHomePage />} />
        <Route path="nt-greek/lesson/:lessonId?" element={<NTGreekLessonPage />} />

        {/* Sanskrit */}
        <Route path="sanskrit" element={<SanskritHomePage />} />
        <Route path="sanskrit/lesson/:lessonId?" element={<SanskritLessonPage />} />
        <Route path="sanskrit/lanman" element={<LanmanReaderPage />} />

        {/* Greek exercises */}
        <Route path="exercises/greek" element={<GreekExercisesPage />} />
        <Route path="exercises/greek/declension" element={<GreekDeclensionExercisePage />} />
        <Route path="exercises/greek/conjugation" element={<GreekConjugationExercisePage />} />

        {/* NT Greek exercises */}
        <Route path="exercises/nt-greek" element={<NTGreekExercisesPage />} />
        <Route path="exercises/nt-greek/declension" element={<NTGreekDeclensionExercisePage />} />
        <Route path="exercises/nt-greek/conjugation" element={<NTGreekConjugationExercisePage />} />

        {/* Sanskrit exercises */}
        <Route path="exercises/sanskrit" element={<SanskritExercisesPage />} />
        <Route path="exercises/sanskrit/declension" element={<SanskritDeclensionExercisePage />} />

        {/* Ecclesiastical Latin */}
        <Route path="ecclesiastical-latin" element={<EcclesiasticalLatinHomePage />} />
        <Route path="ecclesiastical-latin/lesson/:lessonId?" element={<EcclesiasticalLatinLessonPage />} />
        <Route path="ecclesiastical-latin/vulgate" element={<VulgateViewerPage />} />
        <Route path="exercises/ecclesiastical-latin" element={<EcclesiasticalLatinExercisesPage />} />
        <Route path="exercises/ecclesiastical-latin/declension" element={<EcclesiasticalLatinDeclensionExercisePage />} />
        <Route path="exercises/ecclesiastical-latin/conjugation" element={<EcclesiasticalLatinConjugationExercisePage />} />
      </Route>
    </Routes>
  )
}

export default App
