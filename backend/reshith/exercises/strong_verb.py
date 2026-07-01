"""
Rule-based strong-verb (regular triliteral) paradigm generator.

Biblical Hebrew regular verbs share a single vowel pattern per binyan. We
capture that pattern once as a *skeleton* derived from a fully vocalised
reference verb (שָׁמַר for Qal), de-lexicalise its three root consonants, and
re-project the skeleton onto an arbitrary set of three radicals.

Two deterministic Masoretic rules are then applied so the output matches the
printed paradigms:

* **Dagesh lene** — a begadkephat letter (בגדכפת) takes a hard-stop dagesh at
  the start of a word or after a *silent* shewa.
* **Spirantisation** — in transliteration, a begadkephat letter *without*
  dagesh lene is written as its fricative (ḇ ḡ ḏ ḵ p̄ ṯ).

The remaining Masoretic edge cases (a handful of cells where a shewa is treated
as vocal against the mechanical rule) are supplied per verb as explicit
``exceptions`` overrides. Everything the generator emits is checked against the
hand-verified reference verbs in ``tests/test_strong_verb.py``.

This module intentionally handles *strong* verbs only. Weak roots (I-nun,
III-he, hollow, geminate, guttural, …) deviate from the skeleton and must be
supplied as full explicit paradigms instead.
"""

from __future__ import annotations

import unicodedata

# ── Hebrew point constants ───────────────────────────────────────────────────

DAGESH = "\u05bc"
SHEWA = "\u05b0"
SHIN_DOT = "\u05c1"
SIN_DOT = "\u05c2"

# Long vowel marks whose (open) syllable makes a following shewa vocal.
_LONG_VOWEL_MARKS = {
    "\u05b8",  # qamats
    "\u05b5",  # tsere
    "\u05b9",  # holam
}

BEGADKEPHAT = set("בגדכפת")

_SIN = "\u05e9"  # base shin/sin letter


def _is_consonant(ch: str) -> bool:
    return "\u05d0" <= ch <= "\u05ea"


# ── Grapheme segmentation ────────────────────────────────────────────────────


def graphemes(text: str) -> list[str]:
    """Split vocalised Hebrew into consonant-plus-points clusters.

    Each returned string starts with one consonant letter and contains all the
    vowel points / dagesh / dots that follow it.
    """
    text = unicodedata.normalize("NFC", text)
    clusters: list[str] = []
    current = ""
    for ch in text:
        if _is_consonant(ch):
            if current:
                clusters.append(current)
            current = ch
        else:
            current += ch
    if current:
        clusters.append(current)
    return clusters


# ── Skeletonisation ──────────────────────────────────────────────────────────

# The reference verb whose vocalisation defines the strong-verb pattern.
_REFERENCE_ROOT = ("\u05e9", "\u05de", "\u05e8")  # שׁ מ ר (shin carries shin-dot)


def _skeletonize(form: str) -> str:
    """Replace the three reference radicals with @1/@2/@3 placeholders.

    Vowel points that belong to a radical stay in place; the shin-dot on the
    first radical is dropped (it is a property of the letter ש, not the slot).
    """
    out: list[str] = []
    for g in graphemes(form):
        base = g[0]
        points = g[1:].replace(SHIN_DOT, "").replace(SIN_DOT, "")
        if base == _REFERENCE_ROOT[0]:
            out.append("@1" + points)
        elif base == _REFERENCE_ROOT[1]:
            out.append("@2" + points)
        elif base == _REFERENCE_ROOT[2]:
            out.append("@3" + points)
        else:
            out.append(g)
    return "".join(out)


# ── Phonological rules ───────────────────────────────────────────────────────


def _shewa_is_vocal(clusters: list[str], i: int) -> bool:
    """Is the shewa under ``clusters[i]`` vocal (na) rather than silent (nach)?"""
    if i == 0:
        return True
    g = clusters[i]
    # A dagesh forte under the letter makes its shewa vocal.
    if DAGESH in g[1:]:
        return True
    prev = clusters[i - 1]
    # Second of two adjacent shewas is vocal.
    if SHEWA in prev[1:]:
        return True
    # Vocal after an open syllable with a long vowel.
    return any(m in prev[1:] for m in _LONG_VOWEL_MARKS)


