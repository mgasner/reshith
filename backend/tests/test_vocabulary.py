"""Tests for vocabulary loading."""

from reshith.exercises.vocabulary import (
    get_available_lessons,
    get_categories,
    load_by_categories,
    load_by_category,
    load_lesson,
    load_lessons_up_to,
    load_nouns_up_to,
)


def test_load_lesson_1():
    items = load_lesson(1)
    assert len(items) > 0
    assert all(item.lesson == 1 for item in items)


def test_load_lesson_returns_empty_for_nonexistent():
    items = load_lesson(999)
    assert items == []


def test_load_lessons_up_to():
    items = load_lessons_up_to(1)
    assert len(items) > 0


def test_load_nouns_up_to():
    nouns = load_nouns_up_to(1)
    assert len(nouns) > 0
    assert all(noun.category == "nouns" for noun in nouns)


def test_get_available_lessons():
    lessons = get_available_lessons()
    assert 1 in lessons


def test_vocabulary_item_has_required_fields():
    items = load_lesson(1)
    for item in items:
        assert item.hebrew
        assert item.transliteration
        assert item.definition
        assert item.category
        assert item.lesson == 1


def test_load_lesson_2():
    items = load_lesson(2)
    assert len(items) == 14
    assert all(item.lesson == 2 for item in items)


def test_load_nouns_up_to_lesson_2():
    nouns = load_nouns_up_to(2)
    lesson_1_nouns = load_nouns_up_to(1)
    assert len(nouns) > len(lesson_1_nouns)


def test_lessons_combine_correctly():
    items_1 = load_lessons_up_to(1)
    items_2 = load_lessons_up_to(2)
    assert len(items_2) == len(items_1) + len(load_lesson(2))


class TestLesson3:
    def test_load_lesson_3(self):
        items = load_lesson(3)
        assert len(items) == 12
        assert all(item.lesson == 3 for item in items)

    def test_lesson_3_has_nouns(self):
        items = load_lesson(3)
        nouns = [i for i in items if i.category == "nouns"]
        assert len(nouns) == 6

    def test_lesson_3_has_adjectives(self):
        items = load_lesson(3)
        adjectives = [i for i in items if i.category == "adjectives"]
        assert len(adjectives) == 5

    def test_lesson_3_has_adverbs(self):
        items = load_lesson(3)
        adverbs = [i for i in items if i.category == "adverbs"]
        assert len(adverbs) == 1

    def test_load_nouns_up_to_lesson_3(self):
        nouns_2 = load_nouns_up_to(2)
        nouns_3 = load_nouns_up_to(3)
        assert len(nouns_3) > len(nouns_2)

    def test_lessons_1_to_3_combine_correctly(self):
        items_2 = load_lessons_up_to(2)
        items_3 = load_lessons_up_to(3)
        assert len(items_3) == len(items_2) + len(load_lesson(3))


class TestLoadByCategory:
    def test_load_by_category_nouns(self):
        nouns = load_by_category(1, "nouns")
        assert len(nouns) > 0
        assert all(item.category == "nouns" for item in nouns)

    def test_load_by_category_prepositions(self):
        preps = load_by_category(1, "prepositions")
        assert len(preps) > 0
        assert all(item.category == "prepositions" for item in preps)

    def test_load_by_category_adverbs(self):
        adverbs = load_by_category(1, "adverbs")
        assert len(adverbs) > 0
        assert all(item.category == "adverbs" for item in adverbs)

    def test_load_by_category_nonexistent(self):
        items = load_by_category(1, "nonexistent_category")
        assert items == []

    def test_load_by_category_adjectives_lesson_3(self):
        adjectives = load_by_category(3, "adjectives")
        assert len(adjectives) == 5
        assert all(item.category == "adjectives" for item in adjectives)


class TestLoadByCategories:
    def test_load_by_categories_single(self):
        items = load_by_categories(1, ["nouns"])
        assert len(items) > 0
        assert all(item.category == "nouns" for item in items)

    def test_load_by_categories_multiple(self):
        items = load_by_categories(1, ["nouns", "prepositions"])
        assert len(items) > 0
        categories = set(item.category for item in items)
        assert categories <= {"nouns", "prepositions"}

    def test_load_by_categories_all_lesson_1(self):
        items = load_by_categories(1, ["nouns", "prepositions", "adverbs", "conjunction"])
        all_items = load_lesson(1)
        assert len(items) == len(all_items)

    def test_load_by_categories_empty_list(self):
        items = load_by_categories(1, [])
        assert items == []


