import { gql } from '@apollo/client'

export const LOGIN = gql`
  mutation Login($input: LoginInput!) {
    login(input: $input) {
      token
      user {
        id
        username
        email
        displayName
      }
    }
  }
`

export const ME = gql`
  query Me {
    me {
      id
      username
      email
      displayName
    }
  }
`

export const GET_DECKS = gql`
  query GetDecks($language: LanguageCode) {
    decks(language: $language) {
      id
      name
      description
      language
      cardCount
      createdAt
      updatedAt
    }
  }
`

export const GET_DECK = gql`
  query GetDeck($id: UUID!) {
    deck(id: $id) {
      id
      name
      description
      language
      cardCount
      createdAt
      updatedAt
    }
  }
`

export const GET_CARDS = gql`
  query GetCards($deckId: UUID!) {
    cards(deckId: $deckId) {
      id
      deckId
      front
      back
      notes
      transliteration
      grammaticalInfo
      sourceReference
      createdAt
      updatedAt
    }
  }
`

export const GET_DUE_CARDS = gql`
  query GetDueCards($userId: UUID!, $deckId: UUID, $limit: Int) {
    dueCards(userId: $userId, deckId: $deckId, limit: $limit) {
      card {
        id
        deckId
        front
        back
        notes
        transliteration
        grammaticalInfo
        sourceReference
      }
      srs {
        easinessFactor
        intervalDays
        repetitions
        nextReview
      }
    }
  }
`

export const LEXICON_SEARCH = gql`
  query LexiconSearch($query: String!, $language: LanguageCode!, $limit: Int) {
    lexiconSearch(query: $query, language: $language, limit: $limit) {
      id
      language
      lemma
      transliteration
      definition
      partOfSpeech
      morphology
      frequency
    }
  }
`

export const CREATE_DECK = gql`
  mutation CreateDeck($input: CreateDeckInput!) {
    createDeck(input: $input) {
      id
      name
      description
      language
      cardCount
    }
  }
`

export const CREATE_CARD = gql`
  mutation CreateCard($input: CreateCardInput!) {
    createCard(input: $input) {
      id
      deckId
      front
      back
      notes
      transliteration
      grammaticalInfo
      sourceReference
    }
  }
`

export const SUBMIT_REVIEW = gql`
  mutation SubmitReview($input: ReviewInput!) {
    submitReview(input: $input) {
      cardId
      newSrs {
        easinessFactor
        intervalDays
        repetitions
        nextReview
      }
    }
  }
`

export const GET_TRANSLATION_HELP = gql`
  mutation GetTranslationHelp($text: String!, $language: LanguageCode!, $context: String) {
    getTranslationHelp(text: $text, language: $language, context: $context) {
      translation
      notes
    }
  }
`

export const GENERATE_DRILL = gql`
  mutation GenerateDrill($vocabulary: [String!]!, $language: LanguageCode!, $difficulty: String) {
    generateDrill(vocabulary: $vocabulary, language: $language, difficulty: $difficulty) {
      text
      translation
      notes
    }
  }
`

export const GET_PREPOSITION_EXERCISES = gql`
  query GetPrepositionExercises(
    $count: Int!
    $direction: ExerciseDirection!
    $maxLesson: Int!
    $prepositions: [PrepositionType!]
  ) {
    prepositionExercises(
      count: $count
      direction: $direction
      maxLesson: $maxLesson
      prepositions: $prepositions
    ) {
      id
      hebrew
      transliteration
      english
      preposition
      nounHebrew
      nounDefinition
      direction
      prompt
      answer
    }
  }
`

export const GRADE_PREPOSITION_EXERCISE = gql`
  mutation GradePrepositionExercise($input: GradeExerciseInput!) {
    gradePrepositionExercise(input: $input) {
      correct
      expected
      submitted
      feedback
    }
  }
`

export const SYNTHESIZE_SPEECH = gql`
  mutation SynthesizeSpeech($text: String!, $language: String = "he-IL") {
    synthesizeSpeech(text: $text, language: $language) {
      available
      audioBase64
      mimeType
      text
      language
    }
  }
`

export const GET_ARTICLE_EXERCISES = gql`
  query GetArticleExercises(
    $count: Int!
    $direction: ArticleDirection!
    $maxLesson: Int!
  ) {
    articleExercises(count: $count, direction: $direction, maxLesson: $maxLesson) {
      id
      hebrewIndefinite
      hebrewDefinite
      transliterationIndefinite
      transliterationDefinite
      englishIndefinite
      englishDefinite
      articleType
      direction
      prompt
      promptTransliteration
      answer
      answerTransliteration
    }
  }
`

export const GRADE_ARTICLE_EXERCISE = gql`
  mutation GradeArticleExercise($input: GradeArticleExerciseInput!) {
    gradeArticleExercise(input: $input) {
      correct
      expected
      submitted
      feedback
    }
  }
`

