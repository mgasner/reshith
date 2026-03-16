"""GraphQL resolvers."""

from datetime import datetime
from uuid import UUID

import strawberry
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from reshith.api.types import (
    ArticleDirection,
    ArticleExercise,
    Card,
    CardWithSRS,
    ComparativeExercise,
    ComparativeGradeResult,
    ComparativePattern,
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
    RelativeClausePattern,
    ReviewInput,
    ReviewResult,
    SentenceExercise,
    SentencePattern,
    SpeechSynthesisResult,
    SRSState,
    TranslationExercise,
    TranslationGradeResult,
    TranslationHelp,
    TranslationPattern,
    VerbalExercise,
    VerbalGradeResult,
    VerbalPattern,
)
from reshith.db import models
from reshith.exercises import advanced as advanced_exercises
from reshith.exercises import article as article_exercises
from reshith.exercises import prepositions as prep_exercises
from reshith.exercises import sentences as sentence_exercises
from reshith.exercises import translation as translation_exercises
from reshith.exercises import verbal as verbal_exercises
from reshith.services import llm, srs, tts


def db_language_to_gql(db_lang: models.LanguageCode) -> LanguageCode:
    return LanguageCode(db_lang.value)


def gql_language_to_db(gql_lang: LanguageCode) -> models.LanguageCode:
    return models.LanguageCode(gql_lang.value)


async def resolve_decks(
    info: strawberry.Info,
    language: LanguageCode | None = None,
) -> list[Deck]:
    session: AsyncSession = info.context["db"]

    query = select(models.Deck)
    if language:
        query = query.where(models.Deck.language == gql_language_to_db(language))

    result = await session.execute(query)
    decks = result.scalars().all()

    deck_list = []
    for deck in decks:
        count_query = select(func.count()).where(models.Card.deck_id == deck.id)
        count_result = await session.execute(count_query)
        card_count = count_result.scalar() or 0

        deck_list.append(
            Deck(
                id=deck.id,
                name=deck.name,
                description=deck.description,
                language=db_language_to_gql(deck.language),
                created_at=deck.created_at,
                updated_at=deck.updated_at,
                card_count=card_count,
            )
        )

    return deck_list


async def resolve_deck(info: strawberry.Info, id: UUID) -> Deck | None:
    session: AsyncSession = info.context["db"]

    result = await session.execute(select(models.Deck).where(models.Deck.id == id))
    deck = result.scalar_one_or_none()

    if not deck:
        return None

    count_query = select(func.count()).where(models.Card.deck_id == deck.id)
    count_result = await session.execute(count_query)
    card_count = count_result.scalar() or 0

    return Deck(
        id=deck.id,
        name=deck.name,
        description=deck.description,
        language=db_language_to_gql(deck.language),
        created_at=deck.created_at,
        updated_at=deck.updated_at,
        card_count=card_count,
    )


async def resolve_cards(info: strawberry.Info, deck_id: UUID) -> list[Card]:
    session: AsyncSession = info.context["db"]

    result = await session.execute(select(models.Card).where(models.Card.deck_id == deck_id))
    cards = result.scalars().all()

    return [
        Card(
            id=card.id,
            deck_id=card.deck_id,
            front=card.front,
            back=card.back,
            notes=card.notes,
            transliteration=card.transliteration,
            grammatical_info=card.grammatical_info,
            source_reference=card.source_reference,
            created_at=card.created_at,
            updated_at=card.updated_at,
        )
        for card in cards
    ]


async def resolve_due_cards(
    info: strawberry.Info,
    user_id: UUID,
    deck_id: UUID | None = None,
    limit: int = 20,
) -> list[CardWithSRS]:
    session: AsyncSession = info.context["db"]

    query = (
        select(models.Card, models.SRSState)
        .outerjoin(models.SRSState, models.Card.id == models.SRSState.card_id)
        .where(
            (models.SRSState.next_review <= datetime.now()) | (models.SRSState.id.is_(None))
        )
    )

    if deck_id:
        query = query.where(models.Card.deck_id == deck_id)

    query = query.limit(limit)

    result = await session.execute(query)
    rows = result.all()

    return [
        CardWithSRS(
            card=Card(
                id=card.id,
                deck_id=card.deck_id,
                front=card.front,
                back=card.back,
                notes=card.notes,
                transliteration=card.transliteration,
                grammatical_info=card.grammatical_info,
                source_reference=card.source_reference,
                created_at=card.created_at,
                updated_at=card.updated_at,
            ),
            srs=SRSState(
                easiness_factor=srs_state.easiness_factor,
                interval_days=srs_state.interval_days,
                repetitions=srs_state.repetitions,
                next_review=srs_state.next_review,
            )
            if srs_state
            else None,
        )
        for card, srs_state in rows
    ]


