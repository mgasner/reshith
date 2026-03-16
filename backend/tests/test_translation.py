"""Tests for English-to-Hebrew translation exercise generation."""

import pytest

from reshith.exercises.article import Noun, load_nouns_for_exercises
from reshith.exercises.sentences import (
    Adverb,
    Conjunction,
    Preposition,
    _generate_fallback_mapping,
    load_adverbs,
    load_conjunctions,
    load_prepositions,
)
from reshith.exercises.translation import (
    TranslationExercise,
    TranslationGradeResult,
    generate_conjunction_exercise,
    generate_simple_statement_exercise,
    generate_translation_exercises,
    generate_where_question_exercise,
    grade_translation,
    normalize_hebrew_for_grading,
)


def make_noun(
    hebrew: str,
    transliteration: str,
    definition: str,
    lesson: int = 1,
) -> Noun:
    return Noun(
        hebrew=hebrew,
        transliteration=transliteration,
        definition=definition,
        category="nouns",
        lesson=lesson,
    )


def make_preposition(
    hebrew: str,
    transliteration: str,
    definition: str,
    is_inseparable: bool = False,
) -> Preposition:
    return Preposition(
        hebrew=hebrew,
        transliteration=transliteration,
        definition=definition,
        is_inseparable=is_inseparable,
    )


def make_adverb(hebrew: str, transliteration: str, definition: str) -> Adverb:
    return Adverb(
        hebrew=hebrew,
        transliteration=transliteration,
        definition=definition,
    )


def make_conjunction(hebrew: str, transliteration: str, definition: str) -> Conjunction:
    return Conjunction(
        hebrew=hebrew,
        transliteration=transliteration,
        definition=definition,
    )


class TestNormalizeHebrewForGrading:
    def test_normalize_strips_whitespace(self):
        result = normalize_hebrew_for_grading("  בַּיִת  ")
        assert result == "בַּיִת"

    def test_normalize_removes_punctuation(self):
        result = normalize_hebrew_for_grading("בַּיִת.")
        assert result == "בַּיִת"

    def test_normalize_removes_question_mark(self):
        result = normalize_hebrew_for_grading("אַיֵּה הַבַּיִת?")
        assert result == "אַיֵּה הַבַּיִת"

    def test_normalize_collapses_double_spaces(self):
        result = normalize_hebrew_for_grading("הַנַּעַר  בַּבַּיִת")
        assert result == "הַנַּעַר בַּבַּיִת"

    def test_normalize_removes_cantillation(self):
        text_with_cantillation = "בְּרֵאשִׁ֖ית"
        result = normalize_hebrew_for_grading(text_with_cantillation)
        assert "\u0596" not in result


class TestGenerateWhereQuestionExercise:
    @pytest.mark.asyncio
    async def test_returns_exercise_singular(self):
        nouns = load_nouns_for_exercises(1)
        adverbs = load_adverbs(1)
        conjunctions = load_conjunctions(1)

        exercise = await generate_where_question_exercise(
            nouns, adverbs, conjunctions, use_plural=False
        )

        if exercise is not None:
            assert exercise.pattern == "where_question"
            assert "Where is the" in exercise.english
            assert "?" in exercise.hebrew_answer
            assert "?" in exercise.transliteration_answer

    @pytest.mark.asyncio
    async def test_returns_exercise_plural(self):
        nouns = load_nouns_for_exercises(1)
        adverbs = load_adverbs(1)
        conjunctions = load_conjunctions(1)

        exercise = await generate_where_question_exercise(
            nouns, adverbs, conjunctions, use_plural=True
        )

        if exercise is not None:
            assert exercise.pattern == "where_question"
            assert "Where are the" in exercise.english
            assert "and" in exercise.english

    @pytest.mark.asyncio
    async def test_returns_none_without_where_adverb(self):
        nouns = load_nouns_for_exercises(1)
        adverbs = []
        conjunctions = load_conjunctions(1)

        exercise = await generate_where_question_exercise(
            nouns, adverbs, conjunctions
        )

        assert exercise is None

    @pytest.mark.asyncio
    async def test_exercise_has_components(self):
        nouns = load_nouns_for_exercises(1)
        adverbs = load_adverbs(1)
        conjunctions = load_conjunctions(1)

        exercise = await generate_where_question_exercise(
            nouns, adverbs, conjunctions, use_plural=False
        )

        if exercise is not None:
            assert "adverb" in exercise.components
            assert "noun1" in exercise.components


