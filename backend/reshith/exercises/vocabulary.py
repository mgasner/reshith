"""
Vocabulary loader for exercises.

Loads vocabulary from lesson JSON files to use in exercises.
"""

import json
from dataclasses import dataclass
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "hebrew"


@dataclass
class VocabularyItem:
    hebrew: str
    transliteration: str
    definition: str
    category: str
    lesson: int
    notes: str | None = None


def load_lesson(lesson_num: int) -> list[VocabularyItem]:
    """Load vocabulary from a specific lesson."""
    lesson_path = DATA_DIR / f"lesson{lesson_num:02d}.json"

    if not lesson_path.exists():
        return []

    with open(lesson_path, encoding="utf-8") as f:
        data = json.load(f)

    items = []
    for card in data.get("cards", []):
        items.append(
            VocabularyItem(
                hebrew=card["hebrew"],
                transliteration=card["transliteration"],
                definition=card["definition"],
                category=card.get("category", "unknown"),
                lesson=lesson_num,
                notes=card.get("notes"),
            )
        )
    return items


def load_lessons_up_to(max_lesson: int) -> list[VocabularyItem]:
    """Load vocabulary from lesson 1 up to and including max_lesson."""
    items = []
    for lesson_num in range(1, max_lesson + 1):
        items.extend(load_lesson(lesson_num))
    return items


def load_nouns_up_to(max_lesson: int) -> list[VocabularyItem]:
    """Load only nouns from lesson 1 up to and including max_lesson."""
    all_items = load_lessons_up_to(max_lesson)
    return [item for item in all_items if item.category == "nouns"]


def load_verbs_up_to(max_lesson: int) -> list[VocabularyItem]:
    """Load only verbs from lesson 1 up to and including max_lesson."""
    all_items = load_lessons_up_to(max_lesson)
    return [item for item in all_items if item.category == "verbs"]


def load_by_category(max_lesson: int, category: str) -> list[VocabularyItem]:
    """Load vocabulary items of a specific category up to max_lesson."""
    all_items = load_lessons_up_to(max_lesson)
    return [item for item in all_items if item.category == category]


def load_by_categories(max_lesson: int, categories: list[str]) -> list[VocabularyItem]:
    """Load vocabulary items matching any of the given categories up to max_lesson."""
    all_items = load_lessons_up_to(max_lesson)
    return [item for item in all_items if item.category in categories]


def get_categories(max_lesson: int) -> list[str]:
    """Get all unique categories in vocabulary up to max_lesson."""
    all_items = load_lessons_up_to(max_lesson)
    return sorted(set(item.category for item in all_items))


def get_available_lessons() -> list[int]:
    """Get list of available lesson numbers."""
    lessons = []
    for path in DATA_DIR.glob("lesson*.json"):
        try:
            num = int(path.stem.replace("lesson", ""))
            lessons.append(num)
        except ValueError:
            continue
    return sorted(lessons)


def load_adjectives_up_to(max_lesson: int) -> list[VocabularyItem]:
    """Load only adjectives from lesson 1 up to and including max_lesson."""
    all_items = load_lessons_up_to(max_lesson)
    return [item for item in all_items if item.category == "adjectives"]


def load_proper_names_up_to(max_lesson: int) -> list[VocabularyItem]:
    """Load only proper names from lesson 1 up to and including max_lesson."""
    all_items = load_lessons_up_to(max_lesson)
    return [item for item in all_items if item.category == "proper_names"]
