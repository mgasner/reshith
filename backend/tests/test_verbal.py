"""Tests for Hebrew-to-English verbal sentence exercise generation."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from reshith.exercises.article import Noun, load_nouns_for_exercises
from reshith.exercises.sentences import Preposition, load_prepositions
from reshith.exercises.verbal import (
    CACHE_DIR,
    Verb,
    VerbalExercise,
    VerbalGradeResult,
    _generate_fallback_verb_mappings,
    _get_english_noun,
    _get_english_prep,
    _get_english_verb,
    _get_verb_cache_key,
    _get_verb_cache_path,
    generate_subject_verb_exercise,
    generate_subject_verb_object_exercise,
    generate_subject_verb_object_prep_exercise,
    generate_subject_verb_prep_exercise,
    generate_verb_mappings,
    generate_verbal_exercises,
    grade_verbal_exercise,
    load_verbs,
    normalize_english_for_grading,
)


def make_verb(
    hebrew: str,
    transliteration: str,
    definition: str,
    lesson: int = 4,
) -> Verb:
    return Verb(
        hebrew=hebrew,
        transliteration=transliteration,
        definition=definition,
        lesson=lesson,
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


class TestLoadVerbs:
    def test_load_verbs_lesson_4(self):
        verbs = load_verbs(4)

        assert len(verbs) >= 5
        translits = [v.transliteration for v in verbs]
        assert "kōṯēḇ" in translits
        assert "yōšēḇ" in translits

    def test_load_verbs_lesson_3_returns_empty(self):
        verbs = load_verbs(3)

        assert len(verbs) == 0

    def test_verb_has_required_fields(self):
        verbs = load_verbs(4)

        for verb in verbs:
            assert verb.hebrew
            assert verb.transliteration
            assert verb.definition
            assert verb.lesson == 4


class TestNormalizeEnglishForGrading:
    def test_normalize_strips_whitespace(self):
        result = normalize_english_for_grading("  The man is writing.  ")
        assert result == "the man is writing"

    def test_normalize_lowercases(self):
        result = normalize_english_for_grading("The Man Is Writing.")
        assert result == "the man is writing"

    def test_normalize_removes_punctuation(self):
        result = normalize_english_for_grading("The man is writing.")
        assert result == "the man is writing"

    def test_normalize_removes_question_mark(self):
        result = normalize_english_for_grading("Where is the man?")
        assert result == "where is the man"

    def test_normalize_collapses_double_spaces(self):
        result = normalize_english_for_grading("The  man  is  writing")
        assert result == "the man is writing"


class TestFallbackVerbMappings:
    def test_generates_subjects(self):
        verbs = [make_verb("כֹּתֵב", "kōṯēḇ", "writing")]
        nouns = [
            make_noun("אִישׁ", "ʾîš", "man"),
            make_noun("בַּיִת", "báyit", "house"),
        ]
        preps = [make_preposition("בְּ", "bə", "in", is_inseparable=True)]

        mappings = _generate_fallback_verb_mappings(verbs, nouns, preps)

        assert "subjects" in mappings
        assert "kōṯēḇ" in mappings["subjects"]
        assert "ʾîš" in mappings["subjects"]["kōṯēḇ"]

    def test_generates_objects(self):
        verbs = [make_verb("כֹּתֵב", "kōṯēḇ", "writing")]
        nouns = [
            make_noun("אִישׁ", "ʾîš", "man"),
            make_noun("סֵפֶר", "sēp̄er", "book"),
        ]
        preps = [make_preposition("בְּ", "bə", "in", is_inseparable=True)]

        mappings = _generate_fallback_verb_mappings(verbs, nouns, preps)

        assert "objects" in mappings
        assert "kōṯēḇ" in mappings["objects"]

    def test_generates_prepositions(self):
        verbs = [make_verb("הֹלֵךְ", "hōlēḵ", "going")]
        nouns = [
            make_noun("אִישׁ", "ʾîš", "man"),
            make_noun("בַּיִת", "báyit", "house"),
        ]
        preps = [make_preposition("אֶל־", "ʾel-", "to, toward")]

        mappings = _generate_fallback_verb_mappings(verbs, nouns, preps)

        assert "prepositions" in mappings
        assert "hōlēḵ" in mappings["prepositions"]


class TestGenerateSubjectVerbExercise:
    @pytest.mark.asyncio
    async def test_returns_exercise(self):
        verbs = load_verbs(4)
        nouns = load_nouns_for_exercises(4)

        mappings = _generate_fallback_verb_mappings(verbs, nouns, [])

        exercise = await generate_subject_verb_exercise(verbs, nouns, mappings)

        if exercise is not None:
            assert exercise.pattern == "subject_verb"
            assert "The" in exercise.english_answer
            assert "is" in exercise.english_answer
            assert exercise.hebrew.endswith(".")

    @pytest.mark.asyncio
    async def test_exercise_has_components(self):
        verbs = load_verbs(4)
        nouns = load_nouns_for_exercises(4)
        mappings = _generate_fallback_verb_mappings(verbs, nouns, [])

        exercise = await generate_subject_verb_exercise(verbs, nouns, mappings)

        if exercise is not None:
            assert "subject" in exercise.components
            assert "verb" in exercise.components

    @pytest.mark.asyncio
    async def test_returns_none_with_empty_verbs(self):
        verbs: list[Verb] = []
        nouns = load_nouns_for_exercises(4)
        mappings: dict = {"subjects": {}, "objects": {}, "prepositions": {}}

        exercise = await generate_subject_verb_exercise(verbs, nouns, mappings)

        assert exercise is None


class TestGenerateSubjectVerbObjectExercise:
    @pytest.mark.asyncio
    async def test_returns_exercise(self):
        verbs = load_verbs(4)
        nouns = load_nouns_for_exercises(4)
        mappings = _generate_fallback_verb_mappings(verbs, nouns, [])

        exercise = await generate_subject_verb_object_exercise(verbs, nouns, mappings)

        if exercise is not None:
            assert exercise.pattern == "subject_verb_object"
            assert "אֶת־" in exercise.hebrew
            assert "ʾeṯ-" in exercise.transliteration

    @pytest.mark.asyncio
    async def test_exercise_has_components(self):
        verbs = load_verbs(4)
        nouns = load_nouns_for_exercises(4)
        mappings = _generate_fallback_verb_mappings(verbs, nouns, [])

        exercise = await generate_subject_verb_object_exercise(verbs, nouns, mappings)

        if exercise is not None:
            assert "subject" in exercise.components
            assert "verb" in exercise.components
            assert "object" in exercise.components


class TestGenerateSubjectVerbPrepExercise:
    @pytest.mark.asyncio
    async def test_returns_exercise(self):
        verbs = load_verbs(4)
        nouns = load_nouns_for_exercises(4)
        preps = load_prepositions(4)
        mappings = _generate_fallback_verb_mappings(verbs, nouns, preps)

        exercise = await generate_subject_verb_prep_exercise(verbs, nouns, preps, mappings)

        if exercise is not None:
            assert exercise.pattern == "subject_verb_prep"
            assert exercise.hebrew.endswith(".")

    @pytest.mark.asyncio
    async def test_exercise_has_components(self):
        verbs = load_verbs(4)
        nouns = load_nouns_for_exercises(4)
        preps = load_prepositions(4)
        mappings = _generate_fallback_verb_mappings(verbs, nouns, preps)

        exercise = await generate_subject_verb_prep_exercise(verbs, nouns, preps, mappings)

        if exercise is not None:
            assert "subject" in exercise.components
            assert "verb" in exercise.components
            assert "preposition" in exercise.components
            assert "prep_object" in exercise.components


class TestGenerateSubjectVerbObjectPrepExercise:
    @pytest.mark.asyncio
    async def test_returns_exercise(self):
        verbs = load_verbs(4)
        nouns = load_nouns_for_exercises(4)
        preps = load_prepositions(4)
        mappings = _generate_fallback_verb_mappings(verbs, nouns, preps)

        exercise = await generate_subject_verb_object_prep_exercise(verbs, nouns, preps, mappings)

        if exercise is not None:
            assert exercise.pattern == "subject_verb_object_prep"
            assert "אֶת־" in exercise.hebrew

    @pytest.mark.asyncio
    async def test_exercise_has_components(self):
        verbs = load_verbs(4)
        nouns = load_nouns_for_exercises(4)
        preps = load_prepositions(4)
        mappings = _generate_fallback_verb_mappings(verbs, nouns, preps)

        exercise = await generate_subject_verb_object_prep_exercise(verbs, nouns, preps, mappings)

        if exercise is not None:
            assert "subject" in exercise.components
            assert "verb" in exercise.components
            assert "object" in exercise.components
            assert "preposition" in exercise.components
            assert "prep_object" in exercise.components


class TestGenerateVerbalExercises:
    @pytest.mark.asyncio
    async def test_returns_list(self):
        exercises = await generate_verbal_exercises(max_lesson=4, count=5)

        assert isinstance(exercises, list)

    @pytest.mark.asyncio
    async def test_respects_count(self):
        exercises = await generate_verbal_exercises(max_lesson=4, count=3)

        assert len(exercises) <= 3

    @pytest.mark.asyncio
    async def test_with_patterns_filter(self):
        exercises = await generate_verbal_exercises(
            max_lesson=4,
            count=5,
            patterns=["subject_verb"],
        )

        for ex in exercises:
            assert ex.pattern == "subject_verb"

    @pytest.mark.asyncio
    async def test_returns_empty_for_lesson_3(self):
        exercises = await generate_verbal_exercises(max_lesson=3, count=5)

        assert exercises == []


class TestVerbalExerciseStructure:
    @pytest.mark.asyncio
    async def test_exercise_has_required_fields(self):
        exercises = await generate_verbal_exercises(max_lesson=4, count=3)

        for ex in exercises:
            assert isinstance(ex, VerbalExercise)
            assert ex.pattern in [
                "subject_verb",
                "subject_verb_object",
                "subject_verb_prep",
                "subject_verb_object_prep",
            ]
            assert ex.hebrew
            assert ex.transliteration
            assert ex.english_answer
            assert isinstance(ex.components, dict)

    @pytest.mark.asyncio
    async def test_exercise_english_is_proper_sentence(self):
        exercises = await generate_verbal_exercises(max_lesson=4, count=3)

        for ex in exercises:
            assert ex.english_answer[0].isupper()
            assert ex.english_answer.endswith(".")


class TestGradeVerbalExercise:
    def test_correct_answer(self):
        result = grade_verbal_exercise(
            submitted="The man is writing.",
            expected_english="The man is writing.",
        )

        assert result.correct is True
        assert result.score == 1.0
        assert result.feedback == "Correct!"

    def test_correct_without_punctuation(self):
        result = grade_verbal_exercise(
            submitted="The man is writing",
            expected_english="The man is writing.",
        )

        assert result.correct is True
        assert result.score == 1.0

    def test_correct_case_insensitive(self):
        result = grade_verbal_exercise(
            submitted="the man is writing",
            expected_english="The man is writing.",
        )

        assert result.correct is True
        assert result.score == 1.0

    def test_is_are_variation_accepted(self):
        result = grade_verbal_exercise(
            submitted="The men are writing.",
            expected_english="The men is writing.",
        )

        assert result.correct is True
        assert result.score == 1.0
        assert "variation" in result.feedback.lower()

    def test_almost_correct(self):
        result = grade_verbal_exercise(
            submitted="The man is reading.",
            expected_english="The man is writing.",
        )

        assert result.correct is False
        assert result.score == 0.8
        assert "Almost" in result.feedback

    def test_partially_correct(self):
        result = grade_verbal_exercise(
            submitted="The man is writing something.",
            expected_english="The man is writing.",
        )

        assert result.correct is False
        assert 0 < result.score < 1.0

    def test_completely_incorrect(self):
        result = grade_verbal_exercise(
            submitted="Hello world",
            expected_english="The man is writing.",
        )

        assert result.correct is False
        assert result.score < 0.5
        assert "Incorrect" in result.feedback


class TestGradeVerbalResult:
    def test_result_has_all_fields(self):
        result = grade_verbal_exercise(
            submitted="test",
            expected_english="expected",
        )

        assert isinstance(result, VerbalGradeResult)
        assert hasattr(result, "correct")
        assert hasattr(result, "score")
        assert hasattr(result, "expected")
        assert hasattr(result, "submitted")
        assert hasattr(result, "feedback")


class TestVerbDataclass:
    def test_verb_creation(self):
        verb = make_verb("כֹּתֵב", "kōṯēḇ", "writing", lesson=4)

        assert verb.hebrew == "כֹּתֵב"
        assert verb.transliteration == "kōṯēḇ"
        assert verb.definition == "writing"
        assert verb.lesson == 4

    def test_verb_default_lesson(self):
        verb = make_verb("כֹּתֵב", "kōṯēḇ", "writing")

        assert verb.lesson == 4


class TestVerbalExerciseDataclass:
    def test_verbal_exercise_creation(self):
        exercise = VerbalExercise(
            pattern="subject_verb",
            hebrew="הָאִישׁ כֹּתֵב.",
            transliteration="hāʾîš kōṯēḇ.",
            english_answer="The man is writing.",
            components={"subject": "אִישׁ", "verb": "כֹּתֵב"},
        )

        assert exercise.pattern == "subject_verb"
        assert exercise.hebrew == "הָאִישׁ כֹּתֵב."
        assert exercise.transliteration == "hāʾîš kōṯēḇ."
        assert exercise.english_answer == "The man is writing."
        assert exercise.components == {"subject": "אִישׁ", "verb": "כֹּתֵב"}


class TestLoadVerbsExtended:
    def test_load_verbs_lesson_1_returns_empty(self):
        verbs = load_verbs(1)
        assert len(verbs) == 0

    def test_load_verbs_lesson_2_returns_empty(self):
        verbs = load_verbs(2)
        assert len(verbs) == 0

    def test_load_verbs_all_lesson_4_verbs(self):
        verbs = load_verbs(4)
        translits = [v.transliteration for v in verbs]

        assert "kōṯēḇ" in translits
        assert "ʾōḵēl" in translits
        assert "nōṯēn" in translits
        assert "hōlēḵ" in translits
        assert "yōšēḇ" in translits

    def test_load_verbs_definitions(self):
        verbs = load_verbs(4)
        verb_dict = {v.transliteration: v.definition for v in verbs}

        assert "writing" in verb_dict.get("kōṯēḇ", "")
        assert "eating" in verb_dict.get("ʾōḵēl", "")
        assert "giving" in verb_dict.get("nōṯēn", "")
        assert "going" in verb_dict.get("hōlēḵ", "")
        assert "sitting" in verb_dict.get("yōšēḇ", "")


class TestEnglishExtraction:
    def test_get_english_verb_simple(self):
        verb = make_verb("כֹּתֵב", "kōṯēḇ", "writing")
        result = _get_english_verb(verb)
        assert result == "writing"

    def test_get_english_verb_with_comma(self):
        verb = make_verb("נֹתֵן", "nōṯēn", "giving, setting, placing")
        result = _get_english_verb(verb)
        assert result == "giving"

    def test_get_english_noun_simple(self):
        noun = make_noun("אִישׁ", "ʾîš", "man")
        result = _get_english_noun(noun)
        assert result == "man"

    def test_get_english_noun_with_comma(self):
        noun = make_noun("מַלְאָךְ", "malʾāḵ", "messenger, angel")
        result = _get_english_noun(noun)
        assert result == "messenger"

    def test_get_english_prep_simple(self):
        prep = make_preposition("בְּ", "bə", "in")
        result = _get_english_prep(prep)
        assert result == "in"

    def test_get_english_prep_with_comma(self):
        prep = make_preposition("אֶל־", "ʾel-", "to, toward")
        result = _get_english_prep(prep)
        assert result == "to"


class TestVerbCacheKey:
    def test_cache_key_is_deterministic(self):
        verbs = [make_verb("כֹּתֵב", "kōṯēḇ", "writing")]
        nouns = [make_noun("אִישׁ", "ʾîš", "man")]
        preps = [make_preposition("בְּ", "bə", "in")]

        key1 = _get_verb_cache_key(verbs, nouns, preps)
        key2 = _get_verb_cache_key(verbs, nouns, preps)

        assert key1 == key2

    def test_cache_key_changes_with_different_verbs(self):
        verbs1 = [make_verb("כֹּתֵב", "kōṯēḇ", "writing")]
        verbs2 = [make_verb("אֹכֵל", "ʾōḵēl", "eating")]
        nouns = [make_noun("אִישׁ", "ʾîš", "man")]
        preps = [make_preposition("בְּ", "bə", "in")]

        key1 = _get_verb_cache_key(verbs1, nouns, preps)
        key2 = _get_verb_cache_key(verbs2, nouns, preps)

        assert key1 != key2

    def test_cache_key_is_16_chars(self):
        verbs = [make_verb("כֹּתֵב", "kōṯēḇ", "writing")]
        nouns = [make_noun("אִישׁ", "ʾîš", "man")]
        preps = [make_preposition("בְּ", "bə", "in")]

        key = _get_verb_cache_key(verbs, nouns, preps)

        assert len(key) == 16

    def test_cache_path_uses_key(self):
        path = _get_verb_cache_path("abc123")

        assert "verb_map_abc123.json" in str(path)
        assert path.parent == CACHE_DIR


class TestGenerateVerbMappings:
    @pytest.mark.asyncio
    async def test_generates_mappings_without_api_key(self):
        verbs = load_verbs(4)
        nouns = load_nouns_for_exercises(4)
        preps = load_prepositions(4)

        with patch("reshith.exercises.verbal.get_settings") as mock_settings:
            mock_settings.return_value.openai_api_key = None
            mappings = await generate_verb_mappings(verbs, nouns, preps)

        assert "subjects" in mappings
        assert "objects" in mappings
        assert "prepositions" in mappings

    @pytest.mark.asyncio
    async def test_uses_cached_mappings(self):
        verbs = [make_verb("כֹּתֵב", "kōṯēḇ", "writing")]
        nouns = [make_noun("אִישׁ", "ʾîš", "man")]
        preps = [make_preposition("בְּ", "bə", "in")]

        cache_key = _get_verb_cache_key(verbs, nouns, preps)

        with tempfile.TemporaryDirectory() as tmpdir:
            test_cache_dir = Path(tmpdir)
            test_cache_path = test_cache_dir / f"verb_map_{cache_key}.json"
            test_cache_dir.mkdir(parents=True, exist_ok=True)

            cached_data = {
                "subjects": {"kōṯēḇ": ["ʾîš"]},
                "objects": {"kōṯēḇ": []},
                "prepositions": {"kōṯēḇ": {}},
            }
            with open(test_cache_path, "w") as f:
                json.dump(cached_data, f)

            with patch("reshith.exercises.verbal._get_verb_cache_path") as mock_path:
                mock_path.return_value = test_cache_path
                mappings = await generate_verb_mappings(verbs, nouns, preps)

            assert mappings == cached_data


class TestFallbackVerbMappingsExtended:
    def test_eating_verb_gets_food_objects(self):
        verbs = [make_verb("אֹכֵל", "ʾōḵēl", "eating")]
        nouns = [
            make_noun("אִישׁ", "ʾîš", "man"),
            make_noun("לֶחֶם", "léḥem", "bread, food"),
        ]
        preps = []

        mappings = _generate_fallback_verb_mappings(verbs, nouns, preps)

        assert "ʾōḵēl" in mappings["objects"]

    def test_giving_verb_gets_objects_and_locations(self):
        verbs = [make_verb("נֹתֵן", "nōṯēn", "giving")]
        nouns = [
            make_noun("אִישׁ", "ʾîš", "man"),
            make_noun("סֵפֶר", "sēp̄er", "book"),
            make_noun("בַּיִת", "báyit", "house"),
        ]
        preps = []

        mappings = _generate_fallback_verb_mappings(verbs, nouns, preps)

        assert "nōṯēn" in mappings["objects"]

    def test_going_verb_gets_location_prepositions(self):
        verbs = [make_verb("הֹלֵךְ", "hōlēḵ", "going")]
        nouns = [
            make_noun("אִישׁ", "ʾîš", "man"),
            make_noun("בַּיִת", "báyit", "house"),
        ]
        preps = [make_preposition("אֶל־", "ʾel-", "to, toward")]

        mappings = _generate_fallback_verb_mappings(verbs, nouns, preps)

        assert "ʾel-" in mappings["prepositions"]["hōlēḵ"]
        assert "báyit" in mappings["prepositions"]["hōlēḵ"]["ʾel-"]

    def test_excludes_direct_object_marker_from_prepositions(self):
        verbs = [make_verb("כֹּתֵב", "kōṯēḇ", "writing")]
        nouns = [make_noun("אִישׁ", "ʾîš", "man")]
        preps = [
            make_preposition("אֶת־", "ʾeṯ-", "direct object marker"),
            make_preposition("אֵת", "ʾēṯ", "direct object marker"),
            make_preposition("בְּ", "bə", "in"),
        ]

        mappings = _generate_fallback_verb_mappings(verbs, nouns, preps)

        assert "ʾeṯ-" not in mappings["prepositions"]["kōṯēḇ"]
        assert "ʾēṯ" not in mappings["prepositions"]["kōṯēḇ"]
        assert "bə" in mappings["prepositions"]["kōṯēḇ"]

    def test_all_verbs_get_animate_subjects(self):
        verbs = [
            make_verb("כֹּתֵב", "kōṯēḇ", "writing"),
            make_verb("אֹכֵל", "ʾōḵēl", "eating"),
        ]
        nouns = [
            make_noun("אִישׁ", "ʾîš", "man"),
            make_noun("אִשָּׁה", "ʾiššâ", "woman"),
            make_noun("בַּיִת", "báyit", "house"),
        ]
        preps = []

        mappings = _generate_fallback_verb_mappings(verbs, nouns, preps)

        for verb in verbs:
            assert "ʾîš" in mappings["subjects"][verb.transliteration]
            assert "ʾiššâ" in mappings["subjects"][verb.transliteration]


class TestGenerateSubjectVerbExerciseExtended:
    @pytest.mark.asyncio
    async def test_returns_none_with_empty_nouns(self):
        verbs = load_verbs(4)
        nouns: list[Noun] = []
        mappings = {"subjects": {}, "objects": {}, "prepositions": {}}

        exercise = await generate_subject_verb_exercise(verbs, nouns, mappings)

        assert exercise is None

    @pytest.mark.asyncio
    async def test_returns_none_with_empty_subjects_mapping(self):
        verbs = load_verbs(4)
        nouns = load_nouns_for_exercises(4)
        mappings = {"subjects": {}, "objects": {}, "prepositions": {}}

        exercise = await generate_subject_verb_exercise(verbs, nouns, mappings)

        assert exercise is None

    @pytest.mark.asyncio
    async def test_hebrew_has_definite_article(self):
        verbs = load_verbs(4)
        nouns = load_nouns_for_exercises(4)
        mappings = _generate_fallback_verb_mappings(verbs, nouns, [])

        exercise = await generate_subject_verb_exercise(verbs, nouns, mappings)

        if exercise is not None:
            assert "הַ" in exercise.hebrew or "הָ" in exercise.hebrew or "הֶ" in exercise.hebrew


class TestGenerateSubjectVerbObjectExerciseExtended:
    @pytest.mark.asyncio
    async def test_returns_none_with_empty_objects_mapping(self):
        verbs = load_verbs(4)
        nouns = load_nouns_for_exercises(4)
        mappings = {
            "subjects": {v.transliteration: [nouns[0].transliteration] for v in verbs},
            "objects": {},
            "prepositions": {},
        }

        exercise = await generate_subject_verb_object_exercise(verbs, nouns, mappings)

        assert exercise is None

    @pytest.mark.asyncio
    async def test_direct_object_marker_in_transliteration(self):
        verbs = load_verbs(4)
        nouns = load_nouns_for_exercises(4)
        mappings = _generate_fallback_verb_mappings(verbs, nouns, [])

        exercise = await generate_subject_verb_object_exercise(verbs, nouns, mappings)

        if exercise is not None:
            assert "ʾeṯ-" in exercise.transliteration


class TestGenerateSubjectVerbPrepExerciseExtended:
    @pytest.mark.asyncio
    async def test_returns_none_with_empty_preps(self):
        verbs = load_verbs(4)
        nouns = load_nouns_for_exercises(4)
        preps: list[Preposition] = []
        mappings = _generate_fallback_verb_mappings(verbs, nouns, preps)

        exercise = await generate_subject_verb_prep_exercise(verbs, nouns, preps, mappings)

        assert exercise is None

    @pytest.mark.asyncio
    async def test_returns_none_with_empty_prep_mapping(self):
        verbs = load_verbs(4)
        nouns = load_nouns_for_exercises(4)
        preps = load_prepositions(4)
        mappings = {
            "subjects": {v.transliteration: [nouns[0].transliteration] for v in verbs},
            "objects": {},
            "prepositions": {},
        }

        exercise = await generate_subject_verb_prep_exercise(verbs, nouns, preps, mappings)

        assert exercise is None


class TestGenerateVerbalExercisesExtended:
    @pytest.mark.asyncio
    async def test_with_multiple_patterns_filter(self):
        exercises = await generate_verbal_exercises(
            max_lesson=4,
            count=10,
            patterns=["subject_verb", "subject_verb_object"],
        )

        for ex in exercises:
            assert ex.pattern in ["subject_verb", "subject_verb_object"]

    @pytest.mark.asyncio
    async def test_with_custom_pattern_weights(self):
        exercises = await generate_verbal_exercises(
            max_lesson=4,
            count=20,
            patterns=["subject_verb"],
            pattern_weights={"subject_verb": 1.0},
        )

        for ex in exercises:
            assert ex.pattern == "subject_verb"

    @pytest.mark.asyncio
    async def test_returns_empty_for_lesson_1(self):
        exercises = await generate_verbal_exercises(max_lesson=1, count=5)
        assert exercises == []

    @pytest.mark.asyncio
    async def test_returns_empty_for_lesson_2(self):
        exercises = await generate_verbal_exercises(max_lesson=2, count=5)
        assert exercises == []

    @pytest.mark.asyncio
    async def test_generates_variety_of_patterns(self):
        exercises = await generate_verbal_exercises(max_lesson=4, count=20)

        patterns = set(ex.pattern for ex in exercises)
        assert len(patterns) >= 1

    @pytest.mark.asyncio
    async def test_all_exercises_have_hebrew_content(self):
        exercises = await generate_verbal_exercises(max_lesson=4, count=5)

        for ex in exercises:
            assert any(
                "\u05d0" <= c <= "\u05ea" for c in ex.hebrew
            )


class TestGradeVerbalExerciseExtended:
    def test_extra_whitespace_ignored(self):
        result = grade_verbal_exercise(
            submitted="The  man  is  writing.",
            expected_english="The man is writing.",
        )

        assert result.correct is True
        assert result.score == 1.0

    def test_exclamation_mark_removed(self):
        result = grade_verbal_exercise(
            submitted="The man is writing!",
            expected_english="The man is writing.",
        )

        assert result.correct is True
        assert result.score == 1.0

    def test_are_to_is_variation(self):
        result = grade_verbal_exercise(
            submitted="The man are writing.",
            expected_english="The man is writing.",
        )

        assert result.correct is True
        assert "variation" in result.feedback.lower()

    def test_wrong_verb_partial_credit(self):
        result = grade_verbal_exercise(
            submitted="The man is eating.",
            expected_english="The man is writing.",
        )

        assert result.correct is False
        assert result.score > 0

    def test_wrong_subject_partial_credit(self):
        result = grade_verbal_exercise(
            submitted="The woman is writing.",
            expected_english="The man is writing.",
        )

        assert result.correct is False
        assert result.score > 0

    def test_missing_article_partial_credit(self):
        result = grade_verbal_exercise(
            submitted="Man is writing.",
            expected_english="The man is writing.",
        )

        assert result.correct is False
        assert result.score > 0

    def test_completely_wrong_language(self):
        result = grade_verbal_exercise(
            submitted="הָאִישׁ כֹּתֵב",
            expected_english="The man is writing.",
        )

        assert result.correct is False
        assert result.score == 0.0

    def test_empty_submission(self):
        result = grade_verbal_exercise(
            submitted="",
            expected_english="The man is writing.",
        )

        assert result.correct is False
        assert result.score == 0.0

    def test_feedback_includes_expected(self):
        result = grade_verbal_exercise(
            submitted="wrong answer",
            expected_english="The man is writing.",
        )

        assert "The man is writing" in result.feedback

    def test_result_preserves_submitted(self):
        result = grade_verbal_exercise(
            submitted="my answer",
            expected_english="The man is writing.",
        )

        assert result.submitted == "my answer"

    def test_result_preserves_expected(self):
        result = grade_verbal_exercise(
            submitted="my answer",
            expected_english="The man is writing.",
        )

        assert result.expected == "The man is writing."


class TestNormalizeEnglishForGradingExtended:
    def test_normalize_removes_exclamation(self):
        result = normalize_english_for_grading("The man is writing!")
        assert result == "the man is writing"

    def test_normalize_handles_empty_string(self):
        result = normalize_english_for_grading("")
        assert result == ""

    def test_normalize_handles_only_whitespace(self):
        result = normalize_english_for_grading("   ")
        assert result == ""

    def test_normalize_handles_only_punctuation(self):
        result = normalize_english_for_grading("...")
        assert result == ""

    def test_normalize_preserves_apostrophes(self):
        result = normalize_english_for_grading("The man's writing.")
        assert "'" in result or result == "the mans writing"


class TestVerbalExerciseHebrewContent:
    @pytest.mark.asyncio
    async def test_subject_verb_has_two_words(self):
        exercises = await generate_verbal_exercises(
            max_lesson=4,
            count=5,
            patterns=["subject_verb"],
        )

        for ex in exercises:
            hebrew_words = ex.hebrew.rstrip(".").split()
            assert len(hebrew_words) >= 2

    @pytest.mark.asyncio
    async def test_subject_verb_object_has_direct_object_marker(self):
        exercises = await generate_verbal_exercises(
            max_lesson=4,
            count=5,
            patterns=["subject_verb_object"],
        )

        for ex in exercises:
            assert "אֶת־" in ex.hebrew

    @pytest.mark.asyncio
    async def test_transliteration_matches_hebrew_structure(self):
        exercises = await generate_verbal_exercises(max_lesson=4, count=5)

        for ex in exercises:
            hebrew_words = ex.hebrew.rstrip(".").split()
            translit_words = ex.transliteration.rstrip(".").split()
            assert len(hebrew_words) == len(translit_words)


class TestVerbalExerciseEnglishContent:
    @pytest.mark.asyncio
    async def test_english_starts_with_the(self):
        exercises = await generate_verbal_exercises(max_lesson=4, count=5)

        for ex in exercises:
            assert ex.english_answer.startswith("The ")

    @pytest.mark.asyncio
    async def test_english_contains_is(self):
        exercises = await generate_verbal_exercises(max_lesson=4, count=5)

        for ex in exercises:
            assert " is " in ex.english_answer

    @pytest.mark.asyncio
    async def test_english_ends_with_period(self):
        exercises = await generate_verbal_exercises(max_lesson=4, count=5)

        for ex in exercises:
            assert ex.english_answer.endswith(".")

    @pytest.mark.asyncio
    async def test_english_contains_verb_ing_form(self):
        exercises = await generate_verbal_exercises(max_lesson=4, count=5)

        verb_forms = ["writing", "eating", "giving", "going", "sitting", "walking", "dwelling"]
        for ex in exercises:
            assert any(verb in ex.english_answer.lower() for verb in verb_forms)