class TestGenerateSimpleStatementExercise:
    @pytest.mark.asyncio
    async def test_returns_exercise(self):
        nouns = load_nouns_for_exercises(1)
        preps = load_prepositions(1)
        noun_prep_map = _generate_fallback_mapping(nouns, preps)

        exercise = await generate_simple_statement_exercise(nouns, preps, noun_prep_map)

        if exercise is not None:
            assert exercise.pattern == "simple_statement"
            assert "The" in exercise.english
            assert "is" in exercise.english
            assert exercise.hebrew_answer.endswith(".")

    @pytest.mark.asyncio
    async def test_exercise_has_components(self):
        nouns = load_nouns_for_exercises(1)
        preps = load_prepositions(1)
        noun_prep_map = _generate_fallback_mapping(nouns, preps)

        exercise = await generate_simple_statement_exercise(nouns, preps, noun_prep_map)

        if exercise is not None:
            assert "noun1" in exercise.components
            assert "noun2" in exercise.components
            assert "preposition" in exercise.components

    @pytest.mark.asyncio
    async def test_returns_none_with_empty_nouns(self):
        nouns: list[Noun] = []
        preps = load_prepositions(1)
        noun_prep_map: dict = {}

        exercise = await generate_simple_statement_exercise(nouns, preps, noun_prep_map)

        assert exercise is None


class TestGenerateConjunctionExercise:
    @pytest.mark.asyncio
    async def test_returns_exercise(self):
        nouns = load_nouns_for_exercises(2)
        preps = load_prepositions(1)
        conjunctions = load_conjunctions(1)
        noun_prep_map = _generate_fallback_mapping(nouns, preps)

        exercise = await generate_conjunction_exercise(
            nouns, preps, conjunctions, noun_prep_map
        )

        if exercise is not None:
            assert exercise.pattern == "conjunction"
            assert "and" in exercise.english.lower()
            assert "are" in exercise.english

    @pytest.mark.asyncio
    async def test_exercise_has_components(self):
        nouns = load_nouns_for_exercises(2)
        preps = load_prepositions(1)
        conjunctions = load_conjunctions(1)
        noun_prep_map = _generate_fallback_mapping(nouns, preps)

        exercise = await generate_conjunction_exercise(
            nouns, preps, conjunctions, noun_prep_map
        )

        if exercise is not None:
            assert "noun1" in exercise.components
            assert "noun2" in exercise.components
            assert "noun3" in exercise.components
            assert "preposition" in exercise.components
            assert "conjunction" in exercise.components

    @pytest.mark.asyncio
    async def test_returns_none_without_conjunction(self):
        nouns = load_nouns_for_exercises(2)
        preps = load_prepositions(1)
        conjunctions: list[Conjunction] = []
        noun_prep_map = _generate_fallback_mapping(nouns, preps)

        exercise = await generate_conjunction_exercise(
            nouns, preps, conjunctions, noun_prep_map
        )

        assert exercise is None