class TestGetCategories:
    def test_get_categories_lesson_1(self):
        categories = get_categories(1)
        assert "nouns" in categories
        assert "prepositions" in categories
        assert "adverbs" in categories
        assert "conjunction" in categories

    def test_get_categories_lesson_2(self):
        categories = get_categories(2)
        assert "nouns" in categories
        assert "pronouns" in categories

    def test_get_categories_lesson_3(self):
        categories = get_categories(3)
        assert "nouns" in categories
        assert "adjectives" in categories
        assert "adverbs" in categories

    def test_get_categories_returns_sorted(self):
        categories = get_categories(3)
        assert categories == sorted(categories)


class TestLesson4:
    def test_load_lesson_4(self):
        items = load_lesson(4)
        assert len(items) == 13
        assert all(item.lesson == 4 for item in items)

    def test_lesson_4_has_nouns(self):
        items = load_lesson(4)
        nouns = [i for i in items if i.category == "nouns"]
        assert len(nouns) == 3

    def test_lesson_4_has_verbs(self):
        items = load_lesson(4)
        verbs = [i for i in items if i.category == "verbs"]
        assert len(verbs) == 5

    def test_lesson_4_has_prepositions(self):
        items = load_lesson(4)
        preps = [i for i in items if i.category == "prepositions"]
        assert len(preps) == 5

    def test_load_nouns_up_to_lesson_4(self):
        nouns_3 = load_nouns_up_to(3)
        nouns_4 = load_nouns_up_to(4)
        assert len(nouns_4) > len(nouns_3)

    def test_lessons_1_to_4_combine_correctly(self):
        items_3 = load_lessons_up_to(3)
        items_4 = load_lessons_up_to(4)
        assert len(items_4) == len(items_3) + len(load_lesson(4))

    def test_get_categories_lesson_4(self):
        categories = get_categories(4)
        assert "nouns" in categories
        assert "verbs" in categories
        assert "prepositions" in categories

    def test_load_by_category_verbs_lesson_4(self):
        verbs = load_by_category(4, "verbs")
        assert len(verbs) == 5
        assert all(item.category == "verbs" for item in verbs)


class TestLesson5:
    def test_load_lesson_5(self):
        items = load_lesson(5)
        assert len(items) == 15
        assert all(item.lesson == 5 for item in items)

    def test_lesson_5_has_nouns(self):
        items = load_lesson(5)
        nouns = [i for i in items if i.category == "nouns"]
        assert len(nouns) == 5
        translits = [n.transliteration for n in nouns]
        assert "zāhāḇ" in translits
        assert "ḥoḵmāh" in translits
        assert "késep̄" in translits

    def test_lesson_5_has_adjectives(self):
        items = load_lesson(5)
        adjs = [i for i in items if i.category == "adjectives"]
        assert len(adjs) == 5
        translits = [a.transliteration for a in adjs]
        assert "yāqār" in translits
        assert "ṣaddîq" in translits
        assert "rāšāʿ" in translits

    def test_lesson_5_has_proper_names(self):
        items = load_lesson(5)
        names = [i for i in items if i.category == "proper_names"]
        assert len(names) == 3
        translits = [n.transliteration for n in names]
        assert "Dāwid" in translits
        assert "šəmûʾēl" in translits
        assert "Yərûšālaim" in translits

    def test_lesson_5_has_other(self):
        items = load_lesson(5)
        other = [i for i in items if i.category == "other"]
        assert len(other) == 2
        translits = [o.transliteration for o in other]
        assert "min-" in translits
        assert "ʾăšer" in translits

    def test_load_nouns_up_to_lesson_5(self):
        nouns_4 = load_nouns_up_to(4)
        nouns_5 = load_nouns_up_to(5)
        assert len(nouns_5) > len(nouns_4)
        assert len(nouns_5) == len(nouns_4) + 5

    def test_lessons_1_to_5_combine_correctly(self):
        items_4 = load_lessons_up_to(4)
        items_5 = load_lessons_up_to(5)
        assert len(items_5) == len(items_4) + len(load_lesson(5))

    def test_get_categories_lesson_5(self):
        categories = get_categories(5)
        assert "nouns" in categories
        assert "adjectives" in categories
        assert "proper_names" in categories
        assert "other" in categories

    def test_load_by_category_adjectives_lesson_5(self):
        adjs = load_by_category(5, "adjectives")
        assert len(adjs) >= 5
        assert all(item.category == "adjectives" for item in adjs)

    def test_load_by_category_proper_names_lesson_5(self):
        names = load_by_category(5, "proper_names")
        assert len(names) == 3
        assert all(item.category == "proper_names" for item in names)

    def test_jerusalem_has_notes(self):
        items = load_lesson(5)
        jerusalem = next(
            (i for i in items if i.transliteration == "Yərûšālaim"), None
        )
        assert jerusalem is not None
        assert jerusalem.notes is not None
        assert "spelling" in jerusalem.notes.lower()