async def resolve_lexicon_search(
    info: strawberry.Info,
    query: str,
    language: LanguageCode,
    limit: int = 20,
) -> list[LexiconEntry]:
    session: AsyncSession = info.context["db"]

    db_query = (
        select(models.LexiconEntry)
        .where(models.LexiconEntry.language == gql_language_to_db(language))
        .where(models.LexiconEntry.lemma.ilike(f"%{query}%"))
        .limit(limit)
    )

    result = await session.execute(db_query)
    entries = result.scalars().all()

    return [
        LexiconEntry(
            id=entry.id,
            language=db_language_to_gql(entry.language),
            lemma=entry.lemma,
            transliteration=entry.transliteration,
            definition=entry.definition,
            part_of_speech=entry.part_of_speech,
            morphology=entry.morphology,
            frequency=entry.frequency,
        )
        for entry in entries
    ]


async def mutate_create_deck(info: strawberry.Info, input: CreateDeckInput) -> Deck:
    session: AsyncSession = info.context["db"]

    deck = models.Deck(
        name=input.name,
        description=input.description,
        language=gql_language_to_db(input.language),
        owner_id=info.context.get("user_id"),
    )
    session.add(deck)
    await session.flush()

    return Deck(
        id=deck.id,
        name=deck.name,
        description=deck.description,
        language=db_language_to_gql(deck.language),
        created_at=deck.created_at,
        updated_at=deck.updated_at,
        card_count=0,
    )


async def mutate_create_card(info: strawberry.Info, input: CreateCardInput) -> Card:
    session: AsyncSession = info.context["db"]

    card = models.Card(
        deck_id=input.deck_id,
        front=input.front,
        back=input.back,
        notes=input.notes,
        transliteration=input.transliteration,
        grammatical_info=input.grammatical_info,
        source_reference=input.source_reference,
    )
    session.add(card)
    await session.flush()

    return Card(
        id=card.id,
        deck_id=card.deck_id,
        front=card.front,
        back=card.back,
        notes=card.notes,
        transliteration=card.transliteration,
        grammatical_info=card.grammatical_info,
        source_reference=card.source_reference,
        created_at=card.created_at,
        updated_at=card.updated_at,
    )


async def mutate_submit_review(
    info: strawberry.Info,
    input: ReviewInput,
) -> ReviewResult:
    session: AsyncSession = info.context["db"]
    user_id: UUID = info.context["user_id"]

    result = await session.execute(
        select(models.SRSState).where(models.SRSState.card_id == input.card_id)
    )
    srs_state = result.scalar_one_or_none()

    if srs_state:
        update = srs.calculate_sm2(
            quality=input.quality,
            easiness_factor=srs_state.easiness_factor,
            interval_days=srs_state.interval_days,
            repetitions=srs_state.repetitions,
        )
        srs_state.easiness_factor = update.easiness_factor
        srs_state.interval_days = update.interval_days
        srs_state.repetitions = update.repetitions
        srs_state.next_review = update.next_review
    else:
        update = srs.calculate_sm2(
            quality=input.quality,
            easiness_factor=2.5,
            interval_days=0,
            repetitions=0,
        )
        srs_state = models.SRSState(
            card_id=input.card_id,
            user_id=user_id,
            easiness_factor=update.easiness_factor,
            interval_days=update.interval_days,
            repetitions=update.repetitions,
            next_review=update.next_review,
        )
        session.add(srs_state)

    review = models.Review(
        user_id=user_id,
        card_id=input.card_id,
        quality=input.quality,
    )
    session.add(review)
    await session.flush()

    return ReviewResult(
        card_id=input.card_id,
        new_srs=SRSState(
            easiness_factor=update.easiness_factor,
            interval_days=update.interval_days,
            repetitions=update.repetitions,
            next_review=update.next_review,
        ),
    )