def apply_dagesh_lene(form: str) -> str:
    """Insert dagesh lene into begadkephat letters where the Masora requires it."""
    clusters = graphemes(form)
    for i, g in enumerate(clusters):
        base = g[0]
        if base not in BEGADKEPHAT or DAGESH in g[1:]:
            continue
        if i == 0:
            clusters[i] = base + DAGESH + g[1:]
        elif SHEWA in clusters[i - 1][1:] and not _shewa_is_vocal(clusters, i - 1):
            clusters[i] = base + DAGESH + g[1:]
    return "".join(clusters)


# ── Transliteration ──────────────────────────────────────────────────────────

# Plosive / spirant romanisation for begadkephat consonants.
_BEGAD_PLOSIVE = {
    "ב": "b",
    "ג": "g",
    "ד": "d",
    "כ": "k",
    "פ": "p",
    "ת": "t",
}
_BEGAD_SPIRANT = {
    "ב": "ḇ",
    "ג": "ḡ",
    "ד": "ḏ",
    "כ": "ḵ",
    "פ": "f",
    "ת": "ṯ",
}

_CONSONANT_ROMAN = {
    "א": "ʾ",
    "ב": "b",
    "ג": "g",
    "ד": "d",
    "ה": "h",
    "ו": "w",
    "ז": "z",
    "ח": "ḥ",
    "ט": "ṭ",
    "י": "y",
    "כ": "k",
    "ך": "k",
    "ל": "l",
    "מ": "m",
    "ם": "m",
    "נ": "n",
    "ן": "n",
    "ס": "s",
    "ע": "ʿ",
    "פ": "p",
    "ף": "p",
    "צ": "ṣ",
    "ץ": "ṣ",
    "ק": "q",
    "ר": "r",
    "ש": "š",
    "ת": "t",
}


def transliterate_radical(consonant: str, spirant: bool) -> str:
    """Romanise a single radical consonant, honouring spirantisation."""
    if consonant in BEGADKEPHAT:
        return _BEGAD_SPIRANT[consonant] if spirant else _BEGAD_PLOSIVE[consonant]
    return _CONSONANT_ROMAN.get(consonant, consonant)


# ── Skeleton cache ───────────────────────────────────────────────────────────

# Reference Qal paradigm (שָׁמַר), form-by-form, in template order. Populated
# lazily from verb_paradigm to avoid a circular import at module load.
_HEBREW_SKELETON: list[str] | None = None
_TRANSLIT_SKELETON: list[str] | None = None


def _reference_forms() -> tuple[list[str], list[str]]:
    """Return (hebrew, transliteration) for the reference Qal verb שָׁמַר."""
    from reshith.exercises.verb_paradigm import _QAL_REFERENCE

    heb = [h for (h, _t) in _QAL_REFERENCE]
    translit = [t for (_h, t) in _QAL_REFERENCE]
    return heb, translit


def _translit_skeletonize(translit: str) -> str:
    """De-lexicalise the reference romanisation into @1/@2/@3 placeholders.

    The reference verb šāmar has radicals š, m, r appearing in that order. We
    replace only the *first* occurrence of each — scanning left to right — so
    that identical letters inside inflectional suffixes (``-tem``, ``-īm``,
    ``-nū`` …) are left untouched. š always begins the stem, and the first m /
    first r after it are always the C2 / C3 radicals.
    """
    result = translit
    for letter, marker in (("š", "@1"), ("m", "@2"), ("r", "@3")):
        result = result.replace(letter, marker, 1)
    return result


def _ensure_skeletons() -> None:
    global _HEBREW_SKELETON, _TRANSLIT_SKELETON
    if _HEBREW_SKELETON is not None:
        return
    heb, translit = _reference_forms()
    _HEBREW_SKELETON = [_skeletonize(h) for h in heb]
    _TRANSLIT_SKELETON = [_translit_skeletonize(t) for t in translit]


# ── Public generator ─────────────────────────────────────────────────────────