class TestGenerateTranslationExercises:
    @pytest.mark.asyncio
    async def test_returns_list(self):
        exercises = await generate_translation_exercises(max_lesson=1, count=5)

        assert isinstance(exercises, list)

    @pytest.mark.asyncio
    async def test_respects_count(self):
        exercises = await generate_translation_exercises(max_lesson=1, count=3)

        assert len(exercises) <= 3

    @pytest.mark.asyncio
    async def test_with_patterns_filter(self):
        exercises = await generate_translation_exercises(
            max_lesson=1,
            count=5,
            patterns=["simple_statement"],
        )

        for ex in exercises:
            assert ex.pattern == "simple_statement"

    @pytest.mark.asyncio
    async def test_lesson_2(self):
        exercises = await generate_translation_exercises(max_lesson=2, count=5)

        assert isinstance(exercises, list)

    @pytest.mark.asyncio
    async def test_lesson_3(self):
        exercises = await generate_translation_exercises(max_lesson=3, count=5)

        assert isinstance(exercises, list)


class TestTranslationExerciseStructure:
    @pytest.mark.asyncio
    async def test_exercise_has_required_fields(self):
        exercises = await generate_translation_exercises(max_lesson=1, count=3)

        for ex in exercises:
            assert isinstance(ex, TranslationExercise)
            assert ex.pattern in ["where_question", "simple_statement", "conjunction"]
            assert ex.english
            assert ex.hebrew_answer
            assert ex.transliteration_answer
            assert isinstance(ex.components, dict)

    @pytest.mark.asyncio
    async def test_exercise_english_is_proper_sentence(self):
        exercises = await generate_translation_exercises(max_lesson=1, count=3)

        for ex in exercises:
            assert ex.english[0].isupper()
            assert ex.english.endswith(".") or ex.english.endswith("?")


class TestGradeTranslation:
    def test_correct_answer(self):
        result = grade_translation(
            submitted="הַנַּעַר בַּבַּיִת.",
            expected_hebrew="הַנַּעַר בַּבַּיִת.",
            expected_transliteration="hannáʿar babáyit.",
        )

        assert result.correct is True
        assert result.score == 1.0
        assert result.feedback == "Correct!"

    def test_correct_without_punctuation(self):
        result = grade_translation(
            submitted="הַנַּעַר בַּבַּיִת",
            expected_hebrew="הַנַּעַר בַּבַּיִת.",
            expected_transliteration="hannáʿar babáyit.",
        )

        assert result.correct is True
        assert result.score == 1.0

    def test_wrong_word_order(self):
        result = grade_translation(
            submitted="בַּבַּיִת הַנַּעַר",
            expected_hebrew="הַנַּעַר בַּבַּיִת.",
            expected_transliteration="hannáʿar babáyit.",
        )

        assert result.correct is False
        assert result.score == 0.7
        assert "wrong order" in result.feedback.lower()

    def test_partially_correct(self):
        result = grade_translation(
            submitted="הַנַּעַר בַּנָּהָר",
            expected_hebrew="הַנַּעַר בַּבַּיִת.",
            expected_transliteration="hannáʿar babáyit.",
        )

        assert result.correct is False
        assert 0 < result.score < 1.0
        assert "Partially correct" in result.feedback

    def test_completely_incorrect(self):
        result = grade_translation(
            submitted="שָׁלוֹם",
            expected_hebrew="הַנַּעַר בַּבַּיִת.",
            expected_transliteration="hannáʿar babáyit.",
        )

        assert result.correct is False
        assert result.score == 0.0
        assert "Incorrect" in result.feedback

    def test_result_includes_transliteration(self):
        result = grade_translation(
            submitted="wrong",
            expected_hebrew="הַנַּעַר בַּבַּיִת.",
            expected_transliteration="hannáʿar babáyit.",
        )

        assert result.transliteration == "hannáʿar babáyit."


class TestGradeTranslationResult:
    def test_result_has_all_fields(self):
        result = grade_translation(
            submitted="test",
            expected_hebrew="expected",
            expected_transliteration="translit",
        )

        assert isinstance(result, TranslationGradeResult)
        assert hasattr(result, "correct")
        assert hasattr(result, "score")
        assert hasattr(result, "expected")
        assert hasattr(result, "submitted")
        assert hasattr(result, "feedback")
        assert hasattr(result, "transliteration")
