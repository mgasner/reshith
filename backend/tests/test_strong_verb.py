"""Tests for the strong-verb Qal paradigm generator.

The generator (``reshith.exercises.strong_verb``) projects the שָׁמַר vocalisation
pattern onto arbitrary regular triliteral roots and applies deterministic
Masoretic rules (dagesh lene, spirantisation, vocal-shewa imperatives). These
tests pin it against the hand-verified reference verbs so any regression in the
rules is caught immediately.
"""

import unicodedata

from reshith.exercises import verb_paradigm as vp
from reshith.exercises.strong_verb import generate_qal_forms


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


# Regular (strong) verbs that were hand-entered before the generator existed.
# The generator must reproduce them byte-for-byte.
_REFERENCE_STRONG_VERBS = {
    "שׁמר": ("\u05e9", "\u05de", "\u05e8"),  # š-m-r
    "כתב": ("\u05db", "\u05ea", "\u05d1"),  # k-t-b
    "פקד": ("\u05e4", "\u05e7", "\u05d3"),  # p-q-d
}


def test_generator_reproduces_hand_entered_reference_verbs() -> None:
    """Generated forms match the hand-verified paradigms exactly."""
    for root, radicals in _REFERENCE_STRONG_VERBS.items():
        expected = vp._VERB_DATA[("qal", root)]["forms"]
        generated = generate_qal_forms(
            radicals, vocal_shewa_c3_indices=vp._QAL_VOCAL_SHEWA_C3
        )
        assert len(generated) == len(expected), root
        for i, ((gh, gt), (eh, et)) in enumerate(zip(generated, expected)):
            assert _nfc(gh) == _nfc(eh), f"{root} Hebrew form {i}: {gh!r} != {eh!r}"
            assert gt == et, f"{root} translit form {i}: {gt!r} != {et!r}"


def test_reference_matches_shomer_entry() -> None:
    """_QAL_REFERENCE stays in sync with the שׁמר entry in _VERB_DATA."""
    assert vp._QAL_REFERENCE == vp._VERB_DATA[("qal", "שׁמר")]["forms"]


def test_generated_forms_length_matches_template() -> None:
    """Every generated verb fills exactly the Qal template."""
    template = vp.BINYANIM["qal"]["template"]
    for root, radicals, *_ in vp._STRONG_QAL_VERBS:
        forms = generate_qal_forms(
            radicals, vocal_shewa_c3_indices=vp._QAL_VOCAL_SHEWA_C3
        )
        assert len(forms) == len(template), root


def test_new_strong_verbs_registered() -> None:
    """All configured strong verbs are queryable through get_paradigm."""
    for root, _radicals, _rt, _defn in vp._STRONG_QAL_VERBS:
        paradigm = vp.get_paradigm("qal", root)
        assert paradigm is not None, root
        assert paradigm.forms, root
        # Citation (3ms perfect) is the first form.
        assert paradigm.citation == paradigm.forms[0].hebrew, root


def test_dagesh_lene_at_word_start() -> None:
    """A begadkephat first radical takes dagesh lene at word start."""
    forms = generate_qal_forms(
        ("\u05db", "\u05ea", "\u05d1"),  # k-t-b
        vocal_shewa_c3_indices=vp._QAL_VOCAL_SHEWA_C3,
    )
    # 3ms perfect כָּתַב: the first consonant (kaf) carries a dagesh.
    hebrew = _nfc(forms[0][0])
    assert hebrew[0] == "\u05db"  # kaf
    assert "\u05bc" in hebrew[1:3]  # dagesh among the first radical's points


def test_vocal_shewa_imperative_has_no_c3_dagesh() -> None:
    """fs/mp imperatives (כִּתְבִי) keep a spirant third radical."""
    forms = generate_qal_forms(
        ("\u05db", "\u05ea", "\u05d1"),  # k-t-b
        vocal_shewa_c3_indices=vp._QAL_VOCAL_SHEWA_C3,
    )
    # Template index 20 is the 2fs imperative.
    hebrew, translit = forms[20]
    assert "\u05d1\u05bc" not in _nfc(hebrew)  # bet has NO dagesh
    assert translit.endswith("ḇī")  # spirant bet
