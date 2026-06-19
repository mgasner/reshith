"""GraphQL resolvers."""

import json
import re
from datetime import UTC, datetime
from pathlib import Path
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
    DeckSRSConfigType,
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
    GreekExerciseKind,
    GreekGradeResult,
    GreekVariant,
    GreekVerseTranslation,
    ImportLessonInput,
    InterlinearVerse,
    InterlinearWord,
    LanguageCode,
    LatinConjugationExercise,
    LatinDeclensionExercise,
    LatinGradeResult,
    LatinVariant,
    LessonCard,
    LessonProgressInfo,
    LexiconEntry,
    LoginInput,
    PrepositionExercise,
    PrepositionType,
    QalWorksheetGradeItem,
    QalWorksheetGradeResult,
    RegisterInput,
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
    SRSConfigType,
    SRSState,
    TahotBookInfo,
    TahotChapterInfo,
    TahotVerseTranslation,
    TranslationExercise,
    TranslationGradeResult,
    TranslationHelp,
    TranslationPattern,
    UpdateDeckSRSSettingsInput,
    UpdateUserSRSSettingsInput,
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
from reshith.services import (
    exercise_attempts as attempt_svc,
)
from reshith.services import gnt as gnt_svc
from reshith.services import jps as jps_svc
from reshith.services import kjv as kjv_svc
from reshith.services import (
    lesson_progress as lesson_progress_svc,
)
from reshith.services import (
    llm,
    primary_deck,
    srs,
    tts,
    vocab_catalog,
    vocab_sampling,
)
from reshith.services import lxx as lxx_svc
from reshith.services import tahot as tahot_svc
from reshith.services import tbesh as tbesh_svc
from reshith.services import vulgate as vulgate_svc
from reshith.services.auth import create_access_token, hash_password, verify_password


def db_language_to_gql(db_lang: models.LanguageCode) -> LanguageCode:
    return LanguageCode(db_lang.value)


def gql_language_to_db(gql_lang: LanguageCode) -> models.LanguageCode:
    return models.LanguageCode(gql_lang.value)


def _require_user_id(info: strawberry.Info) -> UUID:
    user_id = info.context.get("current_user_id")
    if user_id is None:
        raise Exception("Not authenticated")
    return user_id


def _maybe_user_id(info: strawberry.Info) -> UUID | None:
    """Return the current user id or ``None`` if the request is anonymous.

    Used by exercise queries and grading mutations that remain accessible
    anonymously but become progress-aware when authenticated.
    """
    return info.context.get("current_user_id")


async def _resolve_max_lesson(
    session: AsyncSession,
    user_id: UUID | None,
    language: "models.LanguageCode",
    fallback: int,
) -> int:
    """Resolve the effective max-lesson for an exercise query.

    Anonymous users get the per-page selector value directly. Authenticated
    users get the *higher* of ``fallback`` (per-page selector, defaults to
    the page's hardcoded constant) and ``current_lesson`` — that way a
    user-driven selector still has visible effect (it can broaden scope
    beyond the current lesson) but a stale page default cannot accidentally
    drop their pool below where they've progressed to.
    """
    if user_id is None:
        return fallback
    current = await lesson_progress_svc.get_current_lesson(session, user_id, language)
    return max(current, fallback)


async def _require_owned_deck(
    session: AsyncSession, deck_id: UUID, user_id: UUID
) -> models.Deck:
    result = await session.execute(
        select(models.Deck).where(
            models.Deck.id == deck_id, models.Deck.owner_id == user_id
        )
    )
    deck = result.scalar_one_or_none()
    if deck is None:
        raise Exception("Deck not found")
    return deck


async def resolve_decks(
    info: strawberry.Info,
    language: LanguageCode | None = None,
) -> list[Deck]:
    session: AsyncSession = info.context["db"]
    user_id = _require_user_id(info)

    query = select(models.Deck).where(models.Deck.owner_id == user_id)
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
                is_primary=deck.is_primary,
                created_at=deck.created_at,
                updated_at=deck.updated_at,
                card_count=card_count,
            )
        )

    return deck_list


async def resolve_deck(info: strawberry.Info, id: UUID) -> Deck | None:
    session: AsyncSession = info.context["db"]
    user_id = _require_user_id(info)

    result = await session.execute(
        select(models.Deck).where(models.Deck.id == id, models.Deck.owner_id == user_id)
    )
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
        is_primary=deck.is_primary,
        created_at=deck.created_at,
        updated_at=deck.updated_at,
        card_count=card_count,
    )


