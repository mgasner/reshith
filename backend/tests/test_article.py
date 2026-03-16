"""Tests for definite article exercise generation and grading."""


from reshith.exercises.article import (
    ArticleType,
    Noun,
    add_definite_article,
    create_article_exercise,
    generate_article_exercises,
    generate_article_phrase,
    grade_definite_to_indefinite,
    grade_indefinite_to_definite,
    load_nouns_for_exercises,
    normalize_hebrew,
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


class TestNounProperties:
    def test_first_consonant_bayit(self):
        noun = make_noun("בַּיִת", "báyit", "house")
        assert noun.first_consonant == "ב"

    def test_first_consonant_nahar(self):
        noun = make_noun("נָהָר", "nāhār", "river")
        assert noun.first_consonant == "נ"

    def test_is_guttural_initial_aleph(self):
        noun = make_noun("אִישׁ", "ʾîš", "man")
        assert noun.is_guttural_initial is True

    def test_is_guttural_initial_ayin(self):
        noun = make_noun("עֶבֶד", "ʿébed", "servant")
        assert noun.is_guttural_initial is True

    def test_is_guttural_initial_het(self):
        noun = make_noun("חֶרֶב", "ḥéreb", "sword")
        assert noun.is_guttural_initial is True

    def test_is_guttural_initial_he(self):
        noun = make_noun("הֵיכָל", "hêḵāl", "palace")
        assert noun.is_guttural_initial is True

    def test_is_not_guttural_initial(self):
        noun = make_noun("בַּיִת", "báyit", "house")
        assert noun.is_guttural_initial is False

    def test_is_resh_initial(self):
        noun = make_noun("רֹאשׁ", "rōʾš", "head")
        assert noun.is_resh_initial is True

    def test_is_not_resh_initial(self):
        noun = make_noun("בַּיִת", "báyit", "house")
        assert noun.is_resh_initial is False

    def test_first_vowel_patah(self):
        noun = make_noun("בַּיִת", "báyit", "house")
        assert noun.first_vowel == "\u05B7"

    def test_has_qamets_or_patah_true(self):
        noun = make_noun("נָהָר", "nāhār", "river")
        assert noun.has_qamets_or_patah is True

    def test_has_qamets_or_patah_false(self):
        noun = make_noun("סֵפֶר", "sēper", "book")
        assert noun.has_qamets_or_patah is False


class TestDefiniteArticleRegular:
    """Test regular article הַ + dagesh before non-gutturals."""

    def test_article_bayit(self):
        """Test הַ + בַּיִת = הַבַּיִת (the house)"""
        noun = make_noun("בַּיִת", "báyit", "house")
        hebrew, trans, article_type = add_definite_article(noun)

        assert article_type == ArticleType.REGULAR
        assert hebrew.startswith("הַ")
        assert trans == "habáyit"

    def test_article_nahar(self):
        """Test הַ + נָהָר = הַנָּהָר (the river)"""
        noun = make_noun("נָהָר", "nāhār", "river")
        hebrew, trans, article_type = add_definite_article(noun)

        assert article_type == ArticleType.REGULAR
        assert hebrew.startswith("הַ")
        assert trans == "hanāhār"

    def test_article_sefer(self):
        """Test הַ + סֵפֶר = הַסֵּפֶר (the book)"""
        noun = make_noun("סֵפֶר", "sēper", "book")
        hebrew, trans, article_type = add_definite_article(noun)

        assert article_type == ArticleType.REGULAR
        assert hebrew.startswith("הַ")
        assert trans == "hasēper"

    def test_article_melek(self):
        """Test הַ + מֶלֶךְ = הַמֶּלֶךְ (the king)"""
        noun = make_noun("מֶלֶךְ", "méleḵ", "king")
        hebrew, trans, article_type = add_definite_article(noun)

        assert article_type == ArticleType.REGULAR
        assert hebrew.startswith("הַ")
        assert trans == "haméleḵ"


class TestDefiniteArticleGuttural:
    """Test article before gutturals with compensatory lengthening."""

    def test_article_ish_aleph(self):
        """Test הָ before א - הָאִישׁ (the man)"""
        noun = make_noun("אִישׁ", "ʾîš", "man")
        hebrew, trans, article_type = add_definite_article(noun)

        assert article_type == ArticleType.GUTTURAL_COMPENSATORY
        assert hebrew.startswith("הָ")
        assert trans == "hāʾîš"

    def test_article_ebed_ayin(self):
        """Test before ע with segol"""
        noun = make_noun("עֶבֶד", "ʿébed", "servant")
        hebrew, trans, article_type = add_definite_article(noun)

        assert hebrew.startswith("הָ") or hebrew.startswith("הֶ")

    def test_article_hekal_he(self):
        """Test before ה"""
        noun = make_noun("הֵיכָל", "hêḵāl", "palace")
        hebrew, trans, article_type = add_definite_article(noun)

        assert hebrew.startswith("הָ") or hebrew.startswith("הַ")


class TestDefiniteArticleResh:
    """Test article before resh."""

    def test_article_rosh(self):
        """Test הָ before ר - הָרֹאשׁ (the head)"""
        noun = make_noun("רֹאשׁ", "rōʾš", "head")
        hebrew, trans, article_type = add_definite_article(noun)

        assert article_type == ArticleType.GUTTURAL_COMPENSATORY
        assert hebrew.startswith("הָ")
        assert trans == "hārōʾš"


class TestArticlePhraseGeneration:
    def test_generate_article_phrase(self):
        noun = make_noun("בַּיִת", "báyit", "house")
        phrase = generate_article_phrase(noun)

        assert phrase.noun == noun
        assert phrase.hebrew_indefinite == "בַּיִת"
        assert phrase.hebrew_definite.startswith("הַ")
        assert phrase.transliteration_indefinite == "báyit"
        assert phrase.transliteration_definite.startswith("ha")
        assert "house" in phrase.english_indefinite.lower()
        assert "house" in phrase.english_definite.lower()
        assert "the" in phrase.english_definite.lower()

    def test_generate_article_phrase_english_format(self):
        noun = make_noun("נָהָר", "nāhār", "river")
        phrase = generate_article_phrase(noun)

        assert phrase.english_indefinite == "a river"
        assert phrase.english_definite == "the river"


class TestArticleExerciseGeneration:
    def test_generate_article_exercises_count(self):
        exercises = generate_article_exercises(max_lesson=1, count=5)
        assert len(exercises) == 5

    def test_generate_article_exercises_has_required_fields(self):
        exercises = generate_article_exercises(max_lesson=1, count=3)

        for phrase in exercises:
            assert phrase.hebrew_indefinite
            assert phrase.hebrew_definite
            assert phrase.transliteration_indefinite
            assert phrase.transliteration_definite
            assert phrase.english_indefinite
            assert phrase.english_definite
            assert phrase.article_type is not None

    def test_generate_article_exercises_lesson_2(self):
        exercises = generate_article_exercises(max_lesson=2, count=5)
        assert len(exercises) == 5

    def test_generate_article_exercises_lesson_3(self):
        exercises = generate_article_exercises(max_lesson=3, count=5)
        assert len(exercises) == 5


class TestArticleExerciseCreation:
    def test_create_indefinite_to_definite_exercise(self):
        noun = make_noun("בַּיִת", "báyit", "house")
        phrase = generate_article_phrase(noun)

        exercise = create_article_exercise(phrase, "indefinite_to_definite")

        assert exercise.direction == "indefinite_to_definite"
        assert exercise.prompt == phrase.hebrew_indefinite
        assert exercise.answer == phrase.hebrew_definite
        assert exercise.prompt_transliteration == phrase.transliteration_indefinite
        assert exercise.answer_transliteration == phrase.transliteration_definite

    def test_create_definite_to_indefinite_exercise(self):
        noun = make_noun("בַּיִת", "báyit", "house")
        phrase = generate_article_phrase(noun)

        exercise = create_article_exercise(phrase, "definite_to_indefinite")

        assert exercise.direction == "definite_to_indefinite"
        assert exercise.prompt == phrase.hebrew_definite
        assert exercise.answer == phrase.hebrew_indefinite


class TestArticleGrading:
    def test_grade_indefinite_to_definite_correct(self):
        noun = make_noun("בַּיִת", "báyit", "house")
        phrase = generate_article_phrase(noun)

        result = grade_indefinite_to_definite(phrase, phrase.hebrew_definite)

        assert result.correct is True
        assert result.feedback == "Correct!"

    def test_grade_indefinite_to_definite_incorrect(self):
        noun = make_noun("בַּיִת", "báyit", "house")
        phrase = generate_article_phrase(noun)

        result = grade_indefinite_to_definite(phrase, "בַּיִת")

        assert result.correct is False
        assert "Expected" in result.feedback

    def test_grade_definite_to_indefinite_correct(self):
        noun = make_noun("נָהָר", "nāhār", "river")
        phrase = generate_article_phrase(noun)

        result = grade_definite_to_indefinite(phrase, phrase.hebrew_indefinite)

        assert result.correct is True

    def test_grade_definite_to_indefinite_incorrect(self):
        noun = make_noun("נָהָר", "nāhār", "river")
        phrase = generate_article_phrase(noun)

        result = grade_definite_to_indefinite(phrase, phrase.hebrew_definite)

        assert result.correct is False


class TestNormalizeHebrew:
    def test_normalize_removes_cantillation(self):
        text_with_cantillation = "בְּרֵאשִׁ֖ית"
        result = normalize_hebrew(text_with_cantillation)
        assert "\u0596" not in result

    def test_normalize_preserves_vowels(self):
        text = "בְּרֵאשִׁית"
        result = normalize_hebrew(text)
        assert "\u05B0" in result or "\u05B5" in result

    def test_normalize_strips_whitespace(self):
        text = "  בַּיִת  "
        result = normalize_hebrew(text)
        assert result == "בַּיִת"


class TestLoadNounsForExercises:
    def test_load_nouns_lesson_1(self):
        nouns = load_nouns_for_exercises(1)
        assert len(nouns) > 0
        assert all(isinstance(n, Noun) for n in nouns)

    def test_load_nouns_lesson_2(self):
        nouns = load_nouns_for_exercises(2)
        nouns_1 = load_nouns_for_exercises(1)
        assert len(nouns) >= len(nouns_1)

    def test_load_nouns_lesson_3(self):
        nouns = load_nouns_for_exercises(3)
        nouns_2 = load_nouns_for_exercises(2)
        assert len(nouns) >= len(nouns_2)

    def test_loaded_nouns_have_required_fields(self):
        nouns = load_nouns_for_exercises(1)
        for noun in nouns:
            assert noun.hebrew
            assert noun.transliteration
            assert noun.definition
            assert noun.category == "nouns"
            assert noun.lesson >= 1