async def mutate_get_translation_help(
    info: strawberry.Info,
    text: str,
    language: LanguageCode,
    context: str | None = None,
) -> TranslationHelp:
    language_names = {
        LanguageCode.BIBLICAL_HEBREW: "Biblical Hebrew",
        LanguageCode.LATIN: "Latin",
        LanguageCode.ANCIENT_GREEK: "Ancient Greek",
        LanguageCode.SANSKRIT: "Sanskrit",
        LanguageCode.PALI: "Pali",
        LanguageCode.BUDDHIST_HYBRID_SANSKRIT: "Buddhist Hybrid Sanskrit",
        LanguageCode.ARAMAIC: "Aramaic",
        LanguageCode.MIDRASHIC_HEBREW: "Midrashic Hebrew",
    }

    result = await llm.get_translation_help(
        text=text,
        language=language_names.get(language, "Unknown"),
        context=context,
    )

    return TranslationHelp(translation=result, notes=None)


async def mutate_generate_drill(
    info: strawberry.Info,
    vocabulary: list[str],
    language: LanguageCode,
    difficulty: str = "intermediate",
) -> Drill:
    language_names = {
        LanguageCode.BIBLICAL_HEBREW: "Biblical Hebrew",
        LanguageCode.LATIN: "Latin",
        LanguageCode.ANCIENT_GREEK: "Ancient Greek",
        LanguageCode.SANSKRIT: "Sanskrit",
        LanguageCode.PALI: "Pali",
        LanguageCode.BUDDHIST_HYBRID_SANSKRIT: "Buddhist Hybrid Sanskrit",
        LanguageCode.ARAMAIC: "Aramaic",
        LanguageCode.MIDRASHIC_HEBREW: "Midrashic Hebrew",
    }

    result = await llm.generate_drill(
        vocabulary=vocabulary,
        language=language_names.get(language, "Unknown"),
        difficulty=difficulty,
    )

    return Drill(
        text=result.get("text", ""),
        translation=result.get("translation", ""),
        notes=result.get("notes"),
    )


def prep_type_to_gql(prep: prep_exercises.Preposition) -> PrepositionType:
    return PrepositionType(prep.value)


def gql_to_prep_type(gql_prep: PrepositionType) -> prep_exercises.Preposition:
    return prep_exercises.Preposition(gql_prep.value)


def direction_to_gql(direction: str) -> ExerciseDirection:
    if direction == "hebrew_to_english":
        return ExerciseDirection.HEBREW_TO_ENGLISH
    return ExerciseDirection.ENGLISH_TO_HEBREW


def gql_to_direction(gql_dir: ExerciseDirection) -> str:
    return gql_dir.value


async def resolve_preposition_exercises(
    info: strawberry.Info,
    count: int = 10,
    direction: ExerciseDirection = ExerciseDirection.HEBREW_TO_ENGLISH,
    prepositions: list[PrepositionType] | None = None,
    max_lesson: int = 1,
) -> list[PrepositionExercise]:
    """Generate preposition exercises using vocabulary up to max_lesson."""
    prep_list = None
    if prepositions:
        prep_list = [gql_to_prep_type(p) for p in prepositions]

    nouns = prep_exercises.load_nouns_up_to_lesson(max_lesson)
    if not nouns:
        return []

    phrases = prep_exercises.generate_exercises(
        nouns=nouns,
        prepositions=prep_list,
        count=count,
    )

    exercises = []
    for i, phrase in enumerate(phrases):
        exercise = prep_exercises.create_exercise(phrase, gql_to_direction(direction))
        exercises.append(
            PrepositionExercise(
                id=f"prep-{i}-{hash(phrase.hebrew)}",
                hebrew=phrase.hebrew,
                transliteration=phrase.transliteration,
                english=phrase.english,
                preposition=prep_type_to_gql(phrase.preposition),
                noun_hebrew=phrase.noun.hebrew,
                noun_definition=phrase.noun.definition,
                direction=direction,
                prompt=exercise.prompt,
                answer=exercise.answer,
            )
        )

    return exercises


