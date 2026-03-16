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
    mutate_grade_preposition_exercise,
    mutate_grade_relative_clause_exercise,
    mutate_grade_translation_exercise,
    mutate_grade_verbal_exercise,
    mutate_submit_review,
    mutate_synthesize_speech,
    resolve_article_exercises,
    resolve_cards,
    resolve_comparative_exercises,
    resolve_deck,
    resolve_decks,
    resolve_due_cards,
    resolve_lexicon_search,
    resolve_preposition_exercises,
    resolve_relative_clause_exercises,
    resolve_sentence_exercises,
    resolve_translation_exercises,
    resolve_verbal_exercises,
)
from reshith.api.types import (
    ArticleDirection,
    ArticleExercise,
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
    GradeRelativeClauseInput,
    GradeTranslationInput,
    GradeVerbalInput,
    LanguageCode,
    LexiconEntry,
    PrepositionExercise,
    PrepositionType,
    RelativeClauseExercise,
    RelativeClauseGradeResult,
    ReviewInput,
    ReviewResult,
    SentenceExercise,
    SentencePattern,
    SpeechSynthesisResult,
    TranslationExercise,
    TranslationGradeResult,
    TranslationHelp,
    TranslationPattern,
    VerbalExercise,
    VerbalGradeResult,
    VerbalPattern,
)


@strawberry.type
class Query:
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


@strawberry.type
class Mutation:
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


schema = strawberry.Schema(query=Query, mutation=Mutation)
