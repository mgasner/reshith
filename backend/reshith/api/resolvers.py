"""GraphQL resolvers."""

import re
from datetime import datetime
from uuid import UUID

import strawberry
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from reshith.api.types import (
    ArticleDirection,
    ArticleExercise,
    AuthPayload,
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
    InterlinearWord,
    LanguageCode,
    LatinConjugationExercise,
    LatinDeclensionExercise,
    LatinGradeResult,
    LatinVariant,
    LexiconEntry,
    LoginInput,
    PrepositionExercise,
    PrepositionType,
    QalWorksheetGradeItem,
    QalWorksheetGradeResult,
    RelativeClauseExercise,
    RelativeClauseGradeResult,
    RelativeClausePattern,
    ReviewInput,
    ReviewResult,
    SanskritDeclensionExercise,
    SanskritGradeResult,
    SentenceExercise,
    SentencePattern,
    SpeechSynthesisResult,
    SRSState,
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
from reshith.api.types import QalParadigm as QalParadigmGQL
from reshith.api.types import QalParadigmForm as QalParadigmFormGQL
from reshith.api.types import QalWorksheet as QalWorksheetGQL
from reshith.api.types import QalWorksheetForm as QalWorksheetFormGQL
from reshith.api.types import (
    StrongsEntry as StrongsEntryGQL,
)
from reshith.api.types import (
    TahotWord as TahotWordGQL,
)
from reshith.api.types import (
    VulgateToken as VulgateTokenGQL,
)
from reshith.db import models
from reshith.exercises import advanced as advanced_exercises
from reshith.exercises import article as article_exercises
from reshith.exercises import prepositions as prep_exercises
from reshith.exercises import sentences as sentence_exercises
from reshith.exercises import translation as translation_exercises
from reshith.exercises import verb_paradigm
from reshith.exercises import verbal as verbal_exercises
from reshith.exercises.greek import conjugation as greek_conjugation
from reshith.exercises.greek import declension as greek_declension
from reshith.exercises.latin import conjugation as latin_conjugation
from reshith.exercises.latin import declension as latin_declension
from reshith.exercises.sanskrit import declension as sanskrit_declension
from reshith.services import brenton as brenton_svc
from reshith.services import drc as drc_svc
from reshith.services import gnt as gnt_svc
from reshith.services import jps as jps_svc
from reshith.services import kjv as kjv_svc
from reshith.services import llm, srs, tts
from reshith.services import lxx as lxx_svc
from reshith.services import tahot as tahot_svc
from reshith.services import tbesh as tbesh_svc
from reshith.services import vulgate as vulgate_svc
from reshith.services.auth import create_access_token, verify_password


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
                lesson=phrase.lesson,
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
    # Latin and Sanskrit route to local models regardless of Google TTS availability
    if language not in ("la", "sa") and not tts.is_available():
        return SpeechSynthesisResult(
            available=False,
            audio_base64=None,
            mime_type="audio/mp3",
            text=text,
            language=language,
        )

    result = await tts.synthesize_speech(text, language)

    if result is None:
        return SpeechSynthesisResult(
            available=False,
            audio_base64=None,
            mime_type="audio/mp3",
            text=text,
            language=language,
        )

    audio_base64, mime_type = result
    return SpeechSynthesisResult(
        available=True,
        audio_base64=audio_base64,
        mime_type=mime_type,
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
                lesson=phrase.noun.lesson,
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
                lesson=ex.lesson,
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


# ── Latin exercise resolvers ──────────────────────────────────────────────────

async def resolve_latin_declension_exercises(
    info: strawberry.Info,
    count: int = 10,
    max_lesson: int = 2,
    variant: LatinVariant = LatinVariant.CLASSICAL,
) -> list[LatinDeclensionExercise]:
    exercises = latin_declension.generate_exercises(
        max_lesson=max_lesson, count=count, variant=variant.value,
    )
    return [
        LatinDeclensionExercise(
            id=ex.id,
            dict_form=ex.dict_form,
            definition=ex.definition,
            case=ex.case,
            number=ex.number,
            prompt=ex.prompt,
            answer=ex.answer,
            lesson=ex.lesson,
            variant=variant,
        )
        for ex in exercises
    ]


async def resolve_latin_conjugation_exercises(
    info: strawberry.Info,
    count: int = 10,
    max_lesson: int = 2,
    variant: LatinVariant = LatinVariant.CLASSICAL,
) -> list[LatinConjugationExercise]:
    exercises = latin_conjugation.generate_exercises(
        max_lesson=max_lesson, count=count, variant=variant.value,
    )
    return [
        LatinConjugationExercise(
            id=ex.id,
            dict_form=ex.dict_form,
            definition=ex.definition,
            person=ex.person,
            number=ex.number,
            prompt=ex.prompt,
            answer=ex.answer,
            lesson=ex.lesson,
            variant=variant,
        )
        for ex in exercises
    ]


async def mutate_grade_latin_declension_exercise(
    info: strawberry.Info,
    input: GradeLatinExerciseInput,
) -> LatinGradeResult:
    correct, feedback = latin_declension.grade_exercise(
        submitted=input.submitted,
        expected=input.expected,
    )
    return LatinGradeResult(
        correct=correct,
        expected=input.expected,
        submitted=input.submitted,
        feedback=feedback,
    )


async def mutate_grade_latin_conjugation_exercise(
    info: strawberry.Info,
    input: GradeLatinExerciseInput,
) -> LatinGradeResult:
    correct, feedback = latin_conjugation.grade_exercise(
        submitted=input.submitted,
        expected=input.expected,
    )
    return LatinGradeResult(
        correct=correct,
        expected=input.expected,
        submitted=input.submitted,
        feedback=feedback,
    )


# ── Greek exercise resolvers ──────────────────────────────────────────────────

async def resolve_greek_declension_exercises(
    info: strawberry.Info,
    count: int = 10,
    max_lesson: int = 2,
    variant: GreekVariant = GreekVariant.ANCIENT,
) -> list[GreekDeclensionExercise]:
    exercises = greek_declension.generate_exercises(
        max_lesson=max_lesson, count=count, variant=variant.value
    )
    return [
        GreekDeclensionExercise(
            id=ex.id,
            dict_form=ex.dict_form,
            definition=ex.definition,
            case=ex.case,
            number=ex.number,
            prompt=ex.prompt,
            answer=ex.answer,
            lesson=ex.lesson,
            variant=variant,
        )
        for ex in exercises
    ]


async def resolve_greek_conjugation_exercises(
    info: strawberry.Info,
    count: int = 10,
    max_lesson: int = 2,
    variant: GreekVariant = GreekVariant.ANCIENT,
) -> list[GreekConjugationExercise]:
    exercises = greek_conjugation.generate_exercises(
        max_lesson=max_lesson, count=count, variant=variant.value
    )
    return [
        GreekConjugationExercise(
            id=ex.id,
            dict_form=ex.dict_form,
            definition=ex.definition,
            person=ex.person,
            number=ex.number,
            prompt=ex.prompt,
            answer=ex.answer,
            lesson=ex.lesson,
            variant=variant,
        )
        for ex in exercises
    ]


async def mutate_grade_greek_exercise(
    info: strawberry.Info,
    input: GradeGreekExerciseInput,
) -> GreekGradeResult:
    correct, feedback = greek_declension.grade_exercise(
        submitted=input.submitted,
        expected=input.expected,
    )
    return GreekGradeResult(
        correct=correct,
        expected=input.expected,
        submitted=input.submitted,
        feedback=feedback,
    )


# ── Sanskrit exercise resolvers ───────────────────────────────────────────────

async def resolve_sanskrit_declension_exercises(
    info: strawberry.Info,
    count: int = 10,
    max_lesson: int = 2,
) -> list[SanskritDeclensionExercise]:
    exercises = sanskrit_declension.generate_exercises(max_lesson=max_lesson, count=count)
    return [
        SanskritDeclensionExercise(
            id=ex.id,
            dict_form=ex.dict_form,
            devanagari=ex.devanagari,
            definition=ex.definition,
            case=ex.case,
            number=ex.number,
            prompt=ex.prompt,
            answer=ex.answer,
            lesson=ex.lesson,
        )
        for ex in exercises
    ]


async def mutate_grade_sanskrit_exercise(
    info: strawberry.Info,
    input: GradeSanskritExerciseInput,
) -> SanskritGradeResult:
    correct, feedback = sanskrit_declension.grade_exercise(
        submitted=input.submitted,
        expected=input.expected,
    )
    return SanskritGradeResult(
        correct=correct,
        expected=input.expected,
        submitted=input.submitted,
        feedback=feedback,
    )


def _tahot_word_to_gql(w: tahot_svc.TahotWord) -> TahotWordGQL:
    return TahotWordGQL(
        ref=w.ref,
        book=w.book,
        chapter=w.chapter,
        verse=w.verse,
        token=w.token,
        text_type=w.text_type,
        hebrew=w.hebrew,
        transliteration=w.transliteration,
        translation=w.translation,
        dstrongs=w.dstrongs,
        grammar=w.grammar,
        root_strongs=w.root_strongs,
        expanded=w.expanded,
    )


def resolve_tahot_books() -> list[TahotBookInfo]:
    return [TahotBookInfo(**b) for b in tahot_svc.get_books()]


def resolve_tahot_chapter_verses(book: str) -> list[TahotChapterInfo]:
    counts = tahot_svc.get_chapter_verse_counts(book)
    return [
        TahotChapterInfo(chapter=ch, verse_count=vc)
        for ch, vc in sorted(counts.items())
    ]


def resolve_tahot_verse(book: str, chapter: int, verse: int) -> list[TahotWordGQL]:
    words = tahot_svc.get_verse(book, chapter, verse)
    return [_tahot_word_to_gql(w) for w in words]


def resolve_tahot_chapter(book: str, chapter: int) -> list[TahotWordGQL]:
    verses = tahot_svc.get_chapter(book, chapter)
    words = []
    for v in sorted(verses.keys()):
        for w in verses[v]:
            words.append(_tahot_word_to_gql(w))
    return words


def resolve_tahot_search(query: str, limit: int = 50) -> list[TahotWordGQL]:
    words = tahot_svc.search_words(query, limit)
    return [_tahot_word_to_gql(w) for w in words]


# ── Generic interlinear resolvers ─────────────────────────────────────────────

_EXPANDED_RE = re.compile(r'\{([^={}]+)=([^={}]+)=([^}]+)\}')


def _parse_expanded(expanded: str) -> tuple[str, str, str]:
    """Extract (lemma_id, lemma, definition) from an expanded Strong's tag.

    The expanded column contains entries like '{H7225G=רֵאשִׁית=beginning}'.
    We return the first root match (curly-braced entry with three parts).
    """
    m = _EXPANDED_RE.search(expanded)
    if m:
        return m.group(1), m.group(2), m.group(3)
    return "", "", ""


def _tahot_word_to_interlinear(w: tahot_svc.TahotWord) -> InterlinearWord:
    lemma_id, lemma, lemma_def = _parse_expanded(w.expanded)
    return InterlinearWord(
        ref=w.ref,
        position=w.token,
        text_type=w.text_type,
        native=w.hebrew,
        transliteration=w.transliteration,
        gloss=w.translation,
        morphology=w.grammar,
        lemma_id=lemma_id or w.root_strongs,
        lemma=lemma,
        lemma_definition=lemma_def,
    )


def resolve_interlinear_passage(
    source: str,
    book: str,
    start_chapter: int,
    start_verse: int,
    end_chapter: int | None,
    end_verse: int | None,
) -> list[InterlinearVerse]:
    """Return an interlinear passage for a range of verses.

    Currently supports source="TAHOT" (Hebrew OT).  Additional corpora can be
    wired up here as they are added.

    If end_chapter/end_verse are omitted the range extends to the end of
    start_chapter.
    """
    source_upper = source.upper()

    if source_upper == "TAHOT":
        if end_chapter is None:
            end_chapter = start_chapter
        if end_verse is None:
            counts = tahot_svc.get_chapter_verse_counts(book)
            end_verse = counts.get(end_chapter, start_verse)

        verse_map = tahot_svc.get_range(book, start_chapter, start_verse, end_chapter, end_verse)
        return [
            InterlinearVerse(
                book=book,
                chapter=ch,
                verse=v,
                words=[_tahot_word_to_interlinear(w) for w in words],
            )
            for (ch, v), words in sorted(verse_map.items())
        ]

    return []


def _db_user_to_gql(db_user: models.User) -> User:
    return User(
        id=db_user.id,
        email=db_user.email,
        username=db_user.username,
        display_name=db_user.display_name,
        created_at=db_user.created_at,
    )


async def resolve_me(info: strawberry.Info) -> User | None:
    user_id = info.context.get("current_user_id")
    if user_id is None:
        return None
    session: AsyncSession = info.context["db"]
    result = await session.execute(select(models.User).where(models.User.id == user_id))
    db_user = result.scalar_one_or_none()
    return _db_user_to_gql(db_user) if db_user else None


async def mutate_login(info: strawberry.Info, input: LoginInput) -> AuthPayload | None:
    session: AsyncSession = info.context["db"]
    result = await session.execute(
        select(models.User).where(models.User.username == input.username)
    )
    db_user = result.scalar_one_or_none()
    if db_user is None or not verify_password(input.password, db_user.password_hash):
        return None
    token = create_access_token(db_user.id)
    return AuthPayload(token=token, user=_db_user_to_gql(db_user))


# ── Vulgate interlinear resolvers ─────────────────────────────────────────────

def _vulgate_token_to_gql(t: vulgate_svc.VulgateToken) -> VulgateTokenGQL:
    return VulgateTokenGQL(
        ref=t.ref,
        book=t.book,
        chapter=t.chapter,
        verse=t.verse,
        token=t.token,
        form=t.form,
        lemma=t.lemma,
        pos=t.pos,
        morphology=t.morphology,
        relation=t.relation,
    )


def resolve_vulgate_books() -> list[VulgateBookInfo]:
    return [
        VulgateBookInfo(abbrev=b["abbrev"], name=b["name"], chapters=b["chapters"])
        for b in vulgate_svc.get_books()
    ]


def resolve_vulgate_chapter_verses(book: str) -> list[VulgateChapterInfo]:
    counts = vulgate_svc.get_chapter_verse_counts(book)
    return [
        VulgateChapterInfo(chapter=ch, verse_count=vc)
        for ch, vc in sorted(counts.items())
    ]


def resolve_vulgate_verse(book: str, chapter: int, verse: int) -> list[VulgateTokenGQL]:
    tokens = vulgate_svc.get_verse(book, chapter, verse)
    return [_vulgate_token_to_gql(t) for t in tokens]


def resolve_vulgate_chapter(book: str, chapter: int) -> list[VulgateTokenGQL]:
    verses = vulgate_svc.get_chapter(book, chapter)
    tokens = []
    for v in sorted(verses.keys()):
        for t in verses[v]:
            tokens.append(_vulgate_token_to_gql(t))
    return tokens


def resolve_vulgate_search(query: str, limit: int = 50) -> list[VulgateTokenGQL]:
    tokens = vulgate_svc.search(query, limit)
    return [_vulgate_token_to_gql(t) for t in tokens]


def resolve_tahot_chapter_translations(book: str, chapter: int) -> list[TahotVerseTranslation]:
    verses = jps_svc.get_chapter(book, chapter)
    return [TahotVerseTranslation(verse=v, text=text) for v, text in sorted(verses.items())]


def resolve_vulgate_chapter_translations(book: str, chapter: int) -> list[VulgateVerseTranslation]:
    verses = drc_svc.get_chapter(book, chapter)
    return [VulgateVerseTranslation(verse=v, text=text) for v, text in sorted(verses.items())]


# ── GNT interlinear resolvers ─────────────────────────────────────────────────

def _greek_word_to_gql_gnt(w: gnt_svc.GNTWord) -> GreekTokenGQL:
    return GreekTokenGQL(
        ref=w.ref, book=w.book, chapter=w.chapter, verse=w.verse,
        token=w.token, text_type=w.text_type, greek=w.greek,
        transliteration=w.transliteration, translation=w.translation,
        dstrongs=w.dstrongs, grammar=w.grammar, expanded=w.expanded,
    )


def resolve_gnt_books() -> list[GreekBookInfo]:
    return [
        GreekBookInfo(abbrev=b["abbrev"], name=b["name"], chapters=b["chapters"])
        for b in gnt_svc.get_books()
    ]


def resolve_gnt_chapter_verses(book: str) -> list[GreekChapterInfo]:
    counts = gnt_svc.get_chapter_verse_counts(book)
    return [GreekChapterInfo(chapter=ch, verse_count=vc) for ch, vc in sorted(counts.items())]


def resolve_gnt_verse(book: str, chapter: int, verse: int) -> list[GreekTokenGQL]:
    return [_greek_word_to_gql_gnt(w) for w in gnt_svc.get_verse(book, chapter, verse)]


def resolve_gnt_chapter(book: str, chapter: int) -> list[GreekTokenGQL]:
    verses = gnt_svc.get_chapter(book, chapter)
    tokens = []
    for v in sorted(verses.keys()):
        for w in verses[v]:
            tokens.append(_greek_word_to_gql_gnt(w))
    return tokens


def resolve_gnt_search(query: str, limit: int = 50) -> list[GreekTokenGQL]:
    return [_greek_word_to_gql_gnt(w) for w in gnt_svc.search(query, limit)]


def resolve_gnt_chapter_translations(book: str, chapter: int) -> list[GreekVerseTranslation]:
    verses = kjv_svc.get_chapter(book, chapter)
    return [GreekVerseTranslation(verse=v, text=text) for v, text in sorted(verses.items())]


# ── LXX interlinear resolvers ─────────────────────────────────────────────────

def _greek_word_to_gql_lxx(w: lxx_svc.LXXWord) -> GreekTokenGQL:
    return GreekTokenGQL(
        ref=w.ref, book=w.book, chapter=w.chapter, verse=w.verse,
        token=w.token, text_type=w.text_type, greek=w.greek,
        transliteration=w.transliteration, translation=w.translation,
        dstrongs=w.dstrongs, grammar=w.grammar, expanded=w.expanded,
    )


def resolve_lxx_books() -> list[GreekBookInfo]:
    return [
        GreekBookInfo(abbrev=b["abbrev"], name=b["name"], chapters=b["chapters"])
        for b in lxx_svc.get_books()
    ]


def resolve_lxx_chapter_verses(book: str) -> list[GreekChapterInfo]:
    counts = lxx_svc.get_chapter_verse_counts(book)
    return [GreekChapterInfo(chapter=ch, verse_count=vc) for ch, vc in sorted(counts.items())]


def resolve_lxx_verse(book: str, chapter: int, verse: int) -> list[GreekTokenGQL]:
    return [_greek_word_to_gql_lxx(w) for w in lxx_svc.get_verse(book, chapter, verse)]


def resolve_lxx_chapter(book: str, chapter: int) -> list[GreekTokenGQL]:
    verses = lxx_svc.get_chapter(book, chapter)
    tokens = []
    for v in sorted(verses.keys()):
        for w in verses[v]:
            tokens.append(_greek_word_to_gql_lxx(w))
    return tokens


def resolve_lxx_search(query: str, limit: int = 50) -> list[GreekTokenGQL]:
    return [_greek_word_to_gql_lxx(w) for w in lxx_svc.search(query, limit)]


def resolve_lxx_chapter_translations(book: str, chapter: int) -> list[GreekVerseTranslation]:
    verses = brenton_svc.get_chapter(book, chapter)
    return [GreekVerseTranslation(verse=v, text=text) for v, text in sorted(verses.items())]


# ── TBESH / TBESG lexicon ──────────────────────────────────────────────────────

def resolve_strongs_entry(strongs_id: str) -> StrongsEntryGQL | None:
    entry = tbesh_svc.get_entry(strongs_id)
    if not entry:
        return None
    return StrongsEntryGQL(
        strongs_id=entry.strongs_id,
        e_strongs_id=entry.e_strongs_id,
        native=entry.native,
        transliteration=entry.transliteration,
        morph=entry.morph,
        gloss=entry.gloss,
        meaning=entry.meaning,
    )


# ── Verb paradigm ────────────────────────────────────────────────────────────


async def resolve_qal_paradigm(
    info: strawberry.Info,
    root: str | None = None,
    binyan: str = "qal",
) -> QalParadigmGQL | None:
    paradigm = verb_paradigm.get_paradigm(binyan, root)
    if paradigm is None:
        return None
    return QalParadigmGQL(
        binyan=paradigm.binyan,
        binyan_display=paradigm.binyan_display,
        root=paradigm.root,
        root_transliteration=paradigm.root_transliteration,
        citation=paradigm.citation,
        citation_transliteration=paradigm.citation_transliteration,
        definition=paradigm.definition,
        available_roots=verb_paradigm.available_roots(binyan),
        available_binyanim=verb_paradigm.available_binyanim(),
        forms=[
            QalParadigmFormGQL(
                conjugation=f.conjugation,
                person=f.person,
                number=f.number,
                gender=f.gender,
                label=f.label,
                hebrew=f.hebrew,
                transliteration=f.transliteration,
            )
            for f in paradigm.forms
        ],
    )


async def resolve_qal_worksheet(
    info: strawberry.Info,
    num_blanks: int = 10,
    root: str | None = None,
    conjugations: list[str] | None = None,
    binyan: str = "qal",
) -> QalWorksheetGQL | None:
    worksheet = verb_paradigm.generate_worksheet(
        binyan, root, num_blanks, conjugations,
    )
    if worksheet is None:
        return None
    return QalWorksheetGQL(
        binyan=worksheet.binyan,
        binyan_display=worksheet.binyan_display,
        root=worksheet.root,
        root_transliteration=worksheet.root_transliteration,
        citation=worksheet.citation,
        citation_transliteration=worksheet.citation_transliteration,
        definition=worksheet.definition,
        num_blanks=worksheet.num_blanks,
        forms=[
            QalWorksheetFormGQL(
                conjugation=f.conjugation,
                person=f.person,
                number=f.number,
                gender=f.gender,
                label=f.label,
                hebrew=f.hebrew,
                transliteration=f.transliteration,
                answer_hebrew=f.answer_hebrew,
                answer_transliteration=f.answer_transliteration,
                is_blank=f.is_blank,
            )
            for f in worksheet.forms
        ],
    )


async def mutate_grade_qal_worksheet(
    info: strawberry.Info,
    input: GradeQalWorksheetInput,
) -> QalWorksheetGradeResult:
    binyan = input.binyan or "qal"
    full_ws = verb_paradigm.generate_worksheet(
        binyan, input.root, num_blanks=0,
    )
    if full_ws is None:
        return QalWorksheetGradeResult(total=0, correct_count=0, items=[])

    answers = [(a.index, a.submitted) for a in input.answers]
    results = verb_paradigm.grade_worksheet(answers, full_ws)

    items = [
        QalWorksheetGradeItem(
            index=r.index,
            label=r.label,
            correct=r.correct,
            expected=r.expected,
            submitted=r.submitted,
            feedback=r.feedback,
        )
        for r in results
    ]
    correct_count = sum(1 for r in results if r.correct)
    return QalWorksheetGradeResult(
        total=len(results),
        correct_count=correct_count,
        items=items,
    )
