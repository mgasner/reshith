"""Tests for preposition exercise generation and grading."""

from reshith.exercises.prepositions import (
    Noun,
    Preposition,
    create_exercise,
    generate_exercises,
    generate_phrase,
    get_preposition_hebrew,
    get_preposition_transliteration,
    grade_english_to_hebrew,
    grade_exercise,
    grade_hebrew_to_english,
)


def make_noun(hebrew: str, transliteration: str, definition: str) -> Noun:
    return Noun(
        hebrew=hebrew,
        transliteration=transliteration,
        definition=definition,
        category="nouns",
    )


class TestPrepositionPrefixing:
    def test_be_with_bayit(self):
        """Test בְּ + בַּיִת = בְּבַיִת (in a house)"""
        noun = make_noun("בַּיִת", "báyit", "house")
        result = get_preposition_hebrew(Preposition.BE, noun)
        assert result == "בְּבַּיִת"

    def test_le_with_nahar(self):
        """Test לְ + נָהָר = לְנָהָר (to a river)"""
        noun = make_noun("נָהָר", "nāhār", "river")
        result = get_preposition_hebrew(Preposition.LE, noun)
        assert result == "לְנָהָר"

    def test_ke_with_zaqen(self):
        """Test כְּ + זָקֵן = כְּזָקֵן (like an elder)"""
        noun = make_noun("זָקֵן", "zāqēn", "old man, elder")
        result = get_preposition_hebrew(Preposition.KE, noun)
        assert result == "כְּזָקֵן"

    def test_le_with_sadeh(self):
        """Test לְ + שָׂדֶה = לְשָׂדֶה (to a field)"""
        noun = make_noun("שָׂדֶה", "śādeh", "field")
        result = get_preposition_hebrew(Preposition.LE, noun)
        assert result == "לְשָׂדֶה"


class TestTransliteration:
    def test_be_bayit_transliteration(self):
        noun = make_noun("בַּיִת", "báyit", "house")
        result = get_preposition_transliteration(Preposition.BE, noun)
        assert result == "bəbáyit"

    def test_le_nahar_transliteration(self):
        noun = make_noun("נָהָר", "nāhār", "river")
        result = get_preposition_transliteration(Preposition.LE, noun)
        assert result == "lənāhār"

    def test_ke_zaqen_transliteration(self):
        noun = make_noun("זָקֵן", "zāqēn", "old man")
        result = get_preposition_transliteration(Preposition.KE, noun)
        assert result == "kəzāqēn"


class TestPhraseGeneration:
    def test_generate_phrase_creates_valid_phrase(self):
        noun = make_noun("בַּיִת", "báyit", "house")
        phrase = generate_phrase(Preposition.BE, noun)

        assert phrase.preposition == Preposition.BE
        assert phrase.noun == noun
        assert "בְּ" in phrase.hebrew or "בִּ" in phrase.hebrew
        assert phrase.english.startswith("in")

    def test_generate_exercises_returns_correct_count(self):
        nouns = [
            make_noun("בַּיִת", "báyit", "house"),
            make_noun("נָהָר", "nāhār", "river"),
            make_noun("שָׂדֶה", "śādeh", "field"),
        ]
        exercises = generate_exercises(nouns, count=5)
        assert len(exercises) == 5


class TestGrading:
    def test_grade_hebrew_to_english_correct(self):
        noun = make_noun("בַּיִת", "báyit", "house")
        phrase = generate_phrase(Preposition.BE, noun)

        result = grade_hebrew_to_english(phrase, "in a house")
        assert result.correct is True

    def test_grade_hebrew_to_english_accepts_variations(self):
        noun = make_noun("בַּיִת", "báyit", "house")
        phrase = generate_phrase(Preposition.BE, noun)

        result = grade_hebrew_to_english(phrase, "in the house")
        assert result.correct is True

        result = grade_hebrew_to_english(phrase, "with a house")
        assert result.correct is True

    def test_grade_hebrew_to_english_incorrect(self):
        noun = make_noun("בַּיִת", "báyit", "house")
        phrase = generate_phrase(Preposition.BE, noun)

        result = grade_hebrew_to_english(phrase, "to a river")
        assert result.correct is False

    def test_grade_english_to_hebrew_correct(self):
        noun = make_noun("נָהָר", "nāhār", "river")
        phrase = generate_phrase(Preposition.LE, noun)

        result = grade_english_to_hebrew(phrase, phrase.hebrew)
        assert result.correct is True

    def test_grade_english_to_hebrew_incorrect(self):
        noun = make_noun("נָהָר", "nāhār", "river")
        phrase = generate_phrase(Preposition.LE, noun)

        result = grade_english_to_hebrew(phrase, "בְּנָהָר")
        assert result.correct is False


class TestExerciseCreation:
    def test_create_hebrew_to_english_exercise(self):
        noun = make_noun("בַּיִת", "báyit", "house")
        phrase = generate_phrase(Preposition.BE, noun)

        exercise = create_exercise(phrase, "hebrew_to_english")
        assert exercise.prompt == phrase.hebrew
        assert exercise.answer == phrase.english
        assert exercise.direction == "hebrew_to_english"

    def test_create_english_to_hebrew_exercise(self):
        noun = make_noun("בַּיִת", "báyit", "house")
        phrase = generate_phrase(Preposition.BE, noun)

        exercise = create_exercise(phrase, "english_to_hebrew")
        assert exercise.prompt == phrase.english
        assert exercise.answer == phrase.hebrew
        assert exercise.direction == "english_to_hebrew"

    def test_grade_exercise_hebrew_to_english(self):
        noun = make_noun("שָׂדֶה", "śādeh", "field")
        phrase = generate_phrase(Preposition.KE, noun)
        exercise = create_exercise(phrase, "hebrew_to_english")

        result = grade_exercise(exercise, "like a field")
        assert result.correct is True

    def test_grade_exercise_english_to_hebrew(self):
        noun = make_noun("שָׂדֶה", "śādeh", "field")
        phrase = generate_phrase(Preposition.KE, noun)
        exercise = create_exercise(phrase, "english_to_hebrew")

        result = grade_exercise(exercise, phrase.hebrew)
        assert result.correct is True
