"""Tests for advanced exercise generation (Lesson 5+)."""

import pytest

from reshith.exercises.advanced import (
    Adjective,
    ComparativeExercise,
    ComparativeGradeResult,
    RelativeClauseExercise,
    _generate_fallback_comparative_mappings,
    _get_comparative_cache_key,
    _get_comparative_english,
    _get_english_adjective,
    _get_english_noun,
    attach_min_preposition,
    generate_comparative_exercise,
    generate_comparative_exercises,
    generate_comparative_mappings,
    generate_relative_clause_exercise,
    generate_relative_clause_exercises,
    grade_comparative_exercise,
    grade_relative_clause_exercise,
    load_adjectives,
    load_asher_pronoun,
    load_min_preposition,
    normalize_english_for_grading,
)
from reshith.exercises.article import Noun


class TestAdjectiveDataclass:
    """Tests for the Adjective dataclass."""

    def test_adjective_creation(self):
        adj = Adjective(
            hebrew="יָקָר",
            transliteration="yāqār",
            definition="precious",
            lesson=5,
        )
        assert adj.hebrew == "יָקָר"
        assert adj.transliteration == "yāqār"
        assert adj.definition == "precious"
        assert adj.lesson == 5

    def test_adjective_with_multiple_definitions(self):
        adj = Adjective(
            hebrew="קָשֶׁה",
            transliteration="qāšeh",
            definition="difficult, hard, harsh",
            lesson=5,
        )
        assert adj.definition == "difficult, hard, harsh"


class TestLoadAdjectives:
    """Tests for loading adjectives from vocabulary."""

    def test_load_adjectives_lesson_5(self):
        adjectives = load_adjectives(5)
        assert len(adjectives) >= 5
        translit_list = [a.transliteration for a in adjectives]
        assert "yāqār" in translit_list
        assert "yāšār" in translit_list
        assert "ṣaddîq" in translit_list

    def test_load_adjectives_lesson_2_empty(self):
        adjectives = load_adjectives(2)
        assert len(adjectives) == 0

    def test_adjectives_have_correct_lesson(self):
        adjectives = load_adjectives(5)
        for adj in adjectives:
            assert adj.lesson <= 5


class TestLoadMinPreposition:
    """Tests for loading the מִן preposition."""

    def test_load_min_lesson_5(self):
        result = load_min_preposition(5)
        assert result is not None
        hebrew, translit = result
        assert hebrew == "מִן"
        assert translit == "min-"

    def test_load_min_lesson_4_none(self):
        result = load_min_preposition(4)
        assert result is None


class TestLoadAsherPronoun:
    """Tests for loading the אֲשֶׁר relative pronoun."""

    def test_load_asher_lesson_5(self):
        result = load_asher_pronoun(5)
        assert result is not None
        hebrew, translit = result
        assert hebrew == "אֲשֶׁר"
        assert translit == "ʾăšer"

    def test_load_asher_lesson_4_none(self):
        result = load_asher_pronoun(4)
        assert result is None


class TestAttachMinPreposition:
    """Tests for attaching the מִן preposition."""

    def test_attach_min_with_article(self):
        heb, trans = attach_min_preposition("הַמֶּלֶךְ", "hamméleḵ", has_article=True)
        assert heb == "מֵהַמֶּלֶךְ"
        assert trans == "mēhamméleḵ"

    def test_attach_min_with_qamets_article(self):
        heb, trans = attach_min_preposition("הָאִישׁ", "hāʾîš", has_article=True)
        assert heb == "מֵהָאִישׁ"
        assert trans == "mēhāʾîš"

    def test_attach_min_before_guttural(self):
        heb, trans = attach_min_preposition("אִישׁ", "ʾîš", has_article=False)
        assert heb == "מֵאִישׁ"
        assert trans == "mēʾîš"

    def test_attach_min_before_regular_consonant(self):
        heb, trans = attach_min_preposition("מֶלֶךְ", "méleḵ", has_article=False)
        assert "מִ" in heb
        assert trans.startswith("mi")

    def test_attach_min_before_resh(self):
        heb, trans = attach_min_preposition("רֹאשׁ", "rōʾš", has_article=False)
        assert heb == "מֵרֹאשׁ"
        assert trans == "mērōʾš"


