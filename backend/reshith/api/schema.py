"""GraphQL schema definition."""

from uuid import UUID

import strawberry

from reshith.api.resolvers import (
    mutate_create_card,
    mutate_create_deck,
    mutate_generate_drill,
    mutate_get_translation_help,
    mutate_grade_article_exercise,
    mutate_grade_comparative_exercise,
    mutate_grade_greek_exercise,
    mutate_grade_latin_conjugation_exercise,
    mutate_grade_latin_declension_exercise,
    mutate_grade_preposition_exercise,
    mutate_grade_qal_worksheet,
    mutate_grade_relative_clause_exercise,
    mutate_grade_sanskrit_exercise,
    mutate_grade_translation_exercise,
    mutate_grade_verbal_exercise,
    mutate_login,
    mutate_submit_review,
    mutate_synthesize_speech,
    resolve_article_exercises,
    resolve_cards,
    resolve_comparative_exercises,
    resolve_deck,
    resolve_decks,
    resolve_due_cards,
    resolve_gnt_books,
    resolve_gnt_chapter,
    resolve_gnt_chapter_translations,
    resolve_gnt_chapter_verses,
    resolve_gnt_search,
    resolve_gnt_verse,
    resolve_greek_conjugation_exercises,
    resolve_greek_declension_exercises,
    resolve_interlinear_passage,
    resolve_latin_conjugation_exercises,
    resolve_latin_declension_exercises,
    resolve_lexicon_search,
    resolve_lxx_books,
    resolve_lxx_chapter,
    resolve_lxx_chapter_translations,
    resolve_lxx_chapter_verses,
    resolve_lxx_search,
    resolve_lxx_verse,
    resolve_me,
    resolve_preposition_exercises,
    resolve_qal_paradigm,
    resolve_qal_worksheet,
    resolve_relative_clause_exercises,
    resolve_sanskrit_declension_exercises,
    resolve_sentence_exercises,
    resolve_strongs_entry,
    resolve_tahot_books,
    resolve_tahot_chapter,
    resolve_tahot_chapter_translations,
    resolve_tahot_chapter_verses,
    resolve_tahot_search,
    resolve_tahot_verse,
    resolve_translation_exercises,
    resolve_verbal_exercises,
    resolve_vulgate_books,
    resolve_vulgate_chapter,
    resolve_vulgate_chapter_translations,
    resolve_vulgate_chapter_verses,
    resolve_vulgate_search,
    resolve_vulgate_verse,
)
from reshith.api.types import (
    ArticleDirection,
    ArticleExercise,
    AuthPayload,
    Card,
    CardWithSRS,
    ComparativeExercise,
    ComparativeGradeResult,
    CreateCardInput,
    CreateDeckInput,
    Deck,
    Drill,
    ExerciseDirection,
    ExerciseGradeResult,
    GradeArticleExerciseInput,
    GradeComparativeInput,
    GradeExerciseInput,
    GradeGreekExerciseInput,
    GradeLatinExerciseInput,
    GradeQalWorksheetInput,
    GradeRelativeClauseInput,
    GradeSanskritExerciseInput,
    GradeTranslationInput,
    GradeVerbalInput,
    GreekBookInfo,
    GreekChapterInfo,
    GreekConjugationExercise,
    GreekDeclensionExercise,
    GreekGradeResult,
    GreekVariant,
    GreekVerseTranslation,
    InterlinearVerse,
    LanguageCode,
    LatinConjugationExercise,
    LatinDeclensionExercise,
    LatinGradeResult,
    LatinVariant,
    LexiconEntry,
    LoginInput,
    PrepositionExercise,
    PrepositionType,
    QalParadigm,
    QalWorksheet,
    QalWorksheetGradeResult,
    RelativeClauseExercise,
    RelativeClauseGradeResult,
    ReviewInput,
    ReviewResult,
    SanskritDeclensionExercise,
    SanskritGradeResult,
    SentenceExercise,
    SentencePattern,
    SpeechSynthesisResult,
    StrongsEntry,
    TahotBookInfo,
    TahotChapterInfo,
    TahotVerseTranslation,
    TranslationExercise,
    TranslationGradeResult,
    TranslationHelp,
    TranslationPattern,
    User,
    VerbalExercise,
    VerbalGradeResult,
    VerbalPattern,
    VulgateBookInfo,
    VulgateChapterInfo,
    VulgateVerseTranslation,
)
from reshith.api.types import (
    GreekToken as GreekTokenGQL,
)
from reshith.api.types import (
    TahotWord as TahotWordGQL,
)
from reshith.api.types import (
    VulgateToken as VulgateTokenGQL,
)