export const GET_SENTENCE_EXERCISES = gql`
  query GetSentenceExercises(
    $count: Int!
    $maxLesson: Int!
    $patterns: [SentencePattern!]
  ) {
    sentenceExercises(count: $count, maxLesson: $maxLesson, patterns: $patterns) {
      id
      pattern
      hebrew
      transliteration
      english
      components
    }
  }
`

export const GET_TRANSLATION_EXERCISES = gql`
  query GetTranslationExercises($count: Int!, $maxLesson: Int!, $patterns: [TranslationPattern!]) {
    translationExercises(count: $count, maxLesson: $maxLesson, patterns: $patterns) {
      id
      pattern
      english
      hebrewAnswer
      transliterationAnswer
      components
    }
  }
`

export const GRADE_TRANSLATION_EXERCISE = gql`
  mutation GradeTranslationExercise($input: GradeTranslationInput!) {
    gradeTranslationExercise(input: $input) {
      correct
      score
      expected
      submitted
      feedback
      transliteration
    }
  }
`

export const GET_VERBAL_EXERCISES = gql`
  query GetVerbalExercises($count: Int!, $maxLesson: Int!, $patterns: [VerbalPattern!]) {
    verbalExercises(count: $count, maxLesson: $maxLesson, patterns: $patterns) {
      id
      pattern
      hebrew
      transliteration
      englishAnswer
      components
    }
  }
`

export const GRADE_VERBAL_EXERCISE = gql`
  mutation GradeVerbalExercise($input: GradeVerbalInput!) {
    gradeVerbalExercise(input: $input) {
      correct
      score
      expected
      submitted
      feedback
    }
  }
`

export const GET_COMPARATIVE_EXERCISES = gql`
  query GetComparativeExercises($count: Int!, $maxLesson: Int!) {
    comparativeExercises(count: $count, maxLesson: $maxLesson) {
      id
      pattern
      hebrew
      transliteration
      englishAnswer
      components
    }
  }
`

export const GRADE_COMPARATIVE_EXERCISE = gql`
  mutation GradeComparativeExercise($input: GradeComparativeInput!) {
    gradeComparativeExercise(input: $input) {
      correct
      score
      expected
      submitted
      feedback
    }
  }
`

export const GET_RELATIVE_CLAUSE_EXERCISES = gql`
  query GetRelativeClauseExercises($count: Int!, $maxLesson: Int!) {
    relativeClauseExercises(count: $count, maxLesson: $maxLesson) {
      id
      pattern
      hebrew
      transliteration
      englishAnswer
      components
    }
  }
`

export const GRADE_RELATIVE_CLAUSE_EXERCISE = gql`
  mutation GradeRelativeClauseExercise($input: GradeRelativeClauseInput!) {
    gradeRelativeClauseExercise(input: $input) {
      correct
      score
      expected
      submitted
      feedback
    }
  }
`


export const GET_LATIN_DECLENSION_EXERCISES = gql`
  query GetLatinDeclensionExercises($count: Int, $maxLesson: Int, $variant: LatinVariant) {
    latinDeclensionExercises(count: $count, maxLesson: $maxLesson, variant: $variant) {
      id
      dictForm
      definition
      case
      number
      prompt
      answer
      lesson
      variant
    }
  }
`

export const GRADE_LATIN_DECLENSION_EXERCISE = gql`
  mutation GradeLatinDeclensionExercise($input: GradeLatinExerciseInput!) {
    gradeLatinDeclensionExercise(input: $input) {
      correct
      expected
      submitted
      feedback
    }
  }
`

export const GET_LATIN_CONJUGATION_EXERCISES = gql`
  query GetLatinConjugationExercises($count: Int, $maxLesson: Int, $variant: LatinVariant) {
    latinConjugationExercises(count: $count, maxLesson: $maxLesson, variant: $variant) {
      id
      dictForm
      definition
      person
      number
      prompt
      answer
      lesson
      variant
    }
  }
`

export const GRADE_LATIN_CONJUGATION_EXERCISE = gql`
  mutation GradeLatinConjugationExercise($input: GradeLatinExerciseInput!) {
    gradeLatinConjugationExercise(input: $input) {
      correct
      expected
      submitted
      feedback
    }
  }
`

export const GET_QAL_PARADIGM = gql`
  query GetQalParadigm($root: String) {
    qalParadigm(root: $root) {
      root
      rootTransliteration
      citation
      citationTransliteration
      definition
      availableRoots
      forms {
        conjugation
        person
        number
        gender
        label
        hebrew
        transliteration
      }
    }
  }
`