async def resolve_cards(info: strawberry.Info, deck_id: UUID) -> list[Card]:
    session: AsyncSession = info.context["db"]
    user_id = _require_user_id(info)
    await _require_owned_deck(session, deck_id, user_id)

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
    deck_id: UUID | None = None,
    limit: int = 20,
) -> list[CardWithSRS]:
    """Return cards due for review for the authenticated user.

    New cards (no SRS row yet) come first, capped by ``new_cards_per_day``;
    review cards (SRS row whose ``next_review`` has passed) follow, capped by
    ``reviews_per_day`` minus the number already reviewed since midnight UTC.
    Both caps are read from the effective :class:`SRSConfig` for the deck
    (defaults when ``deck_id`` is omitted).
    """
    session: AsyncSession = info.context["db"]
    user_id = _require_user_id(info)
    if deck_id:
        await _require_owned_deck(session, deck_id, user_id)

    config = await _effective_srs_config(session, user_id, deck_id)

    now = datetime.now(UTC)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Count today's reviews so daily caps wind down as the user studies.
    reviewed_today_query = (
        select(func.count())
        .select_from(models.Review)
        .where(
            models.Review.user_id == user_id,
            models.Review.reviewed_at >= midnight,
        )
    )
    if deck_id:
        reviewed_today_query = reviewed_today_query.join(
            models.Card, models.Card.id == models.Review.card_id
        ).where(models.Card.deck_id == deck_id)
    reviewed_today = (await session.execute(reviewed_today_query)).scalar() or 0
    reviews_remaining = max(0, config.reviews_per_day - reviewed_today)

    # New cards: cards owned by this user with no SRS row yet.
    new_cards_query = (
        select(models.Card)
        .join(models.Deck, models.Card.deck_id == models.Deck.id)
        .outerjoin(
            models.SRSState,
            (models.SRSState.card_id == models.Card.id)
            & (models.SRSState.user_id == user_id),
        )
        .where(models.Deck.owner_id == user_id)
        .where(models.SRSState.id.is_(None))
        .order_by(models.Card.created_at.asc())
    )
    if deck_id:
        new_cards_query = new_cards_query.where(models.Card.deck_id == deck_id)
    new_card_limit = min(limit, config.new_cards_per_day)
    new_cards_query = new_cards_query.limit(new_card_limit)
    new_cards = (await session.execute(new_cards_query)).scalars().all()

    review_slots = max(0, limit - len(new_cards))
    review_limit = min(review_slots, reviews_remaining)
    review_rows: list[tuple] = []
    if review_limit > 0:
        review_query = (
            select(models.Card, models.SRSState)
            .join(models.Deck, models.Card.deck_id == models.Deck.id)
            .join(models.SRSState, models.SRSState.card_id == models.Card.id)
            .where(models.Deck.owner_id == user_id)
            .where(models.SRSState.user_id == user_id)
            .where(models.SRSState.next_review <= now)
            .order_by(models.SRSState.next_review.asc())
            .limit(review_limit)
        )
        if deck_id:
            review_query = review_query.where(models.Card.deck_id == deck_id)
        review_rows = (await session.execute(review_query)).all()

    def _card_gql(card: models.Card, srs_state: models.SRSState | None) -> CardWithSRS:
        return CardWithSRS(
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

    return [_card_gql(c, None) for c in new_cards] + [
        _card_gql(card, srs_state) for card, srs_state in review_rows
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
    user_id = _require_user_id(info)

    deck = models.Deck(
        name=input.name,
        description=input.description,
        language=gql_language_to_db(input.language),
        owner_id=user_id,
    )
    session.add(deck)
    await session.flush()

    # If this is the user's first deck in this language, mark it primary so
    # there's never a "no primary deck" state for users who have any deck here.
    existing_count = await session.execute(
        select(func.count()).where(
            models.Deck.owner_id == user_id,
            models.Deck.language == deck.language,
            models.Deck.id != deck.id,
        )
    )
    if (existing_count.scalar() or 0) == 0:
        deck.is_primary = True
        await session.flush()

    return Deck(
        id=deck.id,
        name=deck.name,
        description=deck.description,
        language=db_language_to_gql(deck.language),
        is_primary=deck.is_primary,
        created_at=deck.created_at,
        updated_at=deck.updated_at,
        card_count=0,
    )


async def resolve_primary_deck(
    info: strawberry.Info, language: LanguageCode
) -> Deck | None:
    session: AsyncSession = info.context["db"]
    user_id = _require_user_id(info)

    result = await session.execute(
        select(models.Deck).where(
            models.Deck.owner_id == user_id,
            models.Deck.language == gql_language_to_db(language),
            models.Deck.is_primary.is_(True),
        )
    )
    deck = result.scalar_one_or_none()
    if deck is None:
        return None

    count_query = select(func.count()).where(models.Card.deck_id == deck.id)
    count_result = await session.execute(count_query)
    card_count = count_result.scalar() or 0

    return Deck(
        id=deck.id,
        name=deck.name,
        description=deck.description,
        language=db_language_to_gql(deck.language),
        is_primary=deck.is_primary,
        created_at=deck.created_at,
        updated_at=deck.updated_at,
        card_count=card_count,
    )


async def mutate_set_primary_deck(info: strawberry.Info, deck_id: UUID) -> Deck:
    session: AsyncSession = info.context["db"]
    user_id = _require_user_id(info)
    deck = await _require_owned_deck(session, deck_id, user_id)

    # Clear primary on any other deck the user owns in the same language so the
    # partial unique index is honoured.
    other = await session.execute(
        select(models.Deck).where(
            models.Deck.owner_id == user_id,
            models.Deck.language == deck.language,
            models.Deck.id != deck.id,
            models.Deck.is_primary.is_(True),
        )
    )
    for other_deck in other.scalars().all():
        other_deck.is_primary = False
    await session.flush()

    deck.is_primary = True
    await session.flush()

    count_query = select(func.count()).where(models.Card.deck_id == deck.id)
    count_result = await session.execute(count_query)
    card_count = count_result.scalar() or 0

    return Deck(
        id=deck.id,
        name=deck.name,
        description=deck.description,
        language=db_language_to_gql(deck.language),
        is_primary=deck.is_primary,
        created_at=deck.created_at,
        updated_at=deck.updated_at,
        card_count=card_count,
    )


async def mutate_create_card(info: strawberry.Info, input: CreateCardInput) -> Card:
    session: AsyncSession = info.context["db"]
    user_id = _require_user_id(info)
    await _require_owned_deck(session, input.deck_id, user_id)

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
    user_id = _require_user_id(info)

    if input.card_id is None:
        # Lesson-page flow: identify the card via (language, lemma) and
        # lazily provision it in the user's primary deck. Returns a fully
        # populated `Card` instance so the per-deck SRS config below can
        # look up overrides via card.deck_id.
        if input.language is None or not input.vocab_lemma:
            raise Exception("Either card_id or (language + vocab_lemma) is required")
        db_lang = gql_language_to_db(input.language)
        deck = await primary_deck.get_or_create_primary_deck(session, user_id, db_lang)
        cards_by_id = await primary_deck.ensure_cards_for_vocab(
            session,
            deck,
            [primary_deck.VocabSeed(lemma=input.vocab_lemma, definition="")],
        )
        # ensure_cards_for_vocab returns id→Card for all freshly upserted
        # rows; grab the single result.
        card = next(iter(cards_by_id.values()))
    else:
        # Legacy explicit-card flow: verify ownership and load the row.
        owner_check = await session.execute(
            select(models.Card)
            .join(models.Deck, models.Card.deck_id == models.Deck.id)
            .where(models.Card.id == input.card_id, models.Deck.owner_id == user_id)
        )
        card = owner_check.scalar_one_or_none()
        if card is None:
            raise Exception("Card not found")

    card_id = card.id
    config = await _effective_srs_config(session, user_id, card.deck_id)

    result = await session.execute(
        select(models.SRSState).where(
            models.SRSState.card_id == card_id,
            models.SRSState.user_id == user_id,
        )
    )
    srs_state = result.scalar_one_or_none()

    if srs_state:
        update = srs.calculate_sm2(
            quality=input.quality,
            easiness_factor=srs_state.easiness_factor,
            interval_days=srs_state.interval_days,
            repetitions=srs_state.repetitions,
            config=config,
        )
        srs_state.easiness_factor = update.easiness_factor
        srs_state.interval_days = update.interval_days
        srs_state.repetitions = update.repetitions
        srs_state.next_review = update.next_review
    else:
        update = srs.calculate_sm2(
            quality=input.quality,
            easiness_factor=config.initial_ef,
            interval_days=0,
            repetitions=0,
            config=config,
        )
        srs_state = models.SRSState(
            card_id=card_id,
            user_id=user_id,
            easiness_factor=update.easiness_factor,
            interval_days=update.interval_days,
            repetitions=update.repetitions,
            next_review=update.next_review,
        )
        session.add(srs_state)

    review = models.Review(
        user_id=user_id,
        card_id=card_id,
        quality=input.quality,
    )
    session.add(review)
    await session.flush()

    return ReviewResult(
        card_id=card_id,
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

    session: AsyncSession = info.context["db"]
    user_id = _maybe_user_id(info)
    db_lang = models.LanguageCode.BIBLICAL_HEBREW
    effective_max = await _resolve_max_lesson(session, user_id, db_lang, max_lesson)

    pool = prep_exercises.load_nouns_up_to_lesson(effective_max)
    if not pool:
        return []
    # SRS-weighted sample (uniform for anon) — oversample so the generator
    # has room to vary preposition x noun combinations.
    nouns = await vocab_sampling.sample_vocab(
        session, user_id, db_lang.value, pool,
        id_fn=lambda n: n.hebrew, k=min(len(pool), count * 3),
    )

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
    session: AsyncSession = info.context["db"]
    user_id = _maybe_user_id(info)

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

        await attempt_svc.record_attempt(
            session, user_id,
            language=models.LanguageCode.BIBLICAL_HEBREW,
            exercise_type="preposition",
            correct=correct,
            vocab_lemma=input.vocab_lemma,
        )
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

        await attempt_svc.record_attempt(
            session, user_id,
            language=models.LanguageCode.BIBLICAL_HEBREW,
            exercise_type="preposition",
            correct=correct,
            vocab_lemma=input.vocab_lemma,
        )
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
    session: AsyncSession = info.context["db"]
    user_id = _maybe_user_id(info)
    db_lang = models.LanguageCode.BIBLICAL_HEBREW
    effective_max = await _resolve_max_lesson(session, user_id, db_lang, max_lesson)
    phrases = article_exercises.generate_article_exercises(
        max_lesson=effective_max,
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
    session: AsyncSession = info.context["db"]
    user_id = _maybe_user_id(info)
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

    await attempt_svc.record_attempt(
        session, user_id,
        language=models.LanguageCode.BIBLICAL_HEBREW,
        exercise_type="article",
        correct=correct,
        vocab_lemma=input.vocab_lemma,
    )
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

    session: AsyncSession = info.context["db"]
    user_id = _maybe_user_id(info)
    db_lang = models.LanguageCode.BIBLICAL_HEBREW
    effective_max = await _resolve_max_lesson(session, user_id, db_lang, max_lesson)

    pattern_strs = None
    if patterns:
        pattern_strs = [sentence_pattern_to_str(p) for p in patterns]

    exercises = await sentence_exercises.generate_sentence_exercises(
        max_lesson=effective_max,
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

    session: AsyncSession = info.context["db"]
    user_id = _maybe_user_id(info)
    db_lang = models.LanguageCode.BIBLICAL_HEBREW
    effective_max = await _resolve_max_lesson(session, user_id, db_lang, max_lesson)

    pattern_strs = None
    if patterns:
        pattern_strs = [translation_pattern_to_str(p) for p in patterns]

    exercises = await translation_exercises.generate_translation_exercises(
        max_lesson=effective_max,
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
    session: AsyncSession = info.context["db"]
    user_id = _maybe_user_id(info)
    result = translation_exercises.grade_translation(
        submitted=input.submitted,
        expected_hebrew=input.expected_hebrew,
        expected_transliteration=input.expected_transliteration,
    )
    await attempt_svc.record_attempt(
        session, user_id,
        language=models.LanguageCode.BIBLICAL_HEBREW,
        exercise_type="translation",
        pattern=input.pattern,
        correct=result.correct,
        score=result.score,
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

    session: AsyncSession = info.context["db"]
    user_id = _maybe_user_id(info)
    db_lang = models.LanguageCode.BIBLICAL_HEBREW
    effective_max = await _resolve_max_lesson(session, user_id, db_lang, max_lesson)

    pattern_strs = None
    if patterns:
        pattern_strs = [verbal_pattern_to_str(p) for p in patterns]

    exercises = await verbal_exercises.generate_verbal_exercises(
        max_lesson=effective_max,
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
    session: AsyncSession = info.context["db"]
    user_id = _maybe_user_id(info)
    result = verbal_exercises.grade_verbal_exercise(
        submitted=input.submitted,
        expected_english=input.expected_english,
    )
    await attempt_svc.record_attempt(
        session, user_id,
        language=models.LanguageCode.BIBLICAL_HEBREW,
        exercise_type="verbal",
        pattern=input.pattern,
        correct=result.correct,
        score=result.score,
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

    session: AsyncSession = info.context["db"]
    user_id = _maybe_user_id(info)
    db_lang = models.LanguageCode.BIBLICAL_HEBREW
    effective_max = await _resolve_max_lesson(session, user_id, db_lang, max_lesson)

    exercises = await advanced_exercises.generate_comparative_exercises(
        max_lesson=effective_max,
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
    session: AsyncSession = info.context["db"]
    user_id = _maybe_user_id(info)
    result = advanced_exercises.grade_comparative_exercise(
        submitted=input.submitted,
        expected_english=input.expected_english,
    )
    await attempt_svc.record_attempt(
        session, user_id,
        language=models.LanguageCode.BIBLICAL_HEBREW,
        exercise_type="comparative",
        pattern=input.pattern,
        correct=result.correct,
        score=result.score,
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

    session: AsyncSession = info.context["db"]
    user_id = _maybe_user_id(info)
    db_lang = models.LanguageCode.BIBLICAL_HEBREW
    effective_max = await _resolve_max_lesson(session, user_id, db_lang, max_lesson)

    exercises = await advanced_exercises.generate_relative_clause_exercises(
        max_lesson=effective_max,
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
    session: AsyncSession = info.context["db"]
    user_id = _maybe_user_id(info)
    result = advanced_exercises.grade_relative_clause_exercise(
        submitted=input.submitted,
        expected_english=input.expected_english,
    )
    await attempt_svc.record_attempt(
        session, user_id,
        language=models.LanguageCode.BIBLICAL_HEBREW,
        exercise_type="relative_clause",
        pattern=input.pattern,
        correct=result.correct,
        score=result.score,
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
    session: AsyncSession = info.context["db"]
    user_id = _maybe_user_id(info)
    db_lang = (
        models.LanguageCode.LATIN if variant == LatinVariant.CLASSICAL
        else models.LanguageCode.ECCLESIASTICAL_LATIN
    )
    effective_max = await _resolve_max_lesson(session, user_id, db_lang, max_lesson)
    exercises = latin_declension.generate_exercises(
        max_lesson=effective_max, count=count, variant=variant.value,
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
    session: AsyncSession = info.context["db"]
    user_id = _maybe_user_id(info)
    db_lang = (
        models.LanguageCode.LATIN if variant == LatinVariant.CLASSICAL
        else models.LanguageCode.ECCLESIASTICAL_LATIN
    )
    effective_max = await _resolve_max_lesson(session, user_id, db_lang, max_lesson)
    exercises = latin_conjugation.generate_exercises(
        max_lesson=effective_max, count=count, variant=variant.value,
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
    session: AsyncSession = info.context["db"]
    user_id = _maybe_user_id(info)
    correct, feedback = latin_declension.grade_exercise(
        submitted=input.submitted,
        expected=input.expected,
    )
    db_lang = (
        models.LanguageCode.ECCLESIASTICAL_LATIN
        if input.variant == LatinVariant.ECCLESIASTICAL
        else models.LanguageCode.LATIN
    )
    await attempt_svc.record_attempt(
        session, user_id,
        language=db_lang,
        exercise_type="latin_declension",
        pattern=input.pattern,
        correct=correct,
        vocab_lemma=input.vocab_lemma,
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
    session: AsyncSession = info.context["db"]
    user_id = _maybe_user_id(info)
    correct, feedback = latin_conjugation.grade_exercise(
        submitted=input.submitted,
        expected=input.expected,
    )
    db_lang = (
        models.LanguageCode.ECCLESIASTICAL_LATIN
        if input.variant == LatinVariant.ECCLESIASTICAL
        else models.LanguageCode.LATIN
    )
    await attempt_svc.record_attempt(
        session, user_id,
        language=db_lang,
        exercise_type="latin_conjugation",
        pattern=input.pattern,
        correct=correct,
        vocab_lemma=input.vocab_lemma,
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
    session: AsyncSession = info.context["db"]
    user_id = _maybe_user_id(info)
    db_lang = (
        models.LanguageCode.ANCIENT_GREEK if variant == GreekVariant.ANCIENT
        else models.LanguageCode.NT_GREEK
    )
    effective_max = await _resolve_max_lesson(session, user_id, db_lang, max_lesson)
    exercises = greek_declension.generate_exercises(
        max_lesson=effective_max, count=count, variant=variant.value
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
    session: AsyncSession = info.context["db"]
    user_id = _maybe_user_id(info)
    db_lang = (
        models.LanguageCode.ANCIENT_GREEK if variant == GreekVariant.ANCIENT
        else models.LanguageCode.NT_GREEK
    )
    effective_max = await _resolve_max_lesson(session, user_id, db_lang, max_lesson)
    exercises = greek_conjugation.generate_exercises(
        max_lesson=effective_max, count=count, variant=variant.value
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
    """Single grading mutation for both Greek declension and conjugation.

    The ``kind`` input field routes to the right grader and tags the
    attempt with the right exercise_type so that declension and
    conjugation pattern weighting stay separate.
    """
    session: AsyncSession = info.context["db"]
    user_id = _maybe_user_id(info)

    is_conj = input.kind == GreekExerciseKind.CONJUGATION
    grader = greek_conjugation.grade_exercise if is_conj else greek_declension.grade_exercise
    correct, feedback = grader(
        submitted=input.submitted,
        expected=input.expected,
    )
    db_lang = (
        models.LanguageCode.NT_GREEK if input.variant == GreekVariant.KOINE
        else models.LanguageCode.ANCIENT_GREEK
    )
    await attempt_svc.record_attempt(
        session, user_id,
        language=db_lang,
        exercise_type="greek_conjugation" if is_conj else "greek_declension",
        pattern=input.pattern,
        correct=correct,
        vocab_lemma=input.vocab_lemma,
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
    session: AsyncSession = info.context["db"]
    user_id = _maybe_user_id(info)
    db_lang = models.LanguageCode.SANSKRIT
    effective_max = await _resolve_max_lesson(session, user_id, db_lang, max_lesson)
    exercises = sanskrit_declension.generate_exercises(max_lesson=effective_max, count=count)
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
    session: AsyncSession = info.context["db"]
    user_id = _maybe_user_id(info)
    correct, feedback = sanskrit_declension.grade_exercise(
        submitted=input.submitted,
        expected=input.expected,
    )
    await attempt_svc.record_attempt(
        session, user_id,
        language=models.LanguageCode.SANSKRIT,
        exercise_type="sanskrit_declension",
        pattern=input.pattern,
        correct=correct,
        vocab_lemma=input.vocab_lemma,
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


async def mutate_register(info: strawberry.Info, input: RegisterInput) -> AuthPayload:
    session: AsyncSession = info.context["db"]

    username = input.username.strip()
    email = input.email.strip().lower()
    if not username or not email or not input.password:
        raise Exception("Username, email and password are required")
    if len(input.password) < 8:
        raise Exception("Password must be at least 8 characters")

    existing = await session.execute(
        select(models.User).where(
            (models.User.username == username) | (models.User.email == email)
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise Exception("Username or email already in use")

    db_user = models.User(
        username=username,
        email=email,
        display_name=(input.display_name or username).strip(),
        password_hash=hash_password(input.password),
    )
    session.add(db_user)
    await session.flush()
    token = create_access_token(db_user.id)
    return AuthPayload(token=token, user=_db_user_to_gql(db_user))


# ── SRS configuration helpers / resolvers ─────────────────────────────────────


def _user_settings_to_dict(row: models.UserSRSSettings | None) -> dict:
    if row is None:
        return {}
    return {name: getattr(row, name) for name in srs.CONFIG_FIELD_NAMES}


def _deck_settings_to_dict(row: models.DeckSRSSettings | None) -> dict:
    if row is None:
        return {}
    # Only include keys whose value is not None — null = inherit.
    return {
        name: getattr(row, name)
        for name in srs.CONFIG_FIELD_NAMES
        if getattr(row, name) is not None
    }


async def _get_or_create_user_settings(
    session: AsyncSession, user_id: UUID
) -> models.UserSRSSettings:
    result = await session.execute(
        select(models.UserSRSSettings).where(models.UserSRSSettings.user_id == user_id)
    )
    row = result.scalar_one_or_none()
    if row is not None:
        return row
    row = models.UserSRSSettings(user_id=user_id)
    session.add(row)
    await session.flush()
    return row


async def _get_deck_settings(
    session: AsyncSession, deck_id: UUID
) -> models.DeckSRSSettings | None:
    result = await session.execute(
        select(models.DeckSRSSettings).where(models.DeckSRSSettings.deck_id == deck_id)
    )
    return result.scalar_one_or_none()


async def _effective_srs_config(
    session: AsyncSession,
    user_id: UUID,
    deck_id: UUID | None,
) -> srs.SRSConfig:
    user_row = await _get_or_create_user_settings(session, user_id)
    deck_row = await _get_deck_settings(session, deck_id) if deck_id else None
    return srs.merge_config(_user_settings_to_dict(user_row), _deck_settings_to_dict(deck_row))


def _user_settings_to_gql(row: models.UserSRSSettings) -> SRSConfigType:
    return SRSConfigType(
        initial_ef=row.initial_ef,
        minimum_ef=row.minimum_ef,
        graduating_interval_days=row.graduating_interval_days,
        easy_interval_days=row.easy_interval_days,
        hard_multiplier=row.hard_multiplier,
        easy_bonus=row.easy_bonus,
        interval_modifier=row.interval_modifier,
        maximum_interval_days=row.maximum_interval_days,
        lapse_multiplier=row.lapse_multiplier,
        lapse_minimum_interval_days=row.lapse_minimum_interval_days,
        new_cards_per_day=row.new_cards_per_day,
        reviews_per_day=row.reviews_per_day,
    )


def _config_to_gql(config: srs.SRSConfig) -> SRSConfigType:
    return SRSConfigType(
        initial_ef=config.initial_ef,
        minimum_ef=config.minimum_ef,
        graduating_interval_days=config.graduating_interval_days,
        easy_interval_days=config.easy_interval_days,
        hard_multiplier=config.hard_multiplier,
        easy_bonus=config.easy_bonus,
        interval_modifier=config.interval_modifier,
        maximum_interval_days=config.maximum_interval_days,
        lapse_multiplier=config.lapse_multiplier,
        lapse_minimum_interval_days=config.lapse_minimum_interval_days,
        new_cards_per_day=config.new_cards_per_day,
        reviews_per_day=config.reviews_per_day,
    )


def _deck_settings_to_gql(
    deck_id: UUID, row: models.DeckSRSSettings | None
) -> DeckSRSConfigType:
    if row is None:
        return DeckSRSConfigType(
            deck_id=deck_id,
            initial_ef=None,
            minimum_ef=None,
            graduating_interval_days=None,
            easy_interval_days=None,
            hard_multiplier=None,
            easy_bonus=None,
            interval_modifier=None,
            maximum_interval_days=None,
            lapse_multiplier=None,
            lapse_minimum_interval_days=None,
            new_cards_per_day=None,
            reviews_per_day=None,
        )
    return DeckSRSConfigType(
        deck_id=deck_id,
        initial_ef=row.initial_ef,
        minimum_ef=row.minimum_ef,
        graduating_interval_days=row.graduating_interval_days,
        easy_interval_days=row.easy_interval_days,
        hard_multiplier=row.hard_multiplier,
        easy_bonus=row.easy_bonus,
        interval_modifier=row.interval_modifier,
        maximum_interval_days=row.maximum_interval_days,
        lapse_multiplier=row.lapse_multiplier,
        lapse_minimum_interval_days=row.lapse_minimum_interval_days,
        new_cards_per_day=row.new_cards_per_day,
        reviews_per_day=row.reviews_per_day,
    )


async def resolve_user_srs_settings(info: strawberry.Info) -> SRSConfigType:
    session: AsyncSession = info.context["db"]
    user_id = _require_user_id(info)
    row = await _get_or_create_user_settings(session, user_id)
    return _user_settings_to_gql(row)


async def resolve_deck_srs_settings(
    info: strawberry.Info, deck_id: UUID
) -> DeckSRSConfigType:
    session: AsyncSession = info.context["db"]
    user_id = _require_user_id(info)
    await _require_owned_deck(session, deck_id, user_id)
    row = await _get_deck_settings(session, deck_id)
    return _deck_settings_to_gql(deck_id, row)


async def resolve_effective_srs_config(
    info: strawberry.Info, deck_id: UUID | None = None
) -> SRSConfigType:
    session: AsyncSession = info.context["db"]
    user_id = _require_user_id(info)
    if deck_id:
        await _require_owned_deck(session, deck_id, user_id)
    config = await _effective_srs_config(session, user_id, deck_id)
    return _config_to_gql(config)


async def mutate_update_user_srs_settings(
    info: strawberry.Info, input: UpdateUserSRSSettingsInput
) -> SRSConfigType:
    session: AsyncSession = info.context["db"]
    user_id = _require_user_id(info)
    row = await _get_or_create_user_settings(session, user_id)
    for name in srs.CONFIG_FIELD_NAMES:
        value = getattr(input, name)
        if value is not None:
            setattr(row, name, value)
    await session.flush()
    return _user_settings_to_gql(row)


async def mutate_update_deck_srs_settings(
    info: strawberry.Info, input: UpdateDeckSRSSettingsInput
) -> DeckSRSConfigType:
    session: AsyncSession = info.context["db"]
    user_id = _require_user_id(info)
    await _require_owned_deck(session, input.deck_id, user_id)
    row = await _get_deck_settings(session, input.deck_id)
    if row is None:
        row = models.DeckSRSSettings(deck_id=input.deck_id)
        session.add(row)
    # Null fields explicitly clear an override (revert to inherit).
    for name in srs.CONFIG_FIELD_NAMES:
        setattr(row, name, getattr(input, name))
    await session.flush()
    return _deck_settings_to_gql(input.deck_id, row)


# ── Lesson import ─────────────────────────────────────────────────────────────


_LANG_TO_DIR: dict[LanguageCode, str] = {
    LanguageCode.BIBLICAL_HEBREW: "hebrew",
    LanguageCode.LATIN: "latin",
    LanguageCode.ECCLESIASTICAL_LATIN: "ecclesiastical_latin",
    LanguageCode.ANCIENT_GREEK: "greek",
    LanguageCode.NT_GREEK: "nt_greek",
    LanguageCode.SANSKRIT: "sanskrit",
}


def _resolve_lesson_path(language: LanguageCode, lesson_id: str) -> Path:
    """Locate ``data/<lang>/lesson<NN>.json`` for the given language.

    ``lesson_id`` may be ``"01"``, ``"1"``, the raw numeric string used in
    the URL, or a named deck like ``"alphabet"`` / ``"vowels"`` — we tolerate
    all forms because the different language pages use different conventions.
    """
    subdir = _LANG_TO_DIR.get(language)
    if subdir is None:
        raise ValueError(f"Unsupported language for lesson import: {language}")
    repo_root = Path(__file__).resolve().parents[3]
    data_dir = repo_root / "data" / subdir
    # Try lesson<id>, the zero-padded form, and the unpadded form in turn.
    candidates: list[str] = [lesson_id]
    if lesson_id.isdigit():
        candidates.append(lesson_id.zfill(2))
        candidates.append(str(int(lesson_id)))
    for cand in candidates:
        path = data_dir / f"lesson{cand}.json"
        if path.is_file():
            return path
    # Support non-lesson decks like alphabet.json / vowels.json.
    path = data_dir / f"{lesson_id}.json"
    if path.is_file():
        return path
    raise ValueError(
        f"Lesson file not found for {language.value} lesson '{lesson_id}' "
        f"(looked under {data_dir})"
    )


async def mutate_import_lesson(
    info: strawberry.Info, input: ImportLessonInput
) -> Deck:
    """Import a lesson JSON file into a deck for the authenticated user.

    Idempotent: re-running with the same input is a no-op for cards already
    present (matched on ``(deck_id, source_reference, front)``).
    """
    session: AsyncSession = info.context["db"]
    user_id = _require_user_id(info)

    path = _resolve_lesson_path(input.language, input.lesson_id)
    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)

    if input.lesson_id.isdigit():
        norm_id = input.lesson_id.zfill(2)
        source_reference = f"{_LANG_TO_DIR[input.language]}/lesson{norm_id}"
        default_deck_name = f"Lesson {norm_id}"
    else:
        # Non-numeric ids (alphabet, vowels, …) are referenced as-is, without the
        # "lesson" prefix so the source_reference reads naturally.
        norm_id = input.lesson_id
        source_reference = f"{_LANG_TO_DIR[input.language]}/{norm_id}"
        default_deck_name = norm_id.capitalize()
    deck_name = input.deck_name or payload.get("name") or default_deck_name
    db_lang = gql_language_to_db(input.language)

    # Find an existing deck for this user keyed by source_reference; otherwise create.
    deck_result = await session.execute(
        select(models.Deck)
        .join(models.Card, models.Card.deck_id == models.Deck.id, isouter=True)
        .where(models.Deck.owner_id == user_id)
        .where(models.Card.source_reference == source_reference)
        .limit(1)
    )
    deck = deck_result.scalar_one_or_none()
    if deck is None:
        deck = models.Deck(
            owner_id=user_id,
            name=deck_name,
            description=payload.get("description"),
            language=db_lang,
        )
        session.add(deck)
        await session.flush()

    existing_query = select(models.Card.front).where(
        (models.Card.deck_id == deck.id)
        & (models.Card.source_reference == source_reference)
    )
    existing_fronts = {
        row[0] for row in (await session.execute(existing_query)).all()
    }

    for card_payload in payload.get("cards", []):
        # Vocabulary lessons use word/hebrew (+ devanagari for Sanskrit) and
        # carry their gloss in `definition`. Alphabet/vowel decks use
        # letter/hebrewExample and store the gloss in `phoneticValue` or just
        # the letter `name`. Walk both shapes.
        front = (
            card_payload.get("devanagari")
            or card_payload.get("hebrew")
            or card_payload.get("word")
            or card_payload.get("letter")
            or card_payload.get("hebrewExample")
            or ""
        )
        if not front or front in existing_fronts:
            continue
        back = (
            card_payload.get("definition")
            or card_payload.get("phoneticValue")
            or card_payload.get("name")
            or ""
        )
        transliteration = (
            card_payload.get("transliteration")
            or card_payload.get("transcription")
            or card_payload.get("name")
        )
        card = models.Card(
            deck_id=deck.id,
            front=front,
            back=back,
            notes=card_payload.get("notes"),
            transliteration=transliteration,
            grammatical_info=card_payload.get("category"),
            source_reference=source_reference,
        )
        session.add(card)
        existing_fronts.add(front)

    await session.flush()

    count_query = select(func.count()).where(models.Card.deck_id == deck.id)
    card_count = (await session.execute(count_query)).scalar() or 0

    return Deck(
        id=deck.id,
        name=deck.name,
        description=deck.description,
        language=db_language_to_gql(deck.language),
        is_primary=deck.is_primary,
        created_at=deck.created_at,
        updated_at=deck.updated_at,
        card_count=card_count,
    )


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


# ── Lesson progress + lesson cards ───────────────────────────────────────────


def _progress_to_gql(p: lesson_progress_svc.ProgressInfo) -> LessonProgressInfo:
    return LessonProgressInfo(
        language=db_language_to_gql(p.language),
        current_lesson=p.current_lesson,
        total_lessons=p.total_lessons,
        vocab_total=p.vocab_total,
        vocab_mastered=p.vocab_mastered,
        mastery_percent=p.mastery_percent,
        due_count=p.due_count,
        is_ready_to_advance=p.is_ready_to_advance,
    )


async def resolve_lesson_progress(
    info: strawberry.Info, language: LanguageCode,
) -> LessonProgressInfo:
    session: AsyncSession = info.context["db"]
    user_id = _require_user_id(info)
    info_ = await lesson_progress_svc.get_progress(
        session, user_id, gql_language_to_db(language),
    )
    return _progress_to_gql(info_)


async def resolve_my_progress(info: strawberry.Info) -> list[LessonProgressInfo]:
    session: AsyncSession = info.context["db"]
    user_id = _require_user_id(info)
    rows = await lesson_progress_svc.get_all_progress(session, user_id)
    return [_progress_to_gql(r) for r in rows]


async def mutate_advance_lesson(
    info: strawberry.Info, language: LanguageCode,
) -> LessonProgressInfo:
    session: AsyncSession = info.context["db"]
    user_id = _require_user_id(info)
    p = await lesson_progress_svc.advance_lesson(
        session, user_id, gql_language_to_db(language),
    )
    return _progress_to_gql(p)


async def mutate_set_current_lesson(
    info: strawberry.Info, language: LanguageCode, lesson: int,
) -> LessonProgressInfo:
    session: AsyncSession = info.context["db"]
    user_id = _require_user_id(info)
    p = await lesson_progress_svc.set_current_lesson(
        session, user_id, gql_language_to_db(language), lesson,
    )
    return _progress_to_gql(p)


def resolve_lesson_cards(
    language: LanguageCode, lesson: int,
) -> list[LessonCard]:
    """Return the lesson's vocabulary with stable ``vocab_id`` for SRS."""
    db_lang = gql_language_to_db(language)
    items = vocab_catalog.load_vocab(db_lang, lesson)
    only_this = [v for v in items if v.lesson == lesson]
    from reshith.exercises.vocab_id import vocab_id as _vocab_id
    return [
        LessonCard(
            vocab_id=_vocab_id(db_lang.value, v.lemma),
            lemma=v.lemma,
            transliteration=v.transliteration,
            definition=v.definition,
            category=v.category,
            lesson=v.lesson,
            notes=v.notes,
        )
        for v in only_this
    ]
