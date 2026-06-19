"""Language-agnostic vocabulary loading.

Wraps the per-language loaders so the rest of the system (primary deck
seeding, SRS-weighted sampler, lesson-progress mastery calc) can ask for
"all vocab for language L up to lesson N" without knowing about the
per-language dataclasses.
"""

from pathlib import Path

from reshith.db import models
from reshith.exercises import vocabulary as hebrew_vocab
from reshith.exercises.greek import vocabulary as greek_vocab
from reshith.exercises.latin import vocabulary as latin_vocab
from reshith.exercises.sanskrit import vocabulary as sanskrit_vocab
from reshith.services.primary_deck import VocabSeed

_DATA_BASE = Path(__file__).parent.parent.parent.parent / "data"


def load_vocab(language: models.LanguageCode, max_lesson: int) -> list[VocabSeed]:
    """Load all lesson vocab for ``language`` through ``max_lesson``."""
    if language == models.LanguageCode.BIBLICAL_HEBREW:
        items = hebrew_vocab.load_lessons_up_to(max_lesson)
        return [
            VocabSeed(
                lemma=i.hebrew,
                definition=i.definition,
                transliteration=i.transliteration,
                category=i.category,
                lesson=i.lesson,
                notes=i.notes,
            )
            for i in items
        ]
    if language in (models.LanguageCode.LATIN, models.LanguageCode.ECCLESIASTICAL_LATIN):
        variant = "lat" if language == models.LanguageCode.LATIN else "ecl"
        items = latin_vocab.load_lessons_up_to(max_lesson, variant=variant)
        return [
            VocabSeed(
                lemma=i.word,
                definition=i.definition,
                transliteration=i.transliteration,
                category=i.category,
                lesson=i.lesson,
            )
            for i in items
        ]
    if language in (models.LanguageCode.ANCIENT_GREEK, models.LanguageCode.NT_GREEK):
        variant = "grc" if language == models.LanguageCode.ANCIENT_GREEK else "gnt"
        items = greek_vocab.load_lessons_up_to(max_lesson, variant=variant)
        return [
            VocabSeed(
                lemma=i.word,
                definition=i.definition,
                transliteration=i.transliteration,
                category=i.category,
                lesson=i.lesson,
            )
            for i in items
        ]
    if language == models.LanguageCode.SANSKRIT:
        items = sanskrit_vocab.load_lessons_up_to(max_lesson)
        return [
            VocabSeed(
                lemma=i.word,
                definition=i.definition,
                transliteration=i.transliteration,
                category=i.category,
                lesson=i.lesson,
            )
            for i in items
        ]
    return []


LESSON_DIRS: dict[models.LanguageCode, str] = {
    models.LanguageCode.BIBLICAL_HEBREW: "hebrew",
    models.LanguageCode.LATIN: "latin",
    models.LanguageCode.ECCLESIASTICAL_LATIN: "ecclesiastical_latin",
    models.LanguageCode.ANCIENT_GREEK: "greek",
    models.LanguageCode.NT_GREEK: "nt_greek",
    models.LanguageCode.SANSKRIT: "sanskrit",
}


def supported_languages() -> list[models.LanguageCode]:
    """Languages with at least one lesson JSON file on disk."""
    return [lang for lang in LESSON_DIRS if total_lessons(lang) > 0]


def total_lessons(language: models.LanguageCode) -> int:
    """Number of lesson JSON files present for ``language``."""
    dirname = LESSON_DIRS.get(language)
    if not dirname:
        return 0
    lesson_dir = _DATA_BASE / dirname
    if not lesson_dir.exists():
        return 0
    nums = []
    for p in lesson_dir.glob("lesson*.json"):
        try:
            nums.append(int(p.stem.replace("lesson", "")))
        except ValueError:
            continue
    return max(nums, default=0)