async def mutate_grade_preposition_exercise(
    info: strawberry.Info,
    input: GradeExerciseInput,
) -> ExerciseGradeResult:
    """Grade a preposition exercise submission."""
    if input.direction == ExerciseDirection.HEBREW_TO_ENGLISH:
        submitted_norm = prep_exercises.normalize_english(input.submitted)
        expected_norm = prep_exercises.normalize_english(input.expected_english)

        correct = False
        for prep in prep_exercises.Preposition:
            prep_data = prep_exercises.PREPOSITION_DATA[prep]
            for prep_eng in prep_data["english"]:
                if prep_eng in submitted_norm:
                    correct = True
                    break

        if submitted_norm == expected_norm:
            correct = True

        if correct:
            feedback = "Correct!"
        else:
            feedback = f"Expected something like: '{input.expected_english}'"

        return ExerciseGradeResult(
            correct=correct,
            expected=input.expected_english,
            submitted=input.submitted,
            feedback=feedback,
        )
    else:
        submitted_norm = prep_exercises.normalize_hebrew(input.submitted)
        expected_norm = prep_exercises.normalize_hebrew(input.expected_hebrew)

        correct = submitted_norm == expected_norm

        if correct:
            feedback = "Correct!"
        else:
            feedback = f"Expected: {input.expected_hebrew}"

        return ExerciseGradeResult(
            correct=correct,
            expected=input.expected_hebrew,
            submitted=input.submitted,
            feedback=feedback,
        )


async def mutate_synthesize_speech(
    info: strawberry.Info,
    text: str,
    language: str = "he-IL",
) -> SpeechSynthesisResult:
    """Synthesize speech for the given text using Google Cloud TTS.

    If Google Cloud TTS is not available, returns available=False so the
    frontend can fall back to the Web Speech API.
    """
    if not tts.is_available():
        return SpeechSynthesisResult(
            available=False,
            audio_base64=None,
            text=text,
            language=language,
        )

    audio_base64 = await tts.synthesize_speech(text, language)

    return SpeechSynthesisResult(
        available=audio_base64 is not None,
        audio_base64=audio_base64,
        text=text,
        language=language,
    )


def article_direction_to_str(direction: ArticleDirection) -> str:
    """Convert GraphQL ArticleDirection to string."""
    return direction.value


async def resolve_article_exercises(
    info: strawberry.Info,
    count: int = 10,
    direction: ArticleDirection = ArticleDirection.INDEFINITE_TO_DEFINITE,
    max_lesson: int = 1,
) -> list[ArticleExercise]:
    """Generate definite article exercises."""
    phrases = article_exercises.generate_article_exercises(
        max_lesson=max_lesson,
        count=count,
    )

    exercises = []
    for i, phrase in enumerate(phrases):
        exercise = article_exercises.create_article_exercise(
            phrase, article_direction_to_str(direction)
        )
        exercises.append(
            ArticleExercise(
                id=f"article-{i}-{hash(phrase.hebrew_definite)}",
                hebrew_indefinite=phrase.hebrew_indefinite,
                hebrew_definite=phrase.hebrew_definite,
                transliteration_indefinite=phrase.transliteration_indefinite,
                transliteration_definite=phrase.transliteration_definite,
                english_indefinite=phrase.english_indefinite,
                english_definite=phrase.english_definite,
                article_type=phrase.article_type.value,
                direction=direction,
                prompt=exercise.prompt,
                prompt_transliteration=exercise.prompt_transliteration,
                answer=exercise.answer,
                answer_transliteration=exercise.answer_transliteration,
            )
        )

    return exercises


async def mutate_grade_article_exercise(
    info: strawberry.Info,
    input: GradeArticleExerciseInput,
) -> ExerciseGradeResult:
    """Grade an article exercise submission."""
    submitted_norm = article_exercises.normalize_hebrew(input.submitted)

    if input.direction == ArticleDirection.INDEFINITE_TO_DEFINITE:
        expected_norm = article_exercises.normalize_hebrew(input.expected_definite)
        expected_display = input.expected_definite
    else:
        expected_norm = article_exercises.normalize_hebrew(input.expected_indefinite)
        expected_display = input.expected_indefinite

    correct = submitted_norm == expected_norm

    if correct:
        feedback = "Correct!"
    else:
        feedback = f"Expected: {expected_display}"

    return ExerciseGradeResult(
        correct=correct,
        expected=expected_display,
        submitted=input.submitted,
        feedback=feedback,
    )