export const GET_QAL_WORKSHEET = gql`
  query GetQalWorksheet($numBlanks: Int!, $root: String, $conjugations: [String!]) {
    qalWorksheet(numBlanks: $numBlanks, root: $root, conjugations: $conjugations) {
      root
      rootTransliteration
      citation
      citationTransliteration
      definition
      numBlanks
      forms {
        conjugation
        person
        number
        gender
        label
        hebrew
        transliteration
        answerHebrew
        answerTransliteration
        isBlank
      }
    }
  }
`

export const GRADE_QAL_WORKSHEET = gql`
  mutation GradeQalWorksheet($input: GradeQalWorksheetInput!) {
    gradeQalWorksheet(input: $input) {
      total
      correctCount
      items {
        index
        label
        correct
        expected
        submitted
        feedback
      }
    }
  }
`

export const TAHOT_BOOKS = gql`
  query TahotBooks {
    tahotBooks {
      abbrev
      chapters
    }
  }
`

export const TAHOT_CHAPTER_VERSES = gql`
  query TahotChapterVerses($book: String!) {
    tahotChapterVerses(book: $book) {
      chapter
      verseCount
    }
  }
`

export const TAHOT_VERSE = gql`
  query TahotVerse($book: String!, $chapter: Int!, $verse: Int!) {
    tahotVerse(book: $book, chapter: $chapter, verse: $verse) {
      ref
      book
      chapter
      verse
      token
      textType
      hebrew
      transliteration
      translation
      dstrongs
      grammar
      rootStrongs
      expanded
    }
  }
`

export const TAHOT_CHAPTER = gql`
  query TahotChapter($book: String!, $chapter: Int!) {
    tahotChapter(book: $book, chapter: $chapter) {
      ref
      verse
      token
      textType
      hebrew
      transliteration
      translation
      dstrongs
      grammar
      rootStrongs
      expanded
    }
  }
`

export const TAHOT_SEARCH = gql`
  query TahotSearch($query: String!, $limit: Int) {
    tahotSearch(query: $query, limit: $limit) {
      ref
      book
      chapter
      verse
      token
      textType
      hebrew
      transliteration
      translation
      dstrongs
      grammar
      rootStrongs
    }
  }
`

export const TAHOT_CHAPTER_TRANSLATIONS = gql`
  query TahotChapterTranslations($book: String!, $chapter: Int!) {
    tahotChapterTranslations(book: $book, chapter: $chapter) {
      verse
      text
    }
  }
`

export const INTERLINEAR_PASSAGE = gql`
  query InterlinearPassage(
    $source: String!
    $book: String!
    $startChapter: Int!
    $startVerse: Int!
    $endChapter: Int
    $endVerse: Int
  ) {
    interlinearPassage(
      source: $source
      book: $book
      startChapter: $startChapter
      startVerse: $startVerse
      endChapter: $endChapter
      endVerse: $endVerse
    ) {
      book
      chapter
      verse
      words {
        ref
        position
        textType
        native
        transliteration
        gloss
        morphology
        lemmaId
        lemma
        lemmaDefinition
      }
    }
  }
`

export const GET_GREEK_DECLENSION_EXERCISES = gql`
  query GetGreekDeclensionExercises($count: Int, $maxLesson: Int, $variant: GreekVariant) {
    greekDeclensionExercises(count: $count, maxLesson: $maxLesson, variant: $variant) {
      id
      dictForm
      definition
      case
      number
      prompt
      answer
      lesson
      variant
    }
  }
`

export const GET_GREEK_CONJUGATION_EXERCISES = gql`
  query GetGreekConjugationExercises($count: Int, $maxLesson: Int, $variant: GreekVariant) {
    greekConjugationExercises(count: $count, maxLesson: $maxLesson, variant: $variant) {
      id
      dictForm
      definition
      person
      number
      prompt
      answer
      lesson
      variant
    }
  }
`

export const GRADE_GREEK_EXERCISE = gql`
  mutation GradeGreekExercise($input: GradeGreekExerciseInput!) {
    gradeGreekExercise(input: $input) {
      correct
      expected
      submitted
      feedback
    }
  }
`

export const GET_SANSKRIT_DECLENSION_EXERCISES = gql`
  query GetSanskritDeclensionExercises($count: Int, $maxLesson: Int) {
    sanskritDeclensionExercises(count: $count, maxLesson: $maxLesson) {
      id
      dictForm
      devanagari
      definition
      case
      number
      prompt
      answer
      lesson
    }
  }
`

export const GRADE_SANSKRIT_EXERCISE = gql`
  mutation GradeSanskritExercise($input: GradeSanskritExerciseInput!) {
    gradeSanskritExercise(input: $input) {
      correct
      expected
      submitted
      feedback
    }
  }
`

export const STRONGS_ENTRY = gql`
  query StrongsEntry($strongsId: String!) {
    strongsEntry(strongsId: $strongsId) {
      strongsId
      eStrongsId
      native
      transliteration
      morph
      gloss
      meaning
    }
  }
`
