"""GraphQL type definitions."""

import enum
from datetime import datetime
from uuid import UUID

import strawberry


@strawberry.enum
class LanguageCode(enum.Enum):
    BIBLICAL_HEBREW = "hbo"
    LATIN = "lat"
    ECCLESIASTICAL_LATIN = "ecl"
    ANCIENT_GREEK = "grc"
    NT_GREEK = "gnt"
    SANSKRIT = "san"
    PALI = "pli"
    BUDDHIST_HYBRID_SANSKRIT = "bhs"
    ARAMAIC = "arc"
    MIDRASHIC_HEBREW = "heb"


@strawberry.type
class User:
    id: UUID
    email: str
    username: str
    display_name: str
    created_at: datetime


@strawberry.type
class AuthPayload:
    token: str
    user: User


@strawberry.input
class LoginInput:
    username: str
    password: str


@strawberry.input
class RegisterInput:
    username: str
    email: str
    password: str
    display_name: str | None = None


@strawberry.type
class Deck:
    id: UUID
    name: str
    description: str | None
    language: LanguageCode
    is_primary: bool
    created_at: datetime
    updated_at: datetime
    card_count: int


@strawberry.type
class Card:
    id: UUID
    deck_id: UUID
    front: str
    back: str
    notes: str | None
    transliteration: str | None
    grammatical_info: str | None
    source_reference: str | None
    created_at: datetime
    updated_at: datetime


@strawberry.type
class SRSState:
    easiness_factor: float
    interval_days: int
    repetitions: int
    next_review: datetime


@strawberry.type
class CardWithSRS:
    card: Card
    srs: SRSState | None


@strawberry.type
class ReviewResult:
    card_id: UUID
    new_srs: SRSState


@strawberry.type
class TranslationHelp:
    translation: str
    notes: str | None


@strawberry.type
class Drill:
    text: str
    translation: str
    notes: str | None


@strawberry.type
class LexiconEntry:
    id: UUID
    language: LanguageCode
    lemma: str
    transliteration: str | None
    definition: str
    part_of_speech: str | None
    morphology: str | None
    frequency: int | None


@strawberry.input
class CreateDeckInput:
    name: str
    description: str | None = None
    language: LanguageCode


@strawberry.input
class CreateCardInput:
    deck_id: UUID
    front: str
    back: str
    notes: str | None = None
    transliteration: str | None = None
    grammatical_info: str | None = None
    source_reference: str | None = None


@strawberry.input
class ReviewInput:
    quality: int
    # Either card_id (legacy: explicit deck card) or (language, vocab_lemma)
    # for the auto-provisioned primary-deck flow used by the lesson page.
    card_id: UUID | None = None
    language: LanguageCode | None = None
    vocab_lemma: str | None = None


@strawberry.type
class LessonProgressInfo:
    language: LanguageCode
    current_lesson: int
    total_lessons: int
    vocab_total: int
    vocab_mastered: int
    mastery_percent: float
    due_count: int
    is_ready_to_advance: bool


@strawberry.type
class LessonCard:
    """A single lesson vocab card with its stable ``vocab_id``."""
    vocab_id: UUID
    lemma: str
    transliteration: str | None
    definition: str
    category: str | None
    lesson: int | None
    notes: str | None


# ── SRS configuration types ───────────────────────────────────────────────────


@strawberry.type
class SRSConfigType:
    """Effective Anki-style SRS configuration (all fields populated)."""
    initial_ef: float
    minimum_ef: float
    graduating_interval_days: int
    easy_interval_days: int
    hard_multiplier: float
    easy_bonus: float
    interval_modifier: float
    maximum_interval_days: int
    lapse_multiplier: float
    lapse_minimum_interval_days: int
    new_cards_per_day: int
    reviews_per_day: int