def generate_qal_forms(
    radicals: tuple[str, str, str],
    exceptions: dict[int, tuple[str, str]] | None = None,
    vocal_shewa_c3_indices: frozenset[int] | None = None,
) -> list[tuple[str, str]]:
    """Generate the full Qal paradigm for a strong triliteral root.

    Args:
        radicals: The three root consonants, e.g. ``("ז", "כ", "ר")``.
        exceptions: Optional ``{form_index: (hebrew, transliteration)}`` overrides
            for Masoretic cells the mechanical rules get wrong.
        vocal_shewa_c3_indices: Template indices where the shewa under C2 is
            vocal even though it follows a short vowel, so the third radical must
            **not** receive dagesh lene (e.g. the Qal fs/mp imperatives כִּתְבִי,
            כִּתְבוּ). Supplied by the caller because it depends on the template,
            not the root.

    Returns:
        A list of ``(hebrew, transliteration)`` pairs in template order,
        matching the length of the Qal template.
    """
    _ensure_skeletons()
    assert _HEBREW_SKELETON is not None and _TRANSLIT_SKELETON is not None

    c1, c2, c3 = radicals
    exceptions = exceptions or {}
    vocal_shewa_c3_indices = vocal_shewa_c3_indices or frozenset()

    def heb_letter(consonant: str) -> str:
        # Shin gets its shin-dot; strong verbs here use shin only (not sin).
        if consonant == _SIN:
            return consonant + SHIN_DOT
        return consonant

    results: list[tuple[str, str]] = []
    for i, (hsk, tsk) in enumerate(zip(_HEBREW_SKELETON, _TRANSLIT_SKELETON)):
        if i in exceptions:
            results.append(exceptions[i])
            continue

        raw = (
            hsk.replace("@1", heb_letter(c1))
            .replace("@2", heb_letter(c2))
            .replace("@3", heb_letter(c3))
        )
        hebrew = apply_dagesh_lene(raw)

        # Suppress a spurious dagesh lene on C3 where the C2 shewa is vocal.
        if i in vocal_shewa_c3_indices and c3 in BEGADKEPHAT:
            hebrew = _strip_c3_dagesh(hebrew, c3)

        # Determine spirantisation per radical from the final Hebrew: a
        # begadkephat radical is spirant when it has no dagesh in this form.
        spirant = _spirant_flags(hebrew, (c1, c2, c3))
        translit = (
            tsk.replace("@1", transliterate_radical(c1, spirant[0]))
            .replace("@2", transliterate_radical(c2, spirant[1]))
            .replace("@3", transliterate_radical(c3, spirant[2]))
        )
        results.append((hebrew, translit))

    return results


def _strip_c3_dagesh(hebrew: str, c3: str) -> str:
    """Remove dagesh lene from the third-radical cluster of a form."""
    clusters = graphemes(hebrew)
    idx = _radical_cluster_indices(clusters, (clusters[0][0], "", c3))[2]
    if idx is not None:
        clusters[idx] = clusters[idx].replace(DAGESH, "")
    return "".join(clusters)


def _spirant_flags(
    hebrew: str, radicals: tuple[str, str, str]
) -> tuple[bool, bool, bool]:
    """For each radical, whether it is spirant (no dagesh) in this Hebrew form."""
    clusters = graphemes(hebrew)
    flags = [False, False, False]
    radical_positions = _radical_cluster_indices(clusters, radicals)
    for slot, idx in enumerate(radical_positions):
        if radicals[slot] in BEGADKEPHAT and idx is not None:
            flags[slot] = DAGESH not in clusters[idx][1:]
    return flags[0], flags[1], flags[2]


def _radical_cluster_indices(
    clusters: list[str], radicals: tuple[str, str, str]
) -> list[int | None]:
    """Find the cluster index of each radical, left to right, first match each."""
    used: set[int] = set()
    indices: list[int | None] = []
    for consonant in radicals:
        found: int | None = None
        for i, g in enumerate(clusters):
            if i in used:
                continue
            if g[0] == consonant:
                found = i
                used.add(i)
                break
        indices.append(found)
    return indices