def sentence_pattern_to_str(pattern: SentencePattern) -> str:
    """Convert GraphQL SentencePattern to string."""
    return pattern.value


def str_to_sentence_pattern(pattern_str: str) -> SentencePattern:
    """Convert string to GraphQL SentencePattern."""
    return SentencePattern(pattern_str)


async def resolve_sentence_exercises(
    info: strawberry.Info,
    count: int = 10,
    max_lesson: int = 1,
    patterns: list[SentencePattern] | None = None,
) -> list[SentenceExercise]:
    """Generate sentence-level exercises."""
    import json

    pattern_strs = None
    if patterns:
        pattern_strs = [sentence_pattern_to_str(p) for p in patterns]

    exercises = await sentence_exercises.generate_sentence_exercises(
        max_lesson=max_lesson,
        count=count,
        patterns=pattern_strs,
    )

    result = []
    for i, ex in enumerate(exercises):
        result.append(
            SentenceExercise(
                id=f"sentence-{i}-{hash(ex.hebrew)}",
                pattern=str_to_sentence_pattern(ex.pattern),
                hebrew=ex.hebrew,
                transliteration=ex.transliteration,
                english=ex.english,
                components=json.dumps(ex.components),
            )
        )

    return result


def translation_pattern_to_str(pattern: TranslationPattern) -> str:
    """Convert GraphQL TranslationPattern to string."""
    return pattern.value


def str_to_translation_pattern(pattern_str: str) -> TranslationPattern:
    """Convert string to GraphQL TranslationPattern."""
    return TranslationPattern(pattern_str)


async def resolve_translation_exercises(
    info: strawberry.Info,
    count: int = 10,
    max_lesson: int = 1,
    patterns: list[TranslationPattern] | None = None,
) -> list[TranslationExercise]:
    """Generate English-to-Hebrew translation exercises."""
    import json

    pattern_strs = None
    if patterns:
        pattern_strs = [translation_pattern_to_str(p) for p in patterns]

    exercises = await translation_exercises.generate_translation_exercises(
        max_lesson=max_lesson,
        count=count,
        patterns=pattern_strs,
    )

    result = []
    for i, ex in enumerate(exercises):
        result.append(
            TranslationExercise(
                id=f"translation-{i}-{hash(ex.english)}",
                pattern=str_to_translation_pattern(ex.pattern),
                english=ex.english,
                hebrew_answer=ex.hebrew_answer,
                transliteration_answer=ex.transliteration_answer,
                components=json.dumps(ex.components),
            )
        )

    return result


async def mutate_grade_translation_exercise(
    info: strawberry.Info,
    input: GradeTranslationInput,
) -> TranslationGradeResult:
    """Grade an English-to-Hebrew translation exercise."""
    result = translation_exercises.grade_translation(
        submitted=input.submitted,
        expected_hebrew=input.expected_hebrew,
        expected_transliteration=input.expected_transliteration,
    )

    return TranslationGradeResult(
        correct=result.correct,
        score=result.score,
        expected=result.expected,
        submitted=result.submitted,
        feedback=result.feedback,
        transliteration=result.transliteration,
    )


def verbal_pattern_to_str(pattern: VerbalPattern) -> str:
    """Convert GraphQL VerbalPattern to string."""
    return pattern.value


def str_to_verbal_pattern(pattern_str: str) -> VerbalPattern:
    """Convert string to GraphQL VerbalPattern."""
    return VerbalPattern(pattern_str)


async def resolve_verbal_exercises(
    info: strawberry.Info,
    count: int = 10,
    max_lesson: int = 4,
    patterns: list[VerbalPattern] | None = None,
) -> list[VerbalExercise]:
    """Generate Hebrew-to-English verbal sentence exercises."""
    import json

    pattern_strs = None
    if patterns:
        pattern_strs = [verbal_pattern_to_str(p) for p in patterns]

    exercises = await verbal_exercises.generate_verbal_exercises(
        max_lesson=max_lesson,
        count=count,
        patterns=pattern_strs,
    )

    result = []
    for i, ex in enumerate(exercises):
        result.append(
            VerbalExercise(
                id=f"verbal-{i}-{hash(ex.hebrew)}",
                pattern=str_to_verbal_pattern(ex.pattern),
                hebrew=ex.hebrew,
                transliteration=ex.transliteration,
                english_answer=ex.english_answer,
                components=json.dumps(ex.components),
            )
        )

    return result


