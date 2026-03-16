"""Tests for sentence-level exercise generation."""

import pytest

from reshith.exercises.article import Noun, load_nouns_for_exercises
from reshith.exercises.sentences import (
    Adverb,
    Conjunction,
    Preposition,
    SentenceExercise,
    _generate_fallback_mapping,
    attach_inseparable_preposition,
    generate_sentence_exercises,
    generate_where_is_x_exercise,
    generate_x_and_y_are_prep_z_exercise,
    generate_x_is_prep_y_exercise,
    load_adverbs,
    load_conjunctions,
    load_prepositions,
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


class TestLoadVocabulary:
    def test_load_prepositions_lesson_1(self):
        preps = load_prepositions(1)
        assert len(preps) > 0
        assert all(isinstance(p, Preposition) for p in preps)

    def test_load_prepositions_includes_inseparable(self):
        preps = load_prepositions(1)
        inseparable = [p for p in preps if p.is_inseparable]
        assert len(inseparable) > 0

    def test_load_adverbs_lesson_1(self):
        adverbs = load_adverbs(1)
        assert len(adverbs) > 0
        assert all(isinstance(a, Adverb) for a in adverbs)

    def test_load_adverbs_includes_where(self):
        adverbs = load_adverbs(1)
        where_adverbs = [a for a in adverbs if "where" in a.definition.lower()]
        assert len(where_adverbs) > 0

    def test_load_conjunctions_lesson_1(self):
        conjs = load_conjunctions(1)
        assert len(conjs) > 0
        assert all(isinstance(c, Conjunction) for c in conjs)

    def test_load_conjunctions_includes_and(self):
        conjs = load_conjunctions(1)
        and_conjs = [c for c in conjs if "and" in c.definition.lower()]
        assert len(and_conjs) > 0


class TestAttachInseparablePreposition:
    def test_attach_be_without_article(self):
        prep = make_preposition("בְּ", "bə", "in", is_inseparable=True)
        hebrew, trans = attach_inseparable_preposition(
            prep, "בַּיִת", "báyit", has_article=False
        )
        assert hebrew == "בְּבַּיִת"
        assert trans == "bəbáyit"

    def test_attach_le_without_article(self):
        prep = make_preposition("לְ", "lə", "to", is_inseparable=True)
        hebrew, trans = attach_inseparable_preposition(
            prep, "נָהָר", "nāhār", has_article=False
        )
        assert hebrew == "לְנָהָר"
        assert trans == "lənāhār"

    def test_attach_be_with_article_ha(self):
        """Test בְּ + הַבַּיִת = בַּבַּיִת (in the house)"""
        prep = make_preposition("בְּ", "bə", "in", is_inseparable=True)
        hebrew, trans = attach_inseparable_preposition(
            prep, "הַבַּיִת", "habáyit", has_article=True
        )
        assert hebrew == "בַּבַּיִת"
        assert trans == "babáyit"

    def test_attach_le_with_article_ha(self):
        """Test לְ + הַנָּהָר = לַנָּהָר (to the river)"""
        prep = make_preposition("לְ", "lə", "to", is_inseparable=True)
        hebrew, trans = attach_inseparable_preposition(
            prep, "הַנָּהָר", "hannāhār", has_article=True
        )
        assert hebrew == "לַנָּהָר"
        assert trans == "lannāhār"

    def test_attach_separate_preposition_with_article(self):
        """Test עַל־ + הַבַּיִת = עַל־הַבַּיִת"""
        prep = make_preposition("עַל־", "ʿal-", "on", is_inseparable=False)
        hebrew, trans = attach_inseparable_preposition(
            prep, "הַבַּיִת", "habáyit", has_article=True
        )
        assert "־" in hebrew
        assert hebrew == "עַל־־הַבַּיִת"

    def test_attach_separate_preposition_without_article(self):
        """Test עַל־ + בַּיִת = עַל־ בַּיִת"""
        prep = make_preposition("עַל־", "ʿal-", "on", is_inseparable=False)
        hebrew, trans = attach_inseparable_preposition(
            prep, "בַּיִת", "báyit", has_article=False
        )
        assert " " in hebrew


class TestFallbackMapping:
    def test_fallback_mapping_creates_entries(self):
        nouns = [
            make_noun("נַעַר", "náʿar", "boy"),
            make_noun("בַּיִת", "báyit", "house"),
            make_noun("נָהָר", "nāhār", "river"),
        ]
        preps = [
            make_preposition("בְּ", "bə", "in", is_inseparable=True),
            make_preposition("אֵצֶל", "ʾēṣel", "near, beside", is_inseparable=False),
        ]

        mapping = _generate_fallback_mapping(nouns, preps)

        assert len(mapping) == 3
        assert "náʿar" in mapping
        assert "báyit" in mapping
        assert "nāhār" in mapping

    def test_fallback_mapping_animate_nouns_get_locations(self):
        nouns = [
            make_noun("נַעַר", "náʿar", "boy"),
            make_noun("בַּיִת", "báyit", "house"),
        ]
        preps = [make_preposition("בְּ", "bə", "in", is_inseparable=True)]

        mapping = _generate_fallback_mapping(nouns, preps)

        assert "báyit" in mapping["náʿar"]["bə"]

    def test_fallback_mapping_near_includes_all_others(self):
        nouns = [
            make_noun("נַעַר", "náʿar", "boy"),
            make_noun("בַּיִת", "báyit", "house"),
            make_noun("נָהָר", "nāhār", "river"),
        ]
        preps = [make_preposition("אֵצֶל", "ʾēṣel", "near, beside", is_inseparable=False)]

        mapping = _generate_fallback_mapping(nouns, preps)

        assert "báyit" in mapping["náʿar"]["ʾēṣel"]
        assert "nāhār" in mapping["náʿar"]["ʾēṣel"]
        assert "náʿar" not in mapping["náʿar"]["ʾēṣel"]


class TestGenerateWhereIsXExercise:
    @pytest.mark.asyncio
    async def test_generate_where_is_x_returns_exercise(self):
        nouns = load_nouns_for_exercises(1)
        preps = load_prepositions(1)
        adverbs = load_adverbs(1)
        noun_prep_map = _generate_fallback_mapping(nouns, preps)

        exercise = await generate_where_is_x_exercise(nouns, preps, adverbs, noun_prep_map)

        if exercise is not None:
            assert exercise.pattern == "where_is_x"
            assert "?" in exercise.hebrew
            assert "?" in exercise.transliteration
            assert "Where" in exercise.english

    @pytest.mark.asyncio
    async def test_generate_where_is_x_returns_none_without_where_adverb(self):
        nouns = load_nouns_for_exercises(1)
        preps = load_prepositions(1)
        adverbs = []
        noun_prep_map = _generate_fallback_mapping(nouns, preps)

        exercise = await generate_where_is_x_exercise(nouns, preps, adverbs, noun_prep_map)

        assert exercise is None


class TestGenerateXIsPrepYExercise:
    @pytest.mark.asyncio
    async def test_generate_x_is_prep_y_returns_exercise(self):
        nouns = load_nouns_for_exercises(1)
        preps = load_prepositions(1)
        noun_prep_map = _generate_fallback_mapping(nouns, preps)

        exercise = await generate_x_is_prep_y_exercise(nouns, preps, noun_prep_map)

        if exercise is not None:
            assert exercise.pattern == "x_is_prep_y"
            assert exercise.hebrew
            assert exercise.transliteration
            assert exercise.english

    @pytest.mark.asyncio
    async def test_generate_x_is_prep_y_has_components(self):
        nouns = load_nouns_for_exercises(1)
        preps = load_prepositions(1)
        noun_prep_map = _generate_fallback_mapping(nouns, preps)

        exercise = await generate_x_is_prep_y_exercise(nouns, preps, noun_prep_map)

        if exercise is not None:
            assert "noun1" in exercise.components
            assert "noun2" in exercise.components
            assert "preposition" in exercise.components


class TestGenerateXAndYArePrepZExercise:
    @pytest.mark.asyncio
    async def test_generate_x_and_y_are_prep_z_returns_exercise(self):
        nouns = load_nouns_for_exercises(2)
        preps = load_prepositions(1)
        conjs = load_conjunctions(1)
        noun_prep_map = _generate_fallback_mapping(nouns, preps)

        exercise = await generate_x_and_y_are_prep_z_exercise(
            nouns, preps, conjs, noun_prep_map
        )

        if exercise is not None:
            assert exercise.pattern == "x_and_y_are_prep_z"
            assert "וְ" in exercise.hebrew or "wə" in exercise.transliteration
            assert "and" in exercise.english.lower()

    @pytest.mark.asyncio
    async def test_generate_x_and_y_are_prep_z_returns_none_without_conjunction(self):
        nouns = load_nouns_for_exercises(2)
        preps = load_prepositions(1)
        conjs = []
        noun_prep_map = _generate_fallback_mapping(nouns, preps)

        exercise = await generate_x_and_y_are_prep_z_exercise(
            nouns, preps, conjs, noun_prep_map
        )

        assert exercise is None


class TestGenerateSentenceExercises:
    @pytest.mark.asyncio
    async def test_generate_sentence_exercises_returns_list(self):
        exercises = await generate_sentence_exercises(max_lesson=1, count=5)

        assert isinstance(exercises, list)

    @pytest.mark.asyncio
    async def test_generate_sentence_exercises_respects_count(self):
        exercises = await generate_sentence_exercises(max_lesson=1, count=3)

        assert len(exercises) <= 3

    @pytest.mark.asyncio
    async def test_generate_sentence_exercises_with_patterns_filter(self):
        exercises = await generate_sentence_exercises(
            max_lesson=1,
            count=5,
            patterns=["x_is_prep_y"],
        )

        for ex in exercises:
            assert ex.pattern == "x_is_prep_y"

    @pytest.mark.asyncio
    async def test_generate_sentence_exercises_lesson_2(self):
        exercises = await generate_sentence_exercises(max_lesson=2, count=5)

        assert isinstance(exercises, list)

    @pytest.mark.asyncio
    async def test_generate_sentence_exercises_lesson_3(self):
        exercises = await generate_sentence_exercises(max_lesson=3, count=5)

        assert isinstance(exercises, list)


class TestSentenceExerciseStructure:
    @pytest.mark.asyncio
    async def test_exercise_has_required_fields(self):
        exercises = await generate_sentence_exercises(max_lesson=1, count=3)

        for ex in exercises:
            assert isinstance(ex, SentenceExercise)
            assert ex.pattern in ["where_is_x", "x_is_prep_y", "x_and_y_are_prep_z"]
            assert ex.hebrew
            assert ex.transliteration
            assert ex.english
            assert isinstance(ex.components, dict)

    @pytest.mark.asyncio
    async def test_exercise_hebrew_ends_with_period(self):
        exercises = await generate_sentence_exercises(max_lesson=1, count=3)

        for ex in exercises:
            assert ex.hebrew.rstrip().endswith(".")

    @pytest.mark.asyncio
    async def test_exercise_english_ends_with_period(self):
        exercises = await generate_sentence_exercises(max_lesson=1, count=3)

        for ex in exercises:
            assert ex.english.rstrip().endswith(".")