class TestComparativeCacheKey:
    """Tests for comparative cache key generation."""

    def test_cache_key_deterministic(self):
        adjs = [Adjective("יָקָר", "yāqār", "precious", 5)]
        nouns = [Noun("זָהָב", "zāhāḇ", "gold", "nouns", 5)]
        key1 = _get_comparative_cache_key(adjs, nouns)
        key2 = _get_comparative_cache_key(adjs, nouns)
        assert key1 == key2

    def test_cache_key_different_for_different_inputs(self):
        adjs1 = [Adjective("יָקָר", "yāqār", "precious", 5)]
        adjs2 = [Adjective("רָשָׁע", "rāšāʿ", "evil", 5)]
        nouns = [Noun("זָהָב", "zāhāḇ", "gold", "nouns", 5)]
        key1 = _get_comparative_cache_key(adjs1, nouns)
        key2 = _get_comparative_cache_key(adjs2, nouns)
        assert key1 != key2


class TestFallbackComparativeMappings:
    """Tests for fallback comparative mappings."""

    def test_fallback_generates_mappings(self):
        adjs = [
            Adjective("יָקָר", "yāqār", "precious", 5),
            Adjective("צַדִּיק", "ṣaddîq", "righteous", 5),
        ]
        nouns = [
            Noun("זָהָב", "zāhāḇ", "gold", "nouns", 5),
            Noun("כֶּסֶף", "késep̄", "silver", "nouns", 5),
            Noun("חָכְמָה", "ḥoḵmāh", "wisdom", "nouns", 5),
        ]
        mappings = _generate_fallback_comparative_mappings(adjs, nouns)
        assert "yāqār" in mappings
        assert "ṣaddîq" in mappings

    def test_fallback_precious_adjective_pairs(self):
        adjs = [Adjective("יָקָר", "yāqār", "precious", 5)]
        nouns = [
            Noun("זָהָב", "zāhāḇ", "gold", "nouns", 5),
            Noun("כֶּסֶף", "késep̄", "silver", "nouns", 5),
        ]
        mappings = _generate_fallback_comparative_mappings(adjs, nouns)
        pairs = mappings.get("yāqār", [])
        assert len(pairs) > 0


class TestEnglishExtraction:
    """Tests for extracting English meanings."""

    def test_get_english_adjective_simple(self):
        adj = Adjective("יָקָר", "yāqār", "precious", 5)
        assert _get_english_adjective(adj) == "precious"

    def test_get_english_adjective_multiple(self):
        adj = Adjective("קָשֶׁה", "qāšeh", "difficult, hard, harsh", 5)
        assert _get_english_adjective(adj) == "difficult"

    def test_get_english_noun_simple(self):
        noun = Noun("זָהָב", "zāhāḇ", "gold", "nouns", 5)
        assert _get_english_noun(noun) == "gold"

    def test_get_english_noun_multiple(self):
        noun = Noun("כֶּסֶף", "késep̄", "silver, money", "nouns", 5)
        assert _get_english_noun(noun) == "silver"


class TestComparativeEnglish:
    """Tests for generating comparative forms."""

    def test_comparative_short_word(self):
        assert _get_comparative_english("hard") == "harder"

    def test_comparative_ending_in_e(self):
        assert _get_comparative_english("large") == "larger"

    def test_comparative_ending_in_y(self):
        assert _get_comparative_english("easy") == "easier"

    def test_comparative_long_word(self):
        assert _get_comparative_english("precious") == "more precious"

    def test_comparative_righteous(self):
        assert _get_comparative_english("righteous") == "more righteous"


class TestComparativeExerciseDataclass:
    """Tests for the ComparativeExercise dataclass."""

    def test_comparative_exercise_creation(self):
        ex = ComparativeExercise(
            pattern="comparative_min",
            hebrew="הַזָּהָב יָקָר מִכֶּסֶף.",
            transliteration="hazzāhāḇ yāqār mikkésep̄.",
            english_answer="The gold is more precious than silver.",
            components={
                "subject": "זָהָב",
                "adjective": "יָקָר",
                "compared_noun": "כֶּסֶף",
                "preposition": "מִן",
            },
        )
        assert ex.pattern == "comparative_min"
        assert "יָקָר" in ex.hebrew
        assert "than" in ex.english_answer


class TestGenerateComparativeExercise:
    """Tests for generating individual comparative exercises."""

    @pytest.mark.asyncio
    async def test_generate_with_valid_mappings(self):
        adjs = [Adjective("יָקָר", "yāqār", "precious", 5)]
        nouns = [
            Noun("זָהָב", "zāhāḇ", "gold", "nouns", 5),
            Noun("כֶּסֶף", "késep̄", "silver", "nouns", 5),
        ]
        mappings = {"yāqār": [["zāhāḇ", "késep̄"]]}
        exercise = await generate_comparative_exercise(adjs, nouns, mappings)
        assert exercise is not None
        assert exercise.pattern == "comparative_min"
        assert "than" in exercise.english_answer

    @pytest.mark.asyncio
    async def test_generate_with_empty_mappings(self):
        adjs = [Adjective("יָקָר", "yāqār", "precious", 5)]
        nouns = [Noun("זָהָב", "zāhāḇ", "gold", "nouns", 5)]
        mappings = {}
        exercise = await generate_comparative_exercise(adjs, nouns, mappings)
        assert exercise is None

    @pytest.mark.asyncio
    async def test_generate_with_missing_noun(self):
        adjs = [Adjective("יָקָר", "yāqār", "precious", 5)]
        nouns = [Noun("זָהָב", "zāhāḇ", "gold", "nouns", 5)]
        mappings = {"yāqār": [["zāhāḇ", "nonexistent"]]}
        exercise = await generate_comparative_exercise(adjs, nouns, mappings)
        assert exercise is None