async def mutate_grade_verbal_exercise(
    info: strawberry.Info,
    input: GradeVerbalInput,
) -> VerbalGradeResult:
    """Grade a Hebrew-to-English verbal exercise."""
    result = verbal_exercises.grade_verbal_exercise(
        submitted=input.submitted,
        expected_english=input.expected_english,
    )

    return VerbalGradeResult(
        correct=result.correct,
        score=result.score,
        expected=result.expected,
        submitted=result.submitted,
        feedback=result.feedback,
    )


def comparative_pattern_to_str(pattern: ComparativePattern) -> str:
    """Convert GraphQL ComparativePattern to string."""
    return pattern.value


def str_to_comparative_pattern(pattern_str: str) -> ComparativePattern:
    """Convert string to GraphQL ComparativePattern."""
    return ComparativePattern(pattern_str)


async def resolve_comparative_exercises(
    info: strawberry.Info,
    count: int = 10,
    max_lesson: int = 5,
) -> list[ComparativeExercise]:
    """Generate comparative construction exercises."""
    import json

    exercises = await advanced_exercises.generate_comparative_exercises(
        max_lesson=max_lesson,
        count=count,
    )

    result = []
    for i, ex in enumerate(exercises):
        result.append(
            ComparativeExercise(
                id=f"comparative-{i}-{hash(ex.hebrew)}",
                pattern=str_to_comparative_pattern(ex.pattern),
                hebrew=ex.hebrew,
                transliteration=ex.transliteration,
                english_answer=ex.english_answer,
                components=json.dumps(ex.components),
            )
        )

    return result


async def mutate_grade_comparative_exercise(
    info: strawberry.Info,
    input: GradeComparativeInput,
) -> ComparativeGradeResult:
    """Grade a Hebrew-to-English comparative exercise."""
    result = advanced_exercises.grade_comparative_exercise(
        submitted=input.submitted,
        expected_english=input.expected_english,
    )

    return ComparativeGradeResult(
        correct=result.correct,
        score=result.score,
        expected=result.expected,
        submitted=result.submitted,
        feedback=result.feedback,
    )


def relative_clause_pattern_to_str(pattern: RelativeClausePattern) -> str:
    """Convert GraphQL RelativeClausePattern to string."""
    return pattern.value


def str_to_relative_clause_pattern(pattern_str: str) -> RelativeClausePattern:
    """Convert string to GraphQL RelativeClausePattern."""
    return RelativeClausePattern(pattern_str)


async def resolve_relative_clause_exercises(
    info: strawberry.Info,
    count: int = 10,
    max_lesson: int = 5,
) -> list[RelativeClauseExercise]:
    """Generate relative clause exercises with אֲשֶׁר."""
    import json

    exercises = await advanced_exercises.generate_relative_clause_exercises(
        max_lesson=max_lesson,
        count=count,
    )

    result = []
    for i, ex in enumerate(exercises):
        result.append(
            RelativeClauseExercise(
                id=f"relative-{i}-{hash(ex.hebrew)}",
                pattern=str_to_relative_clause_pattern(ex.pattern),
                hebrew=ex.hebrew,
                transliteration=ex.transliteration,
                english_answer=ex.english_answer,
                components=json.dumps(ex.components),
            )
        )

    return result


async def mutate_grade_relative_clause_exercise(
    info: strawberry.Info,
    input: GradeRelativeClauseInput,
) -> RelativeClauseGradeResult:
    """Grade a Hebrew-to-English relative clause exercise."""
    result = advanced_exercises.grade_relative_clause_exercise(
        submitted=input.submitted,
        expected_english=input.expected_english,
    )

    return RelativeClauseGradeResult(
        correct=result.correct,
        score=result.score,
        expected=result.expected,
        submitted=result.submitted,
        feedback=result.feedback,
    )
