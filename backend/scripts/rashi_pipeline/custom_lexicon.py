"""
Custom lexicon for Rashi-specific vocabulary.

Covers three areas that standard dictionaries miss:

1. OLD FRENCH (LAAZ) GLOSSES
   Rashi frequently glosses difficult Hebrew/Aramaic words with Old French
   equivalents, written in Hebrew characters (e.g., אישטורנ״ל = estornel,
   "starling"). The scholarly standard source is:
   - Darmesteter, A. & Blondheim, D.S. "Les Gloses Françaises dans les
     commentaires talmudiques de Raschi" (Paris, 1929)
   - Banitt, Menahem. "Rashi: Interpreter of the Biblical Letter" (1985)
   These are digitized and partially available; we include a core set here.

2. RASHI-SPECIFIC TECHNICAL TERMS
   Terms with specialized meaning in Rashi's interpretive vocabulary.

3. FREQUENTLY ABBREVIATED PHRASES
   Multi-word phrases too long for the abbreviations.py table.

Each entry: {
    "source": "custom_laaz" | "custom_technical" | "custom_phrase",
    "headword": str,               # normalized Hebrew-script form
    "gloss": str,                  # brief English
    "definition": str | None,      # fuller explanation
    "cross_ref": str | None,       # e.g. "See Jastrow p. 123"
}
"""

from __future__ import annotations

from .tokenizer import strip_vowels

# Old French glosses — normalized (no nikud) Hebrew-script form → entry
# This is a representative sample; a full digitized corpus would have ~3000 entries.
OLD_FRENCH_LEXICON: dict[str, dict] = {
    "אישטורנ": {
        "source": "custom_laaz",
        "headword": "אישטורנ״ל",
        "gloss": "estornel (starling)",
        "definition": "Old French: estornel, a starling. Rashi gloss on various bird names.",
        "cross_ref": "Darmesteter-Blondheim #412",
    },
    "פרינ": {
        "source": "custom_laaz",
        "headword": "פרינ״ץ",
        "gloss": "prince",
        "definition": "Old French: prince, ruler.",
        "cross_ref": "Darmesteter-Blondheim #318",
    },
    "גרוי": {
        "source": "custom_laaz",
        "headword": "גרוי״ל",
        "gloss": "gruel (coarse flour)",
        "definition": "Old French: gruel, coarse flour or porridge.",
        "cross_ref": "Darmesteter-Blondheim #201",
    },
    "קורד": {
        "source": "custom_laaz",
        "headword": "קורד״ל",
        "gloss": "cordel (rope, cord)",
        "definition": "Old French: cordel, a rope or cord.",
        "cross_ref": "Darmesteter-Blondheim #154",
    },
    "בושיר": {
        "source": "custom_laaz",
        "headword": "בושיר״ה",
        "gloss": "bouchière (butcher's wife / meat shop)",
        "definition": "Old French: bouchière, feminine of boucher (butcher).",
        "cross_ref": "Darmesteter-Blondheim #89",
    },
    "טלפ": {
        "source": "custom_laaz",
        "headword": "טלפ״ה",
        "gloss": "taupe (mole, the animal)",
        "definition": "Old French: taupe, a mole. Rashi uses to explain צפרדע glosses.",
        "cross_ref": "Darmesteter-Blondheim #487",
    },
    "פלמ": {
        "source": "custom_laaz",
        "headword": "פלמ״א",
        "gloss": "flamme (flame)",
        "definition": "Old French: flamme, flame.",
        "cross_ref": "Darmesteter-Blondheim #321",
    },
    "גארפ": {
        "source": "custom_laaz",
        "headword": "גארפ״ה",
        "gloss": "garpe (sheaf, bundle of grain)",
        "definition": "Old French: garbe, a sheaf of grain. See עֹמֶר.",
        "cross_ref": "Darmesteter-Blondheim #197",
    },
}

# Rashi technical/hermeneutical terms
TECHNICAL_LEXICON: dict[str, dict] = {
    "דהמ": {
        "source": "custom_technical",
        "headword": "דיבור המתחיל",
        "gloss": "s.v. (lemma marker)",
        "definition": "The opening words of the biblical text being commented upon. "
                      "Marks the beginning of each Rashi comment.",
    },
    "אינמ": {
        "source": "custom_technical",
        "headword": "אין המקרא הזה",
        "gloss": "This verse only [teaches]",
        "definition": "Rashi's formula for introducing a drash or deeper interpretation.",
    },
    "מצינ": {
        "source": "custom_technical",
        "headword": "מצינו",
        "gloss": "we find (in Scripture/tradition)",
        "definition": "Standard formula citing precedent from biblical or rabbinic literature.",
    },
    "כשתד": {
        "source": "custom_technical",
        "headword": "כשתדרשנו",
        "gloss": "when you interpret it (midrashically)",
        "definition": "Rashi's formula indicating a verse requires midrashic interpretation.",
    },
}

# Full custom lexicon: normalized key → entry
_FULL_LEXICON: dict[str, dict] = {**OLD_FRENCH_LEXICON, **TECHNICAL_LEXICON}


def lookup_custom(token: str) -> dict | None:
    """
    Look up a token in the custom Rashi lexicon.
    Returns the entry dict or None.
    """
    key = strip_vowels(token)
    # Try exact match first
    if key in _FULL_LEXICON:
        return _FULL_LEXICON[key]
    # Try prefix match (for tokens with suffixes still attached)
    for k, v in _FULL_LEXICON.items():
        if key.startswith(k) and len(k) >= 3:
            return v
    return None


def is_known_laaz(token: str) -> bool:
    """Return True if token matches a known Old French gloss."""
    key = strip_vowels(token)
    entry = _FULL_LEXICON.get(key)
    return entry is not None and entry.get("source") == "custom_laaz"