class TestGenerateComparativeExercises:
    """Tests for generating multiple comparative exercises."""

    @pytest.mark.asyncio
    async def test_generate_exercises_lesson_5(self):
        exercises = await generate_comparative_exercises(max_lesson=5, count=5)
        assert len(exercises) <= 5
        for ex in exercises:
            assert ex.pattern == "comparative_min"
            assert "than" in ex.english_answer

    @pytest.mark.asyncio
    async def test_generate_exercises_lesson_2_empty(self):
        exercises = await generate_comparative_exercises(max_lesson=2, count=5)
        assert len(exercises) == 0


class TestRelativeClauseExerciseDataclass:
    """Tests for the RelativeClauseExercise dataclass."""

    def test_relative_clause_exercise_creation(self):
        ex = RelativeClauseExercise(
            pattern="relative_asher",
            hebrew="הָאִישׁ אֲשֶׁר צַדִּיק.",
            transliteration="hāʾîš ʾăšer ṣaddîq.",
            english_answer="The man who is righteous.",
            components={
                "noun": "אִישׁ",
                "relative_pronoun": "אֲשֶׁר",
                "adjective": "צַדִּיק",
            },
        )
        assert ex.pattern == "relative_asher"
        assert "אֲשֶׁר" in ex.hebrew
        assert "who" in ex.english_answer


class TestGenerateRelativeClauseExercise:
    """Tests for generating individual relative clause exercises."""

    @pytest.mark.asyncio
    async def test_generate_with_valid_inputs(self):
        nouns = [Noun("אִישׁ", "ʾîš", "man", "nouns", 1)]
        adjs = [Adjective("צַדִּיק", "ṣaddîq", "righteous", 5)]
        exercise = await generate_relative_clause_exercise(nouns, adjs)
        assert exercise is not None
        assert exercise.pattern == "relative_asher"
        assert "אֲשֶׁר" in exercise.hebrew
        assert "who" in exercise.english_answer

    @pytest.mark.asyncio
    async def test_generate_with_empty_nouns(self):
        nouns = []
        adjs = [Adjective("צַדִּיק", "ṣaddîq", "righteous", 5)]
        exercise = await generate_relative_clause_exercise(nouns, adjs)
        assert exercise is None

    @pytest.mark.asyncio
    async def test_generate_with_empty_adjectives(self):
        nouns = [Noun("אִישׁ", "ʾîš", "man", "nouns", 1)]
        adjs = []
        exercise = await generate_relative_clause_exercise(nouns, adjs)
        assert exercise is None


class TestGenerateRelativeClauseExercises:
    """Tests for generating multiple relative clause exercises."""

    @pytest.mark.asyncio
    async def test_generate_exercises_lesson_5(self):
        exercises = await generate_relative_clause_exercises(max_lesson=5, count=5)
        assert len(exercises) <= 5
        for ex in exercises:
            assert ex.pattern == "relative_asher"
            assert "אֲשֶׁר" in ex.hebrew

    @pytest.mark.asyncio
    async def test_generate_exercises_lesson_4_empty(self):
        exercises = await generate_relative_clause_exercises(max_lesson=4, count=5)
        assert len(exercises) == 0


class TestNormalizeEnglishForGrading:
    """Tests for English normalization."""

    def test_normalize_strips_whitespace(self):
        assert normalize_english_for_grading("  hello  ") == "hello"

    def test_normalize_lowercase(self):
        assert normalize_english_for_grading("Hello World") == "hello world"

    def test_normalize_removes_punctuation(self):
        assert normalize_english_for_grading("Hello!") == "hello"
        assert normalize_english_for_grading("Hello?") == "hello"
        assert normalize_english_for_grading("Hello.") == "hello"

    def test_normalize_collapses_spaces(self):
        assert normalize_english_for_grading("hello  world") == "hello world"


