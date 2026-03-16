import { gql } from '@apollo/client'

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