@strawberry.type
class Query:
    @strawberry.field
    async def me(self, info: strawberry.Info) -> User | None:
        return await resolve_me(info)

    @strawberry.field
    async def decks(
        self,
        info: strawberry.Info,
        language: LanguageCode | None = None,
    ) -> list[Deck]:
        return await resolve_decks(info, language)

    @strawberry.field
    async def deck(self, info: strawberry.Info, id: UUID) -> Deck | None:
        return await resolve_deck(info, id)

    @strawberry.field
    async def cards(self, info: strawberry.Info, deck_id: UUID) -> list[Card]:
        return await resolve_cards(info, deck_id)

    @strawberry.field
    async def due_cards(
        self,
        info: strawberry.Info,
        user_id: UUID,
        deck_id: UUID | None = None,
        limit: int = 20,
    ) -> list[CardWithSRS]:
        return await resolve_due_cards(info, user_id, deck_id, limit)

    @strawberry.field
    async def lexicon_search(
        self,
        info: strawberry.Info,
        query: str,
        language: LanguageCode,
        limit: int = 20,
    ) -> list[LexiconEntry]:
        return await resolve_lexicon_search(info, query, language, limit)

    @strawberry.field
    async def preposition_exercises(
        self,
        info: strawberry.Info,
        count: int = 10,
        direction: ExerciseDirection = ExerciseDirection.HEBREW_TO_ENGLISH,
        prepositions: list[PrepositionType] | None = None,
        max_lesson: int = 1,
    ) -> list[PrepositionExercise]:
        return await resolve_preposition_exercises(
            info, count, direction, prepositions, max_lesson
        )

    @strawberry.field
    async def article_exercises(
        self,
        info: strawberry.Info,
        count: int = 10,
        direction: ArticleDirection = ArticleDirection.INDEFINITE_TO_DEFINITE,
        max_lesson: int = 1,
    ) -> list[ArticleExercise]:
        return await resolve_article_exercises(info, count, direction, max_lesson)

    @strawberry.field
    async def sentence_exercises(
        self,
        info: strawberry.Info,
        count: int = 10,
        max_lesson: int = 1,
        patterns: list[SentencePattern] | None = None,
    ) -> list[SentenceExercise]:
        return await resolve_sentence_exercises(info, count, max_lesson, patterns)

    @strawberry.field
    async def translation_exercises(
        self,
        info: strawberry.Info,
        count: int = 10,
        max_lesson: int = 1,
        patterns: list[TranslationPattern] | None = None,
    ) -> list[TranslationExercise]:
        return await resolve_translation_exercises(info, count, max_lesson, patterns)

    @strawberry.field
    async def verbal_exercises(
        self,
        info: strawberry.Info,
        count: int = 10,
        max_lesson: int = 4,
        patterns: list[VerbalPattern] | None = None,
    ) -> list[VerbalExercise]:
        return await resolve_verbal_exercises(info, count, max_lesson, patterns)

    @strawberry.field
    async def comparative_exercises(
        self,
        info: strawberry.Info,
        count: int = 10,
        max_lesson: int = 5,
    ) -> list[ComparativeExercise]:
        return await resolve_comparative_exercises(info, count, max_lesson)

    @strawberry.field
    async def relative_clause_exercises(
        self,
        info: strawberry.Info,
        count: int = 10,
        max_lesson: int = 5,
    ) -> list[RelativeClauseExercise]:
        return await resolve_relative_clause_exercises(info, count, max_lesson)

    @strawberry.field
    async def qal_paradigm(
        self,
        info: strawberry.Info,
        root: str | None = None,
    ) -> QalParadigm | None:
        return await resolve_qal_paradigm(info, root)

    @strawberry.field
    async def qal_worksheet(
        self,
        info: strawberry.Info,
        num_blanks: int = 10,
        root: str | None = None,
        conjugations: list[str] | None = None,
    ) -> QalWorksheet | None:
        return await resolve_qal_worksheet(info, num_blanks, root, conjugations)

    @strawberry.field
    async def latin_declension_exercises(
        self,
        info: strawberry.Info,
        count: int = 10,
        max_lesson: int = 2,
        variant: LatinVariant = LatinVariant.CLASSICAL,
    ) -> list[LatinDeclensionExercise]:
        return await resolve_latin_declension_exercises(info, count, max_lesson, variant)

    @strawberry.field
    async def latin_conjugation_exercises(
        self,
        info: strawberry.Info,
        count: int = 10,
        max_lesson: int = 2,
        variant: LatinVariant = LatinVariant.CLASSICAL,
    ) -> list[LatinConjugationExercise]:
        return await resolve_latin_conjugation_exercises(info, count, max_lesson, variant)

    @strawberry.field
    async def greek_declension_exercises(
        self,
        info: strawberry.Info,
        count: int = 10,
        max_lesson: int = 2,
        variant: GreekVariant = GreekVariant.ANCIENT,
    ) -> list[GreekDeclensionExercise]:
        return await resolve_greek_declension_exercises(info, count, max_lesson, variant)

    @strawberry.field
    async def greek_conjugation_exercises(
        self,
        info: strawberry.Info,
        count: int = 10,
        max_lesson: int = 2,
        variant: GreekVariant = GreekVariant.ANCIENT,
    ) -> list[GreekConjugationExercise]:
        return await resolve_greek_conjugation_exercises(info, count, max_lesson, variant)

    @strawberry.field
    async def sanskrit_declension_exercises(
        self,
        info: strawberry.Info,
        count: int = 10,
        max_lesson: int = 2,
    ) -> list[SanskritDeclensionExercise]:
        return await resolve_sanskrit_declension_exercises(info, count, max_lesson)

    @strawberry.field
    def interlinear_passage(
        self,
        source: str,
        book: str,
        start_chapter: int,
        start_verse: int,
        end_chapter: int | None = None,
        end_verse: int | None = None,
    ) -> list[InterlinearVerse]:
        """Return interlinear text for a passage range.

        source: corpus identifier — currently "TAHOT" (Hebrew OT).
        Range is inclusive: start_chapter:start_verse – end_chapter:end_verse.
        Omitting end_chapter/end_verse extends to end of start_chapter.

        Example — Genesis 1:1–3:4:
          interlinearPassage(source: "TAHOT", book: "Gen",
                             startChapter: 1, startVerse: 1,
                             endChapter: 3, endVerse: 4)
        """
        return resolve_interlinear_passage(
            source, book, start_chapter, start_verse, end_chapter, end_verse
        )

    @strawberry.field
    def tahot_books(self) -> list[TahotBookInfo]:
        return resolve_tahot_books()

    @strawberry.field
    def tahot_chapter_verses(self, book: str) -> list[TahotChapterInfo]:
        return resolve_tahot_chapter_verses(book)

    @strawberry.field
    def tahot_verse(self, book: str, chapter: int, verse: int) -> list[TahotWordGQL]:
        return resolve_tahot_verse(book, chapter, verse)

    @strawberry.field
    def tahot_chapter(self, book: str, chapter: int) -> list[TahotWordGQL]:
        return resolve_tahot_chapter(book, chapter)

    @strawberry.field
    def tahot_search(self, query: str, limit: int = 50) -> list[TahotWordGQL]:
        return resolve_tahot_search(query, limit)

    @strawberry.field
    def tahot_chapter_translations(self, book: str, chapter: int) -> list[TahotVerseTranslation]:
        """JPS 1917 translation for a chapter (public domain Jewish translation)."""
        return resolve_tahot_chapter_translations(book, chapter)

    @strawberry.field
    def strongs_entry(self, strongs_id: str) -> StrongsEntry | None:
        """Look up a TBESH (Hebrew) or TBESG (Greek) lexicon entry by Extended Strong's ID."""
        return resolve_strongs_entry(strongs_id)

    @strawberry.field
    def vulgate_books(self) -> list[VulgateBookInfo]:
        return resolve_vulgate_books()

    @strawberry.field
    def vulgate_chapter_verses(self, book: str) -> list[VulgateChapterInfo]:
        return resolve_vulgate_chapter_verses(book)

    @strawberry.field
    def vulgate_verse(self, book: str, chapter: int, verse: int) -> list[VulgateTokenGQL]:
        return resolve_vulgate_verse(book, chapter, verse)

    @strawberry.field
    def vulgate_chapter(self, book: str, chapter: int) -> list[VulgateTokenGQL]:
        return resolve_vulgate_chapter(book, chapter)

    @strawberry.field
    def vulgate_search(self, query: str, limit: int = 50) -> list[VulgateTokenGQL]:
        return resolve_vulgate_search(query, limit)

    @strawberry.field
    def vulgate_chapter_translations(
        self, book: str, chapter: int,
    ) -> list[VulgateVerseTranslation]:
        return resolve_vulgate_chapter_translations(book, chapter)

    # ── GNT ──────────────────────────────────────────────────────────────────

    @strawberry.field
    def gnt_books(self) -> list[GreekBookInfo]:
        return resolve_gnt_books()

    @strawberry.field
    def gnt_chapter_verses(self, book: str) -> list[GreekChapterInfo]:
        return resolve_gnt_chapter_verses(book)

    @strawberry.field
    def gnt_verse(self, book: str, chapter: int, verse: int) -> list[GreekTokenGQL]:
        return resolve_gnt_verse(book, chapter, verse)

    @strawberry.field
    def gnt_chapter(self, book: str, chapter: int) -> list[GreekTokenGQL]:
        return resolve_gnt_chapter(book, chapter)

    @strawberry.field
    def gnt_search(self, query: str, limit: int = 50) -> list[GreekTokenGQL]:
        return resolve_gnt_search(query, limit)

    @strawberry.field
    def gnt_chapter_translations(self, book: str, chapter: int) -> list[GreekVerseTranslation]:
        return resolve_gnt_chapter_translations(book, chapter)

    # ── LXX ──────────────────────────────────────────────────────────────────

    @strawberry.field
    def lxx_books(self) -> list[GreekBookInfo]:
        return resolve_lxx_books()

    @strawberry.field
    def lxx_chapter_verses(self, book: str) -> list[GreekChapterInfo]:
        return resolve_lxx_chapter_verses(book)

    @strawberry.field
    def lxx_verse(self, book: str, chapter: int, verse: int) -> list[GreekTokenGQL]:
        return resolve_lxx_verse(book, chapter, verse)

    @strawberry.field
    def lxx_chapter(self, book: str, chapter: int) -> list[GreekTokenGQL]:
        return resolve_lxx_chapter(book, chapter)

    @strawberry.field
    def lxx_search(self, query: str, limit: int = 50) -> list[GreekTokenGQL]:
        return resolve_lxx_search(query, limit)

    @strawberry.field
    def lxx_chapter_translations(self, book: str, chapter: int) -> list[GreekVerseTranslation]:
        return resolve_lxx_chapter_translations(book, chapter)


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def login(self, info: strawberry.Info, input: LoginInput) -> AuthPayload | None:
        return await mutate_login(info, input)

    @strawberry.mutation
    async def create_deck(self, info: strawberry.Info, input: CreateDeckInput) -> Deck:
        return await mutate_create_deck(info, input)

    @strawberry.mutation
    async def create_card(self, info: strawberry.Info, input: CreateCardInput) -> Card:
        return await mutate_create_card(info, input)

    @strawberry.mutation
    async def submit_review(self, info: strawberry.Info, input: ReviewInput) -> ReviewResult:
        return await mutate_submit_review(info, input)

    @strawberry.mutation
    async def get_translation_help(
        self,
        info: strawberry.Info,
        text: str,
        language: LanguageCode,
        context: str | None = None,
    ) -> TranslationHelp:
        return await mutate_get_translation_help(info, text, language, context)

    @strawberry.mutation
    async def generate_drill(
        self,
        info: strawberry.Info,
        vocabulary: list[str],
        language: LanguageCode,
        difficulty: str = "intermediate",
    ) -> Drill:
        return await mutate_generate_drill(info, vocabulary, language, difficulty)

    @strawberry.mutation
    async def grade_preposition_exercise(
        self,
        info: strawberry.Info,
        input: GradeExerciseInput,
    ) -> ExerciseGradeResult:
        return await mutate_grade_preposition_exercise(info, input)

    @strawberry.mutation
    async def grade_article_exercise(
        self,
        info: strawberry.Info,
        input: GradeArticleExerciseInput,
    ) -> ExerciseGradeResult:
        return await mutate_grade_article_exercise(info, input)

    @strawberry.mutation
    async def synthesize_speech(
        self,
        info: strawberry.Info,
        text: str,
        language: str = "he-IL",
    ) -> SpeechSynthesisResult:
        return await mutate_synthesize_speech(info, text, language)

    @strawberry.mutation
    async def grade_translation_exercise(
        self,
        info: strawberry.Info,
        input: GradeTranslationInput,
    ) -> TranslationGradeResult:
        return await mutate_grade_translation_exercise(info, input)

    @strawberry.mutation
    async def grade_verbal_exercise(
        self,
        info: strawberry.Info,
        input: GradeVerbalInput,
    ) -> VerbalGradeResult:
        return await mutate_grade_verbal_exercise(info, input)

    @strawberry.mutation
    async def grade_comparative_exercise(
        self,
        info: strawberry.Info,
        input: GradeComparativeInput,
    ) -> ComparativeGradeResult:
        return await mutate_grade_comparative_exercise(info, input)

    @strawberry.mutation
    async def grade_relative_clause_exercise(
        self,
        info: strawberry.Info,
        input: GradeRelativeClauseInput,
    ) -> RelativeClauseGradeResult:
        return await mutate_grade_relative_clause_exercise(info, input)

    @strawberry.mutation
    async def grade_qal_worksheet(
        self,
        info: strawberry.Info,
        input: GradeQalWorksheetInput,
    ) -> QalWorksheetGradeResult:
        return await mutate_grade_qal_worksheet(info, input)

    @strawberry.mutation
    async def grade_latin_declension_exercise(
        self,
        info: strawberry.Info,
        input: GradeLatinExerciseInput,
    ) -> LatinGradeResult:
        return await mutate_grade_latin_declension_exercise(info, input)

    @strawberry.mutation
    async def grade_latin_conjugation_exercise(
        self,
        info: strawberry.Info,
        input: GradeLatinExerciseInput,
    ) -> LatinGradeResult:
        return await mutate_grade_latin_conjugation_exercise(info, input)

    @strawberry.mutation
    async def grade_greek_exercise(
        self,
        info: strawberry.Info,
        input: GradeGreekExerciseInput,
    ) -> GreekGradeResult:
        return await mutate_grade_greek_exercise(info, input)

    @strawberry.mutation
    async def grade_sanskrit_exercise(
        self,
        info: strawberry.Info,
        input: GradeSanskritExerciseInput,
    ) -> SanskritGradeResult:
        return await mutate_grade_sanskrit_exercise(info, input)


schema = strawberry.Schema(query=Query, mutation=Mutation)