@strawberry.type
class DeckSRSConfigType:
    """Sparse per-deck override. Any null field means inherit from the user
    settings."""
    deck_id: UUID
    initial_ef: float | None
    minimum_ef: float | None
    graduating_interval_days: int | None
    easy_interval_days: int | None
    hard_multiplier: float | None
    easy_bonus: float | None
    interval_modifier: float | None
    maximum_interval_days: int | None
    lapse_multiplier: float | None
    lapse_minimum_interval_days: int | None
    new_cards_per_day: int | None
    reviews_per_day: int | None


@strawberry.input
class UpdateUserSRSSettingsInput:
    """Update payload for the per-user SRS settings. Any null field is left
    unchanged."""
    initial_ef: float | None = None
    minimum_ef: float | None = None
    graduating_interval_days: int | None = None
    easy_interval_days: int | None = None
    hard_multiplier: float | None = None
    easy_bonus: float | None = None
    interval_modifier: float | None = None
    maximum_interval_days: int | None = None
    lapse_multiplier: float | None = None
    lapse_minimum_interval_days: int | None = None
    new_cards_per_day: int | None = None
    reviews_per_day: int | None = None


# ── LLM API keys ──────────────────────────────────────────────────────────────


@strawberry.enum
class LLMProvider(enum.Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@strawberry.type
class UserAPIKeysType:
    """Per-user LLM credential state.

    Plaintext keys are never returned. ``openai_key_last4`` /
    ``anthropic_key_last4`` are populated when a key is configured so the UI
    can show "••••sk-1234" instead of forcing the user to re-enter to verify.
    ``preferred_provider`` is the user's explicit pick; ``None`` means the
    server default is in effect.
    """
    preferred_provider: LLMProvider | None
    has_openai_key: bool
    has_anthropic_key: bool
    openai_key_last4: str | None
    anthropic_key_last4: str | None
    # Whether the server has the encryption key configured. False means the
    # update mutation will reject writes — surface this in the UI so users
    # aren't confused by a save failure.
    encryption_configured: bool


@strawberry.input
class UpdateUserAPIKeysInput:
    """Update payload for a user's LLM credentials.

    ``openai_api_key`` / ``anthropic_api_key`` set the corresponding key when
    non-empty. Pass ``clear_openai=True`` / ``clear_anthropic=True`` to remove
    a stored key. ``preferred_provider=None`` leaves the existing preference
    unchanged; pass it explicitly to change which provider is used.
    """
    openai_api_key: str | None = None
    clear_openai: bool = False
    anthropic_api_key: str | None = None
    clear_anthropic: bool = False
    preferred_provider: LLMProvider | None = None


@strawberry.input
class UpdateDeckSRSSettingsInput:
    """Sparse update for a deck's SRS overrides. Null means "clear override",
    i.e. revert to inheriting from the user-level value."""
    deck_id: UUID
    initial_ef: float | None = None
    minimum_ef: float | None = None
    graduating_interval_days: int | None = None
    easy_interval_days: int | None = None
    hard_multiplier: float | None = None
    easy_bonus: float | None = None
    interval_modifier: float | None = None
    maximum_interval_days: int | None = None
    lapse_multiplier: float | None = None
    lapse_minimum_interval_days: int | None = None
    new_cards_per_day: int | None = None
    reviews_per_day: int | None = None


@strawberry.input
class ImportLessonInput:
    language: LanguageCode
    lesson_id: str
    deck_name: str | None = None


@strawberry.enum
class PrepositionType(enum.Enum):
    BE = "bə"
    LE = "lə"
    KE = "kə"


@strawberry.enum
class ExerciseDirection(enum.Enum):
    HEBREW_TO_ENGLISH = "hebrew_to_english"
    ENGLISH_TO_HEBREW = "english_to_hebrew"


@strawberry.type
class PrepositionExercise:
    id: str
    hebrew: str
    transliteration: str
    english: str
    preposition: PrepositionType
    noun_hebrew: str
    noun_definition: str
    direction: ExerciseDirection
    prompt: str
    answer: str
    lesson: int


@strawberry.type
class ExerciseGradeResult:
    correct: bool
    expected: str
    submitted: str
    feedback: str


@strawberry.input
class GradeExerciseInput:
    exercise_id: str
    submitted: str
    direction: ExerciseDirection
    expected_hebrew: str
    expected_english: str
    # Optional native-script lemma used to attribute the attempt to a
    # specific lesson card for SRS weighting. Anonymous users may omit.
    vocab_lemma: str | None = None


@strawberry.type
class SpeechSynthesisResult:
    available: bool
    audio_base64: str | None
    mime_type: str
    text: str
    language: str


@strawberry.enum
class ArticleDirection(enum.Enum):
    INDEFINITE_TO_DEFINITE = "indefinite_to_definite"
    DEFINITE_TO_INDEFINITE = "definite_to_indefinite"


@strawberry.type
class ArticleExercise:
    id: str
    hebrew_indefinite: str
    hebrew_definite: str
    transliteration_indefinite: str
    transliteration_definite: str
    english_indefinite: str
    english_definite: str
    article_type: str
    direction: ArticleDirection
    prompt: str
    prompt_transliteration: str
    answer: str
    answer_transliteration: str
    lesson: int


@strawberry.input
class GradeArticleExerciseInput:
    exercise_id: str
    submitted: str
    direction: ArticleDirection
    expected_definite: str
    expected_indefinite: str
    vocab_lemma: str | None = None


@strawberry.enum
class SentencePattern(enum.Enum):
    WHERE_IS_X = "where_is_x"
    X_IS_PREP_Y = "x_is_prep_y"
    X_AND_Y_ARE_PREP_Z = "x_and_y_are_prep_z"


@strawberry.type
class SentenceExercise:
    id: str
    pattern: SentencePattern
    hebrew: str
    transliteration: str
    english: str
    components: str
    lesson: int


@strawberry.enum
class TranslationPattern(enum.Enum):
    WHERE_QUESTION = "where_question"
    SIMPLE_STATEMENT = "simple_statement"
    CONJUNCTION = "conjunction"


@strawberry.type
class TranslationExercise:
    id: str
    pattern: TranslationPattern
    english: str
    hebrew_answer: str
    transliteration_answer: str
    components: str
    lesson: int


@strawberry.type
class TranslationGradeResult:
    correct: bool
    score: float
    expected: str
    submitted: str
    feedback: str
    transliteration: str


@strawberry.input
class GradeTranslationInput:
    exercise_id: str
    submitted: str
    expected_hebrew: str
    expected_transliteration: str
    pattern: str | None = None


@strawberry.enum
class VerbalPattern(enum.Enum):
    SUBJECT_VERB = "subject_verb"
    SUBJECT_VERB_OBJECT = "subject_verb_object"
    SUBJECT_VERB_PREP = "subject_verb_prep"
    SUBJECT_VERB_OBJECT_PREP = "subject_verb_object_prep"


@strawberry.type
class VerbalExercise:
    id: str
    pattern: VerbalPattern
    hebrew: str
    transliteration: str
    english_answer: str
    components: str
    lesson: int


@strawberry.type
class VerbalGradeResult:
    correct: bool
    score: float
    expected: str
    submitted: str
    feedback: str


@strawberry.input
class GradeVerbalInput:
    exercise_id: str
    submitted: str
    expected_english: str
    pattern: str | None = None


@strawberry.enum
class ComparativePattern(enum.Enum):
    COMPARATIVE_MIN = "comparative_min"


@strawberry.type
class ComparativeExercise:
    id: str
    pattern: ComparativePattern
    hebrew: str
    transliteration: str
    english_answer: str
    components: str
    lesson: int


@strawberry.type
class ComparativeGradeResult:
    correct: bool
    score: float
    expected: str
    submitted: str
    feedback: str


@strawberry.input
class GradeComparativeInput:
    exercise_id: str
    submitted: str
    expected_english: str
    pattern: str | None = None


@strawberry.enum
class RelativeClausePattern(enum.Enum):
    RELATIVE_ASHER = "relative_asher"


@strawberry.type
class RelativeClauseExercise:
    id: str
    pattern: RelativeClausePattern
    hebrew: str
    transliteration: str
    english_answer: str
    components: str
    lesson: int


@strawberry.type
class RelativeClauseGradeResult:
    correct: bool
    score: float
    expected: str
    submitted: str
    feedback: str


@strawberry.input
class GradeRelativeClauseInput:
    exercise_id: str
    submitted: str
    expected_english: str
    pattern: str | None = None


# ── Latin exercise types ──────────────────────────────────────────────────────

@strawberry.enum
class LatinVariant(enum.Enum):
    CLASSICAL = "lat"
    ECCLESIASTICAL = "ecl"


@strawberry.type
class LatinDeclensionExercise:
    id: str
    dict_form: str
    definition: str
    case: str
    number: str
    prompt: str
    answer: str
    lesson: int
    variant: LatinVariant


@strawberry.type
class LatinConjugationExercise:
    id: str
    dict_form: str
    definition: str
    person: str
    number: str
    prompt: str
    answer: str
    lesson: int
    variant: LatinVariant


@strawberry.type
class LatinGradeResult:
    correct: bool
    expected: str
    submitted: str
    feedback: str


@strawberry.input
class GradeLatinExerciseInput:
    exercise_id: str
    submitted: str
    expected: str
    vocab_lemma: str | None = None
    pattern: str | None = None
    # Routes the attempt to the right LessonProgress / primary deck.
    # Defaults to CLASSICAL for backward-compat with callers that don't
    # yet send the variant.
    variant: LatinVariant = LatinVariant.CLASSICAL


# ── Qal paradigm types ───────────────────────────────────────────────────────


@strawberry.type
class QalParadigmForm:
    conjugation: str
    person: str
    number: str
    gender: str
    label: str
    hebrew: str
    transliteration: str


@strawberry.type
class QalParadigm:
    binyan: str
    binyan_display: str
    root: str
    root_transliteration: str
    citation: str
    citation_transliteration: str
    definition: str
    available_roots: list[str]
    available_binyanim: list[str]
    forms: list[QalParadigmForm]


@strawberry.type
class QalWorksheetForm:
    conjugation: str
    person: str
    number: str
    gender: str
    label: str
    hebrew: str
    transliteration: str
    answer_hebrew: str
    answer_transliteration: str
    is_blank: bool


@strawberry.type
class QalWorksheet:
    binyan: str
    binyan_display: str
    root: str
    root_transliteration: str
    citation: str
    citation_transliteration: str
    definition: str
    forms: list[QalWorksheetForm]
    num_blanks: int


@strawberry.input
class GradeQalWorksheetAnswer:
    index: int
    submitted: str


@strawberry.input
class GradeQalWorksheetInput:
    root: str
    binyan: str | None = None
    answers: list[GradeQalWorksheetAnswer]


@strawberry.type
class QalWorksheetGradeItem:
    index: int
    label: str
    correct: bool
    expected: str
    submitted: str
    feedback: str


@strawberry.type
class QalWorksheetGradeResult:
    total: int
    correct_count: int
    items: list[QalWorksheetGradeItem]


@strawberry.type
class InterlinearWord:
    """A single word token in an interlinear text, source-agnostic."""
    ref: str                  # Source-specific position key (e.g. "Gen.1.1#01=L")
    position: int             # Token index within the verse
    text_type: str            # Text variant marker (L/Q/K for Hebrew, etc.)
    native: str               # Text in native script
    transliteration: str      # Romanised form
    gloss: str                # Word-level translation/gloss
    morphology: str           # Morphological code (source-specific)
    lemma_id: str             # Root/lemma identifier (Strong's for Hebrew, etc.)
    lemma: str                # Lemma in native script
    lemma_definition: str     # Lemma gloss/definition


@strawberry.type
class InterlinearVerse:
    """A single verse with its interlinear word tokens."""
    book: str
    chapter: int
    verse: int
    words: list[InterlinearWord]


@strawberry.type
class TahotWord:
    ref: str
    book: str
    chapter: int
    verse: int
    token: int
    text_type: str
    hebrew: str
    transliteration: str
    translation: str
    dstrongs: str
    grammar: str
    root_strongs: str
    expanded: str


@strawberry.type
class StrongsEntry:
    """A TBESH (Hebrew) or TBESG (Greek) lexicon entry keyed by Extended Strong's ID."""
    strongs_id: str        # dStrong ID, e.g. H0776G
    e_strongs_id: str      # eStrong#, e.g. H0776
    native: str            # Hebrew / Greek form
    transliteration: str
    morph: str
    gloss: str
    meaning: str           # HTML definition (may include <br>, <b>, <i>)


@strawberry.type
class TahotBookInfo:
    abbrev: str
    chapters: int


@strawberry.type
class TahotChapterInfo:
    chapter: int
    verse_count: int


@strawberry.type
class TahotVerseTranslation:
    verse: int
    text: str


# ── Vulgate interlinear types ─────────────────────────────────────────────────

@strawberry.type
class VulgateToken:
    ref: str
    book: str
    chapter: int
    verse: int
    token: int
    form: str
    lemma: str
    pos: str
    morphology: str
    relation: str


@strawberry.type
class VulgateBookInfo:
    abbrev: str
    name: str
    chapters: int


@strawberry.type
class VulgateChapterInfo:
    chapter: int
    verse_count: int


@strawberry.type
class VulgateVerseTranslation:
    verse: int
    text: str


# ── Greek interlinear types (GNT + LXX) ──────────────────────────────────────

@strawberry.type
class GreekToken:
    ref: str
    book: str
    chapter: int
    verse: int
    token: int
    text_type: str
    greek: str
    transliteration: str
    translation: str
    dstrongs: str
    grammar: str
    expanded: str


@strawberry.type
class GreekBookInfo:
    abbrev: str
    name: str
    chapters: int


@strawberry.type
class GreekChapterInfo:
    chapter: int
    verse_count: int


@strawberry.type
class GreekVerseTranslation:
    verse: int
    text: str


# ── Greek exercise types ──────────────────────────────────────────────────────

@strawberry.enum
class GreekVariant(enum.Enum):
    ANCIENT = "grc"
    KOINE = "gnt"


@strawberry.type
class GreekDeclensionExercise:
    id: str
    dict_form: str
    definition: str
    case: str
    number: str
    prompt: str
    answer: str
    lesson: int
    variant: GreekVariant


@strawberry.type
class GreekConjugationExercise:
    id: str
    dict_form: str
    definition: str
    person: str
    number: str
    prompt: str
    answer: str
    lesson: int
    variant: GreekVariant


@strawberry.type
class GreekGradeResult:
    correct: bool
    expected: str
    submitted: str
    feedback: str


@strawberry.enum
class GreekExerciseKind(enum.Enum):
    DECLENSION = "declension"
    CONJUGATION = "conjugation"


@strawberry.input
class GradeGreekExerciseInput:
    exercise_id: str
    submitted: str
    expected: str
    vocab_lemma: str | None = None
    pattern: str | None = None
    # Defaults preserve backward-compat: ANCIENT + DECLENSION mirror the
    # original single-mutation behaviour. Conjugation pages and NT-Greek
    # pages must set these explicitly so attempts are attributed to the
    # right language and exercise type.
    variant: GreekVariant = GreekVariant.ANCIENT
    kind: GreekExerciseKind = GreekExerciseKind.DECLENSION


# ── Sanskrit exercise types ───────────────────────────────────────────────────

@strawberry.type
class SanskritDeclensionExercise:
    id: str
    dict_form: str
    devanagari: str
    definition: str
    case: str
    number: str
    prompt: str
    answer: str
    lesson: int


@strawberry.type
class SanskritGradeResult:
    correct: bool
    expected: str
    submitted: str
    feedback: str


@strawberry.input
class GradeSanskritExerciseInput:
    exercise_id: str
    submitted: str
    expected: str
    vocab_lemma: str | None = None
    pattern: str | None = None