class TestGradeComparativeExercise:
    """Tests for grading comparative exercises."""

    def test_grade_exact_match(self):
        result = grade_comparative_exercise(
            submitted="The gold is more precious than silver.",
            expected_english="The gold is more precious than silver.",
        )
        assert result.correct is True
        assert result.score == 1.0
        assert result.feedback == "Correct!"

    def test_grade_case_insensitive(self):
        result = grade_comparative_exercise(
            submitted="the gold is more precious than silver",
            expected_english="The gold is more precious than silver.",
        )
        assert result.correct is True
        assert result.score == 1.0

    def test_grade_almost_correct(self):
        result = grade_comparative_exercise(
            submitted="The gold is more precious than the silver.",
            expected_english="The gold is more precious than silver.",
        )
        assert result.score >= 0.8

    def test_grade_incorrect(self):
        result = grade_comparative_exercise(
            submitted="The gold is shiny.",
            expected_english="The gold is more precious than silver.",
        )
        assert result.correct is False
        assert result.score < 0.8

    def test_grade_partial_credit_for_than(self):
        result = grade_comparative_exercise(
            submitted="Something is better than something else.",
            expected_english="The gold is more precious than silver.",
        )
        assert result.score >= 0.3


class TestGradeRelativeClauseExercise:
    """Tests for grading relative clause exercises."""

    def test_grade_exact_match(self):
        result = grade_relative_clause_exercise(
            submitted="The man who is righteous.",
            expected_english="The man who is righteous.",
        )
        assert result.correct is True
        assert result.score == 1.0

    def test_grade_which_instead_of_who(self):
        result = grade_relative_clause_exercise(
            submitted="The man which is righteous.",
            expected_english="The man who is righteous.",
        )
        assert result.score >= 0.8

    def test_grade_that_instead_of_who(self):
        result = grade_relative_clause_exercise(
            submitted="The man that is righteous.",
            expected_english="The man who is righteous.",
        )
        assert result.score >= 0.8

    def test_grade_incorrect(self):
        result = grade_relative_clause_exercise(
            submitted="The man is good.",
            expected_english="The man who is righteous.",
        )
        assert result.correct is False

    def test_grade_partial_credit_for_relative_word(self):
        result = grade_relative_clause_exercise(
            submitted="Someone who is something.",
            expected_english="The man who is righteous.",
        )
        assert result.score >= 0.4


class TestComparativeGradeResultDataclass:
    """Tests for the ComparativeGradeResult dataclass."""

    def test_grade_result_creation(self):
        result = ComparativeGradeResult(
            correct=True,
            score=1.0,
            expected="The gold is more precious than silver.",
            submitted="The gold is more precious than silver.",
            feedback="Correct!",
        )
        assert result.correct is True
        assert result.score == 1.0
        assert result.feedback == "Correct!"


class TestVocabularyLoaders:
    """Tests for vocabulary loader functions."""

    def test_load_adjectives_up_to(self):
        from reshith.exercises.vocabulary import load_adjectives_up_to
        adjs = load_adjectives_up_to(5)
        assert len(adjs) >= 5
        for adj in adjs:
            assert adj.category == "adjectives"

    def test_load_proper_names_up_to(self):
        from reshith.exercises.vocabulary import load_proper_names_up_to
        names = load_proper_names_up_to(5)
        assert len(names) >= 3
        for name in names:
            assert name.category == "proper_names"


class TestComparativeMappingsGeneration:
    """Tests for comparative mappings generation."""

    @pytest.mark.asyncio
    async def test_generate_mappings_uses_fallback_without_api_key(self):
        adjs = [Adjective("יָקָר", "yāqār", "precious", 5)]
        nouns = [
            Noun("זָהָב", "zāhāḇ", "gold", "nouns", 5),
            Noun("כֶּסֶף", "késep̄", "silver", "nouns", 5),
        ]
        mappings = await generate_comparative_mappings(adjs, nouns)
        assert isinstance(mappings, dict)
        assert "yāqār" in mappings


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_generate_comparative_with_single_noun(self):
        adjs = [Adjective("יָקָר", "yāqār", "precious", 5)]
        nouns = [Noun("זָהָב", "zāhāḇ", "gold", "nouns", 5)]
        mappings = {"yāqār": [["zāhāḇ"]]}
        exercise = await generate_comparative_exercise(adjs, nouns, mappings)
        assert exercise is None

    @pytest.mark.asyncio
    async def test_generate_comparative_with_empty_pairs(self):
        adjs = [Adjective("יָקָר", "yāqār", "precious", 5)]
        nouns = [Noun("זָהָב", "zāhāḇ", "gold", "nouns", 5)]
        mappings = {"yāqār": []}
        exercise = await generate_comparative_exercise(adjs, nouns, mappings)
        assert exercise is None

    def test_attach_min_empty_string(self):
        heb, trans = attach_min_preposition("", "", has_article=False)
        assert "מִן" in heb or "מֵ" in heb or "מִ" in heb
