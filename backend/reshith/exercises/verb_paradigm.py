"""
Hebrew verb paradigm generator for all seven binyanim.

Provides full paradigm tables for strong verbs and generates
worksheets with configurable numbers of blanked-out forms.

Binyanim covered: Qal, Niphal, Piel, Pual, Hiphil, Hophal, Hithpael.
"""

import random
import unicodedata
from dataclasses import dataclass, field


@dataclass
class ParadigmForm:
    """A single conjugated form in a verb paradigm."""

    conjugation: str  # perfect, imperfect, imperative, inf_construct, etc.
    person: str  # "1", "2", "3", "" (for non-finite)
    number: str  # "sg", "pl", "" (for infinitives)
    gender: str  # "m", "f", "c" (common), "" (for infinitives)
    label: str  # e.g. "3ms Perfect"
    hebrew: str
    transliteration: str


@dataclass
class VerbParadigm:
    """Complete paradigm for a single verb in a single binyan."""

    binyan: str
    binyan_display: str
    root: str
    root_transliteration: str
    citation: str  # 3ms perfect
    citation_transliteration: str
    definition: str
    forms: list[ParadigmForm] = field(default_factory=list)


@dataclass
class WorksheetForm:
    """A paradigm form that may be blanked out in a worksheet."""

    conjugation: str
    person: str
    number: str
    gender: str
    label: str
    hebrew: str
    transliteration: str
    answer_hebrew: str
    answer_transliteration: str
    is_blank: bool


@dataclass
class VerbWorksheet:
    """A paradigm worksheet with some forms blanked out."""

    binyan: str
    binyan_display: str
    root: str
    root_transliteration: str
    citation: str
    citation_transliteration: str
    definition: str
    forms: list[WorksheetForm] = field(default_factory=list)
    num_blanks: int = 0


@dataclass
class WorksheetGradeResult:
    """Result of grading a single worksheet answer."""

    index: int
    label: str
    correct: bool
    expected: str
    submitted: str
    feedback: str


# ── Form group definitions ───────────────────────────────────────────────────

_PERFECT = [
    ("perfect", "3", "sg", "m", "3ms Perfect"),
    ("perfect", "3", "sg", "f", "3fs Perfect"),
    ("perfect", "2", "sg", "m", "2ms Perfect"),
    ("perfect", "2", "sg", "f", "2fs Perfect"),
    ("perfect", "1", "sg", "c", "1cs Perfect"),
    ("perfect", "3", "pl", "c", "3cp Perfect"),
    ("perfect", "2", "pl", "m", "2mp Perfect"),
    ("perfect", "2", "pl", "f", "2fp Perfect"),
    ("perfect", "1", "pl", "c", "1cp Perfect"),
]

_IMPERFECT = [
    ("imperfect", "3", "sg", "m", "3ms Imperfect"),
    ("imperfect", "3", "sg", "f", "3fs Imperfect"),
    ("imperfect", "2", "sg", "m", "2ms Imperfect"),
    ("imperfect", "2", "sg", "f", "2fs Imperfect"),
    ("imperfect", "1", "sg", "c", "1cs Imperfect"),
    ("imperfect", "3", "pl", "m", "3mp Imperfect"),
    ("imperfect", "3", "pl", "f", "3fp Imperfect"),
    ("imperfect", "2", "pl", "m", "2mp Imperfect"),
    ("imperfect", "2", "pl", "f", "2fp Imperfect"),
    ("imperfect", "1", "pl", "c", "1cp Imperfect"),
]

_IMPERATIVE = [
    ("imperative", "2", "sg", "m", "2ms Imperative"),
    ("imperative", "2", "sg", "f", "2fs Imperative"),
    ("imperative", "2", "pl", "m", "2mp Imperative"),
    ("imperative", "2", "pl", "f", "2fp Imperative"),
]

_INFINITIVES = [
    ("inf_construct", "", "", "", "Inf. Construct"),
    ("inf_absolute", "", "", "", "Inf. Absolute"),
]

_ACTIVE_PTC = [
    ("ptc_active", "", "sg", "m", "Act. Ptc. ms"),
    ("ptc_active", "", "sg", "f", "Act. Ptc. fs"),
    ("ptc_active", "", "pl", "m", "Act. Ptc. mp"),
    ("ptc_active", "", "pl", "f", "Act. Ptc. fp"),
]

_PASSIVE_PTC = [
    ("ptc_passive", "", "sg", "m", "Pass. Ptc. ms"),
    ("ptc_passive", "", "sg", "f", "Pass. Ptc. fs"),
    ("ptc_passive", "", "pl", "m", "Pass. Ptc. mp"),
    ("ptc_passive", "", "pl", "f", "Pass. Ptc. fp"),
]

_PARTICIPLE = [
    ("participle", "", "sg", "m", "Ptc. ms"),
    ("participle", "", "sg", "f", "Ptc. fs"),
    ("participle", "", "pl", "m", "Ptc. mp"),
    ("participle", "", "pl", "f", "Ptc. fp"),
]


# ── Binyan metadata ──────────────────────────────────────────────────────────

BINYANIM: dict[str, dict] = {
    "qal": {
        "display": "Qal (קַל)",
        "template": (
            _PERFECT + _IMPERFECT + _IMPERATIVE + _INFINITIVES
            + _ACTIVE_PTC + _PASSIVE_PTC
        ),
    },
    "niphal": {
        "display": "Niphal (נִפְעַל)",
        "template": (
            _PERFECT + _IMPERFECT + _IMPERATIVE + _INFINITIVES + _PARTICIPLE
        ),
    },
    "piel": {
        "display": "Piel (פִּעֵל)",
        "template": (
            _PERFECT + _IMPERFECT + _IMPERATIVE + _INFINITIVES + _PARTICIPLE
        ),
    },
    "pual": {
        "display": "Pual (פֻּעַל)",
        "template": _PERFECT + _IMPERFECT + _INFINITIVES + _PARTICIPLE,
    },
    "hiphil": {
        "display": "Hiphil (הִפְעִיל)",
        "template": (
            _PERFECT + _IMPERFECT + _IMPERATIVE + _INFINITIVES + _PARTICIPLE
        ),
    },
    "hophal": {
        "display": "Hophal (הֻפְעַל)",
        "template": _PERFECT + _IMPERFECT + _INFINITIVES + _PARTICIPLE,
    },
    "hithpael": {
        "display": "Hithpael (הִתְפַּעֵל)",
        "template": (
            _PERFECT + _IMPERFECT + _IMPERATIVE + _INFINITIVES + _PARTICIPLE
        ),
    },
}


# ── Paradigm data ────────────────────────────────────────────────────────────
# Keyed by (binyan, root). Each verb's "forms" list matches the binyan's
# template in order.

_VERB_DATA: dict[tuple[str, str], dict] = {
    # ═══════════════════════════════════════════════════════════════════════
    # QAL
    # ═══════════════════════════════════════════════════════════════════════
    ("qal", "שׁמר"): {
        "root_transliteration": "š-m-r",
        "citation": "שָׁמַר",
        "citation_transliteration": "šāmar",
        "definition": "to keep, guard, watch over, observe",
        "forms": [
            # Perfect
            ("שָׁמַר", "šāmar"), ("שָׁמְרָה", "šāmᵊrāh"),
            ("שָׁמַרְתָּ", "šāmartā"), ("שָׁמַרְתְּ", "šāmart"),
            ("שָׁמַרְתִּי", "šāmartī"), ("שָׁמְרוּ", "šāmᵊrū"),
            ("שְׁמַרְתֶּם", "šᵊmartem"), ("שְׁמַרְתֶּן", "šᵊmarten"),
            ("שָׁמַרְנוּ", "šāmarnū"),
            # Imperfect
            ("יִשְׁמֹר", "yišmōr"), ("תִּשְׁמֹר", "tišmōr"),
            ("תִּשְׁמֹר", "tišmōr"), ("תִּשְׁמְרִי", "tišmᵊrī"),
            ("אֶשְׁמֹר", "ʾešmōr"), ("יִשְׁמְרוּ", "yišmᵊrū"),
            ("תִּשְׁמֹרְנָה", "tišmōrnāh"), ("תִּשְׁמְרוּ", "tišmᵊrū"),
            ("תִּשְׁמֹרְנָה", "tišmōrnāh"), ("נִשְׁמֹר", "nišmōr"),
            # Imperative
            ("שְׁמֹר", "šᵊmōr"), ("שִׁמְרִי", "šimrī"),
            ("שִׁמְרוּ", "šimrū"), ("שְׁמֹרְנָה", "šᵊmōrnāh"),
            # Infinitives
            ("שְׁמֹר", "šᵊmōr"), ("שָׁמוֹר", "šāmōr"),
            # Active Participle
            ("שֹׁמֵר", "šōmēr"), ("שֹׁמֶרֶת", "šōmereṯ"),
            ("שֹׁמְרִים", "šōmᵊrīm"), ("שֹׁמְרוֹת", "šōmᵊrōṯ"),
            # Passive Participle
            ("שָׁמוּר", "šāmūr"), ("שְׁמוּרָה", "šᵊmūrāh"),
            ("שְׁמוּרִים", "šᵊmūrīm"), ("שְׁמוּרוֹת", "šᵊmūrōṯ"),
        ],
    },
    ("qal", "כתב"): {
        "root_transliteration": "k-t-b",
        "citation": "כָּתַב",
        "citation_transliteration": "kāṯaḇ",
        "definition": "to write",
        "forms": [
            ("כָּתַב", "kāṯaḇ"), ("כָּתְבָה", "kāṯᵊḇāh"),
            ("כָּתַבְתָּ", "kāṯaḇtā"), ("כָּתַבְתְּ", "kāṯaḇt"),
            ("כָּתַבְתִּי", "kāṯaḇtī"), ("כָּתְבוּ", "kāṯᵊḇū"),
            ("כְּתַבְתֶּם", "kᵊṯaḇtem"), ("כְּתַבְתֶּן", "kᵊṯaḇten"),
            ("כָּתַבְנוּ", "kāṯaḇnū"),
            ("יִכְתֹּב", "yiḵtōḇ"), ("תִּכְתֹּב", "tiḵtōḇ"),
            ("תִּכְתֹּב", "tiḵtōḇ"), ("תִּכְתְּבִי", "tiḵtᵊḇī"),
            ("אֶכְתֹּב", "ʾeḵtōḇ"), ("יִכְתְּבוּ", "yiḵtᵊḇū"),
            ("תִּכְתֹּבְנָה", "tiḵtōḇnāh"), ("תִּכְתְּבוּ", "tiḵtᵊḇū"),
            ("תִּכְתֹּבְנָה", "tiḵtōḇnāh"), ("נִכְתֹּב", "niḵtōḇ"),
            ("כְּתֹב", "kᵊṯōḇ"), ("כִּתְבִי", "kiṯḇī"),
            ("כִּתְבוּ", "kiṯḇū"), ("כְּתֹבְנָה", "kᵊṯōḇnāh"),
            ("כְּתֹב", "kᵊṯōḇ"), ("כָּתוֹב", "kāṯōḇ"),
            ("כֹּתֵב", "kōṯēḇ"), ("כֹּתֶבֶת", "kōṯeḇeṯ"),
            ("כֹּתְבִים", "kōṯᵊḇīm"), ("כֹּתְבוֹת", "kōṯᵊḇōṯ"),
            ("כָּתוּב", "kāṯūḇ"), ("כְּתוּבָה", "kᵊṯūḇāh"),
            ("כְּתוּבִים", "kᵊṯūḇīm"), ("כְּתוּבוֹת", "kᵊṯūḇōṯ"),
        ],
    },
    ("qal", "מלך"): {
        "root_transliteration": "m-l-k",
        "citation": "מָלַךְ",
        "citation_transliteration": "mālak",
        "definition": "to reign, be king",
        "forms": [
            ("מָלַךְ", "mālak"), ("מָלְכָה", "mālᵊkāh"),
            ("מָלַכְתָּ", "mālaktā"), ("מָלַכְתְּ", "mālakt"),
            ("מָלַכְתִּי", "mālaktī"), ("מָלְכוּ", "mālᵊkū"),
            ("מְלַכְתֶּם", "mᵊlaktem"), ("מְלַכְתֶּן", "mᵊlakten"),
            ("מָלַכְנוּ", "mālaknū"),
            ("יִמְלֹךְ", "yimlōk"), ("תִּמְלֹךְ", "timlōk"),
            ("תִּמְלֹךְ", "timlōk"), ("תִּמְלְכִי", "timlᵊkī"),
            ("אֶמְלֹךְ", "ʾemlōk"), ("יִמְלְכוּ", "yimlᵊkū"),
            ("תִּמְלֹכְנָה", "timlōknāh"), ("תִּמְלְכוּ", "timlᵊkū"),
            ("תִּמְלֹכְנָה", "timlōknāh"), ("נִמְלֹךְ", "nimlōk"),
            ("מְלֹךְ", "mᵊlōk"), ("מִלְכִי", "milkī"),
            ("מִלְכוּ", "milkū"), ("מְלֹכְנָה", "mᵊlōknāh"),
            ("מְלֹךְ", "mᵊlōk"), ("מָלוֹךְ", "mālōk"),
            ("מֹלֵךְ", "mōlēk"), ("מֹלֶכֶת", "mōlekeṯ"),
            ("מֹלְכִים", "mōlᵊkīm"), ("מֹלְכוֹת", "mōlᵊkōṯ"),
            ("מָלוּךְ", "mālūk"), ("מְלוּכָה", "mᵊlūkāh"),
            ("מְלוּכִים", "mᵊlūkīm"), ("מְלוּכוֹת", "mᵊlūkōṯ"),
        ],
    },
    ("qal", "למד"): {
        "root_transliteration": "l-m-d",
        "citation": "לָמַד",
        "citation_transliteration": "lāmaḏ",
        "definition": "to learn",
        "forms": [
            ("לָמַד", "lāmaḏ"), ("לָמְדָה", "lāmᵊḏāh"),
            ("לָמַדְתָּ", "lāmaḏtā"), ("לָמַדְתְּ", "lāmaḏt"),
            ("לָמַדְתִּי", "lāmaḏtī"), ("לָמְדוּ", "lāmᵊḏū"),
            ("לְמַדְתֶּם", "lᵊmaḏtem"), ("לְמַדְתֶּן", "lᵊmaḏten"),
            ("לָמַדְנוּ", "lāmaḏnū"),
            ("יִלְמַד", "yilmaḏ"), ("תִּלְמַד", "tilmaḏ"),
            ("תִּלְמַד", "tilmaḏ"), ("תִּלְמְדִי", "tilmᵊḏī"),
            ("אֶלְמַד", "ʾelmaḏ"), ("יִלְמְדוּ", "yilmᵊḏū"),
            ("תִּלְמַדְנָה", "tilmaḏnāh"), ("תִּלְמְדוּ", "tilmᵊḏū"),
            ("תִּלְמַדְנָה", "tilmaḏnāh"), ("נִלְמַד", "nilmaḏ"),
            ("לְמַד", "lᵊmaḏ"), ("לִמְדִי", "limḏī"),
            ("לִמְדוּ", "limḏū"), ("לְמַדְנָה", "lᵊmaḏnāh"),
            ("לְמֹד", "lᵊmōḏ"), ("לָמוֹד", "lāmōḏ"),
            ("לֹמֵד", "lōmēḏ"), ("לֹמֶדֶת", "lōmeḏeṯ"),
            ("לֹמְדִים", "lōmᵊḏīm"), ("לֹמְדוֹת", "lōmᵊḏōṯ"),
            ("לָמוּד", "lāmūḏ"), ("לְמוּדָה", "lᵊmūḏāh"),
            ("לְמוּדִים", "lᵊmūḏīm"), ("לְמוּדוֹת", "lᵊmūḏōṯ"),
        ],
    },
    ("qal", "פקד"): {
        "root_transliteration": "p-q-d",
        "citation": "פָּקַד",
        "citation_transliteration": "pāqaḏ",
        "definition": "to visit, appoint, number, punish",
        "forms": [
            ("פָּקַד", "pāqaḏ"), ("פָּקְדָה", "pāqᵊḏāh"),
            ("פָּקַדְתָּ", "pāqaḏtā"), ("פָּקַדְתְּ", "pāqaḏt"),
            ("פָּקַדְתִּי", "pāqaḏtī"), ("פָּקְדוּ", "pāqᵊḏū"),
            ("פְּקַדְתֶּם", "pᵊqaḏtem"), ("פְּקַדְתֶּן", "pᵊqaḏten"),
            ("פָּקַדְנוּ", "pāqaḏnū"),
            ("יִפְקֹד", "yifqōḏ"), ("תִּפְקֹד", "tifqōḏ"),
            ("תִּפְקֹד", "tifqōḏ"), ("תִּפְקְדִי", "tifqᵊḏī"),
            ("אֶפְקֹד", "ʾefqōḏ"), ("יִפְקְדוּ", "yifqᵊḏū"),
            ("תִּפְקֹדְנָה", "tifqōḏnāh"), ("תִּפְקְדוּ", "tifqᵊḏū"),
            ("תִּפְקֹדְנָה", "tifqōḏnāh"), ("נִפְקֹד", "nifqōḏ"),
            ("פְּקֹד", "pᵊqōḏ"), ("פִּקְדִי", "piqḏī"),
            ("פִּקְדוּ", "piqḏū"), ("פְּקֹדְנָה", "pᵊqōḏnāh"),
            ("פְּקֹד", "pᵊqōḏ"), ("פָּקוֹד", "pāqōḏ"),
            ("פֹּקֵד", "pōqēḏ"), ("פֹּקֶדֶת", "pōqeḏeṯ"),
            ("פֹּקְדִים", "pōqᵊḏīm"), ("פֹּקְדוֹת", "pōqᵊḏōṯ"),
            ("פָּקוּד", "pāqūḏ"), ("פְּקוּדָה", "pᵊqūḏāh"),
            ("פְּקוּדִים", "pᵊqūḏīm"), ("פְּקוּדוֹת", "pᵊqūḏōṯ"),
        ],
    },
    ("qal", "זכר"): {
        "root_transliteration": "z-k-r",
        "citation": "זָכַר",
        "citation_transliteration": "zāḵar",
        "definition": "to remember",
        "forms": [
            ("זָכַר", "zāḵar"), ("זָכְרָה", "zāḵᵊrāh"),
            ("זָכַרְתָּ", "zāḵartā"), ("זָכַרְתְּ", "zāḵart"),
            ("זָכַרְתִּי", "zāḵartī"), ("זָכְרוּ", "zāḵᵊrū"),
            ("זְכַרְתֶּם", "zᵊḵartem"), ("זְכַרְתֶּן", "zᵊḵarten"),
            ("זָכַרְנוּ", "zāḵarnū"),
            ("יִזְכֹּר", "yizkōr"), ("תִּזְכֹּר", "tizkōr"),
            ("תִּזְכֹּר", "tizkōr"), ("תִּזְכְּרִי", "tizkᵊrī"),
            ("אֶזְכֹּר", "ʾezkōr"), ("יִזְכְּרוּ", "yizkᵊrū"),
            ("תִּזְכֹּרְנָה", "tizkōrnāh"), ("תִּזְכְּרוּ", "tizkᵊrū"),
            ("תִּזְכֹּרְנָה", "tizkōrnāh"), ("נִזְכֹּר", "nizkōr"),
            ("זְכֹר", "zᵊkōr"), ("זִכְרִי", "ziḵrī"),
            ("זִכְרוּ", "ziḵrū"), ("זְכֹרְנָה", "zᵊkōrnāh"),
            ("זְכֹר", "zᵊkōr"), ("זָכוֹר", "zāḵōr"),
            ("זֹכֵר", "zōḵēr"), ("זֹכֶרֶת", "zōḵereṯ"),
            ("זֹכְרִים", "zōḵᵊrīm"), ("זֹכְרוֹת", "zōḵᵊrōṯ"),
            ("זָכוּר", "zāḵūr"), ("זְכוּרָה", "zᵊḵūrāh"),
            ("זְכוּרִים", "zᵊḵūrīm"), ("זְכוּרוֹת", "zᵊḵūrōṯ"),
        ],
    },
    # ═══════════════════════════════════════════════════════════════════════
    # NIPHAL — passive / reflexive of Qal
    # ═══════════════════════════════════════════════════════════════════════
    ("niphal", "שׁמר"): {
        "root_transliteration": "š-m-r",
        "citation": "נִשְׁמַר",
        "citation_transliteration": "nišmar",
        "definition": "to be kept, be guarded, take heed",
        "forms": [
            # Perfect (niqṭal)
            ("נִשְׁמַר", "nišmar"), ("נִשְׁמְרָה", "nišmᵊrāh"),
            ("נִשְׁמַרְתָּ", "nišmartā"), ("נִשְׁמַרְתְּ", "nišmart"),
            ("נִשְׁמַרְתִּי", "nišmartī"), ("נִשְׁמְרוּ", "nišmᵊrū"),
            ("נִשְׁמַרְתֶּם", "nišmartem"), ("נִשְׁמַרְתֶּן", "nišmarten"),
            ("נִשְׁמַרְנוּ", "nišmarnū"),
            # Imperfect (yiqqāṭēl)
            ("יִשָּׁמֵר", "yiššāmēr"), ("תִּשָּׁמֵר", "tiššāmēr"),
            ("תִּשָּׁמֵר", "tiššāmēr"), ("תִּשָּׁמְרִי", "tiššāmᵊrī"),
            ("אֶשָּׁמֵר", "ʾeššāmēr"), ("יִשָּׁמְרוּ", "yiššāmᵊrū"),
            ("תִּשָּׁמַרְנָה", "tiššāmarnāh"),
            ("תִּשָּׁמְרוּ", "tiššāmᵊrū"),
            ("תִּשָּׁמַרְנָה", "tiššāmarnāh"),
            ("נִשָּׁמֵר", "niššāmēr"),
            # Imperative (hiqqāṭēl)
            ("הִשָּׁמֵר", "hiššāmēr"), ("הִשָּׁמְרִי", "hiššāmᵊrī"),
            ("הִשָּׁמְרוּ", "hiššāmᵊrū"),
            ("הִשָּׁמַרְנָה", "hiššāmarnāh"),
            # Infinitives
            ("הִשָּׁמֵר", "hiššāmēr"), ("נִשְׁמוֹר", "nišmōr"),
            # Participle (niqṭāl)
            ("נִשְׁמָר", "nišmār"), ("נִשְׁמֶרֶת", "nišmereṯ"),
            ("נִשְׁמָרִים", "nišmārīm"), ("נִשְׁמָרוֹת", "nišmārōṯ"),
        ],
    },
    ("niphal", "כתב"): {
        "root_transliteration": "k-t-b",
        "citation": "נִכְתַּב",
        "citation_transliteration": "niḵtaḇ",
        "definition": "to be written",
        "forms": [
            ("נִכְתַּב", "niḵtaḇ"), ("נִכְתְּבָה", "niḵtᵊḇāh"),
            ("נִכְתַּבְתָּ", "niḵtaḇtā"), ("נִכְתַּבְתְּ", "niḵtaḇt"),
            ("נִכְתַּבְתִּי", "niḵtaḇtī"), ("נִכְתְּבוּ", "niḵtᵊḇū"),
            ("נִכְתַּבְתֶּם", "niḵtaḇtem"),
            ("נִכְתַּבְתֶּן", "niḵtaḇten"),
            ("נִכְתַּבְנוּ", "niḵtaḇnū"),
            ("יִכָּתֵב", "yikkāṯēḇ"), ("תִּכָּתֵב", "tikkāṯēḇ"),
            ("תִּכָּתֵב", "tikkāṯēḇ"), ("תִּכָּתְבִי", "tikkāṯᵊḇī"),
            ("אֶכָּתֵב", "ʾekkāṯēḇ"), ("יִכָּתְבוּ", "yikkāṯᵊḇū"),
            ("תִּכָּתַבְנָה", "tikkāṯaḇnāh"),
            ("תִּכָּתְבוּ", "tikkāṯᵊḇū"),
            ("תִּכָּתַבְנָה", "tikkāṯaḇnāh"),
            ("נִכָּתֵב", "nikkāṯēḇ"),
            ("הִכָּתֵב", "hikkāṯēḇ"), ("הִכָּתְבִי", "hikkāṯᵊḇī"),
            ("הִכָּתְבוּ", "hikkāṯᵊḇū"),
            ("הִכָּתַבְנָה", "hikkāṯaḇnāh"),
            ("הִכָּתֵב", "hikkāṯēḇ"), ("נִכְתּוֹב", "niḵtōḇ"),
            ("נִכְתָּב", "niḵtāḇ"), ("נִכְתֶּבֶת", "niḵteḇeṯ"),
            ("נִכְתָּבִים", "niḵtāḇīm"), ("נִכְתָּבוֹת", "niḵtāḇōṯ"),
        ],
    },
    # ═══════════════════════════════════════════════════════════════════════
    # PIEL — intensive active
    # ═══════════════════════════════════════════════════════════════════════
    ("piel", "שׁמר"): {
        "root_transliteration": "š-m-r",
        "citation": "שִׁמֵּר",
        "citation_transliteration": "šimmēr",
        "definition": "to keep carefully, preserve",
        "forms": [
            # Perfect (qiṭṭēl)
            ("שִׁמֵּר", "šimmēr"), ("שִׁמְּרָה", "šimmᵊrāh"),
            ("שִׁמַּרְתָּ", "šimmartā"), ("שִׁמַּרְתְּ", "šimmart"),
            ("שִׁמַּרְתִּי", "šimmartī"), ("שִׁמְּרוּ", "šimmᵊrū"),
            ("שִׁמַּרְתֶּם", "šimmartem"), ("שִׁמַּרְתֶּן", "šimmarten"),
            ("שִׁמַּרְנוּ", "šimmarnū"),
            # Imperfect (yᵊqaṭṭēl)
            ("יְשַׁמֵּר", "yᵊšammēr"), ("תְּשַׁמֵּר", "tᵊšammēr"),
            ("תְּשַׁמֵּר", "tᵊšammēr"), ("תְּשַׁמְּרִי", "tᵊšammᵊrī"),
            ("אֲשַׁמֵּר", "ʾᵃšammēr"), ("יְשַׁמְּרוּ", "yᵊšammᵊrū"),
            ("תְּשַׁמֵּרְנָה", "tᵊšammērnāh"),
            ("תְּשַׁמְּרוּ", "tᵊšammᵊrū"),
            ("תְּשַׁמֵּרְנָה", "tᵊšammērnāh"),
            ("נְשַׁמֵּר", "nᵊšammēr"),
            # Imperative (qaṭṭēl)
            ("שַׁמֵּר", "šammēr"), ("שַׁמְּרִי", "šammᵊrī"),
            ("שַׁמְּרוּ", "šammᵊrū"), ("שַׁמֵּרְנָה", "šammērnāh"),
            # Infinitives
            ("שַׁמֵּר", "šammēr"), ("שַׁמֵּר", "šammēr"),
            # Participle (mᵊqaṭṭēl)
            ("מְשַׁמֵּר", "mᵊšammēr"), ("מְשַׁמֶּרֶת", "mᵊšammereṯ"),
            ("מְשַׁמְּרִים", "mᵊšammᵊrīm"),
            ("מְשַׁמְּרוֹת", "mᵊšammᵊrōṯ"),
        ],
    },
    ("piel", "למד"): {
        "root_transliteration": "l-m-d",
        "citation": "לִמֵּד",
        "citation_transliteration": "limmēḏ",
        "definition": "to teach",
        "forms": [
            ("לִמֵּד", "limmēḏ"), ("לִמְּדָה", "limmᵊḏāh"),
            ("לִמַּדְתָּ", "limmaḏtā"), ("לִמַּדְתְּ", "limmaḏt"),
            ("לִמַּדְתִּי", "limmaḏtī"), ("לִמְּדוּ", "limmᵊḏū"),
            ("לִמַּדְתֶּם", "limmaḏtem"), ("לִמַּדְתֶּן", "limmaḏten"),
            ("לִמַּדְנוּ", "limmaḏnū"),
            ("יְלַמֵּד", "yᵊlammēḏ"), ("תְּלַמֵּד", "tᵊlammēḏ"),
            ("תְּלַמֵּד", "tᵊlammēḏ"), ("תְּלַמְּדִי", "tᵊlammᵊḏī"),
            ("אֲלַמֵּד", "ʾᵃlammēḏ"), ("יְלַמְּדוּ", "yᵊlammᵊḏū"),
            ("תְּלַמֵּדְנָה", "tᵊlammēḏnāh"),
            ("תְּלַמְּדוּ", "tᵊlammᵊḏū"),
            ("תְּלַמֵּדְנָה", "tᵊlammēḏnāh"),
            ("נְלַמֵּד", "nᵊlammēḏ"),
            ("לַמֵּד", "lammēḏ"), ("לַמְּדִי", "lammᵊḏī"),
            ("לַמְּדוּ", "lammᵊḏū"), ("לַמֵּדְנָה", "lammēḏnāh"),
            ("לַמֵּד", "lammēḏ"), ("לַמֵּד", "lammēḏ"),
            ("מְלַמֵּד", "mᵊlammēḏ"), ("מְלַמֶּדֶת", "mᵊlammeḏeṯ"),
            ("מְלַמְּדִים", "mᵊlammᵊḏīm"),
            ("מְלַמְּדוֹת", "mᵊlammᵊḏōṯ"),
        ],
    },
    # ═══════════════════════════════════════════════════════════════════════
    # PUAL — passive of Piel (no imperative)
    # ═══════════════════════════════════════════════════════════════════════
    ("pual", "שׁמר"): {
        "root_transliteration": "š-m-r",
        "citation": "שֻׁמַּר",
        "citation_transliteration": "šummar",
        "definition": "to be kept carefully, be preserved",
        "forms": [
            # Perfect (quṭṭal)
            ("שֻׁמַּר", "šummar"), ("שֻׁמְּרָה", "šummᵊrāh"),
            ("שֻׁמַּרְתָּ", "šummartā"), ("שֻׁמַּרְתְּ", "šummart"),
            ("שֻׁמַּרְתִּי", "šummartī"), ("שֻׁמְּרוּ", "šummᵊrū"),
            ("שֻׁמַּרְתֶּם", "šummartem"), ("שֻׁמַּרְתֶּן", "šummarten"),
            ("שֻׁמַּרְנוּ", "šummarnū"),
            # Imperfect (yᵊquṭṭal)
            ("יְשֻׁמַּר", "yᵊšummar"), ("תְּשֻׁמַּר", "tᵊšummar"),
            ("תְּשֻׁמַּר", "tᵊšummar"), ("תְּשֻׁמְּרִי", "tᵊšummᵊrī"),
            ("אֲשֻׁמַּר", "ʾᵃšummar"), ("יְשֻׁמְּרוּ", "yᵊšummᵊrū"),
            ("תְּשֻׁמַּרְנָה", "tᵊšummarnāh"),
            ("תְּשֻׁמְּרוּ", "tᵊšummᵊrū"),
            ("תְּשֻׁמַּרְנָה", "tᵊšummarnāh"),
            ("נְשֻׁמַּר", "nᵊšummar"),
            # Infinitives
            ("שֻׁמַּר", "šummar"), ("שֻׁמַּר", "šummar"),
            # Participle (mᵊquṭṭāl)
            ("מְשֻׁמָּר", "mᵊšummār"), ("מְשֻׁמֶּרֶת", "mᵊšummereṯ"),
            ("מְשֻׁמָּרִים", "mᵊšummārīm"),
            ("מְשֻׁמָּרוֹת", "mᵊšummārōṯ"),
        ],
    },
    ("pual", "למד"): {
        "root_transliteration": "l-m-d",
        "citation": "לֻמַּד",
        "citation_transliteration": "lummaḏ",
        "definition": "to be taught",
        "forms": [
            ("לֻמַּד", "lummaḏ"), ("לֻמְּדָה", "lummᵊḏāh"),
            ("לֻמַּדְתָּ", "lummaḏtā"), ("לֻמַּדְתְּ", "lummaḏt"),
            ("לֻמַּדְתִּי", "lummaḏtī"), ("לֻמְּדוּ", "lummᵊḏū"),
            ("לֻמַּדְתֶּם", "lummaḏtem"), ("לֻמַּדְתֶּן", "lummaḏten"),
            ("לֻמַּדְנוּ", "lummaḏnū"),
            ("יְלֻמַּד", "yᵊlummaḏ"), ("תְּלֻמַּד", "tᵊlummaḏ"),
            ("תְּלֻמַּד", "tᵊlummaḏ"), ("תְּלֻמְּדִי", "tᵊlummᵊḏī"),
            ("אֲלֻמַּד", "ʾᵃlummaḏ"), ("יְלֻמְּדוּ", "yᵊlummᵊḏū"),
            ("תְּלֻמַּדְנָה", "tᵊlummaḏnāh"),
            ("תְּלֻמְּדוּ", "tᵊlummᵊḏū"),
            ("תְּלֻמַּדְנָה", "tᵊlummaḏnāh"),
            ("נְלֻמַּד", "nᵊlummaḏ"),
            ("לֻמַּד", "lummaḏ"), ("לֻמַּד", "lummaḏ"),
            ("מְלֻמָּד", "mᵊlummāḏ"), ("מְלֻמֶּדֶת", "mᵊlummeḏeṯ"),
            ("מְלֻמָּדִים", "mᵊlummāḏīm"),
            ("מְלֻמָּדוֹת", "mᵊlummāḏōṯ"),
        ],
    },
    # ═══════════════════════════════════════════════════════════════════════
    # HIPHIL — causative active
    # ═══════════════════════════════════════════════════════════════════════
    ("hiphil", "שׁמר"): {
        "root_transliteration": "š-m-r",
        "citation": "הִשְׁמִיר",
        "citation_transliteration": "hišmīr",
        "definition": "to cause to keep, set a guard (model form)",
        "forms": [
            # Perfect (hiqṭīl)
            ("הִשְׁמִיר", "hišmīr"), ("הִשְׁמִירָה", "hišmīrāh"),
            ("הִשְׁמַרְתָּ", "hišmartā"), ("הִשְׁמַרְתְּ", "hišmart"),
            ("הִשְׁמַרְתִּי", "hišmartī"), ("הִשְׁמִירוּ", "hišmīrū"),
            ("הִשְׁמַרְתֶּם", "hišmartem"), ("הִשְׁמַרְתֶּן", "hišmarten"),
            ("הִשְׁמַרְנוּ", "hišmarnū"),
            # Imperfect (yaqṭīl)
            ("יַשְׁמִיר", "yašmīr"), ("תַּשְׁמִיר", "tašmīr"),
            ("תַּשְׁמִיר", "tašmīr"), ("תַּשְׁמִירִי", "tašmīrī"),
            ("אַשְׁמִיר", "ʾašmīr"), ("יַשְׁמִירוּ", "yašmīrū"),
            ("תַּשְׁמֵרְנָה", "tašmērnāh"), ("תַּשְׁמִירוּ", "tašmīrū"),
            ("תַּשְׁמֵרְנָה", "tašmērnāh"), ("נַשְׁמִיר", "našmīr"),
            # Imperative (haqṭēl)
            ("הַשְׁמֵר", "hašmēr"), ("הַשְׁמִירִי", "hašmīrī"),
            ("הַשְׁמִירוּ", "hašmīrū"), ("הַשְׁמֵרְנָה", "hašmērnāh"),
            # Infinitives
            ("הַשְׁמִיר", "hašmīr"), ("הַשְׁמֵר", "hašmēr"),
            # Participle (maqṭīl)
            ("מַשְׁמִיר", "mašmīr"), ("מַשְׁמִירָה", "mašmīrāh"),
            ("מַשְׁמִירִים", "mašmīrīm"), ("מַשְׁמִירוֹת", "mašmīrōṯ"),
        ],
    },
    ("hiphil", "מלך"): {
        "root_transliteration": "m-l-k",
        "citation": "הִמְלִיךְ",
        "citation_transliteration": "himlīḵ",
        "definition": "to make king, enthrone",
        "forms": [
            ("הִמְלִיךְ", "himlīḵ"), ("הִמְלִיכָה", "himlīḵāh"),
            ("הִמְלַכְתָּ", "himlaktā"), ("הִמְלַכְתְּ", "himlakt"),
            ("הִמְלַכְתִּי", "himlaktī"), ("הִמְלִיכוּ", "himlīḵū"),
            ("הִמְלַכְתֶּם", "himlaktem"), ("הִמְלַכְתֶּן", "himlakten"),
            ("הִמְלַכְנוּ", "himlaknū"),
            ("יַמְלִיךְ", "yamlīḵ"), ("תַּמְלִיךְ", "tamlīḵ"),
            ("תַּמְלִיךְ", "tamlīḵ"), ("תַּמְלִיכִי", "tamlīḵī"),
            ("אַמְלִיךְ", "ʾamlīḵ"), ("יַמְלִיכוּ", "yamlīḵū"),
            ("תַּמְלֵכְנָה", "tamlēḵnāh"), ("תַּמְלִיכוּ", "tamlīḵū"),
            ("תַּמְלֵכְנָה", "tamlēḵnāh"), ("נַמְלִיךְ", "namlīḵ"),
            ("הַמְלֵךְ", "hamlēḵ"), ("הַמְלִיכִי", "hamlīḵī"),
            ("הַמְלִיכוּ", "hamlīḵū"), ("הַמְלֵכְנָה", "hamlēḵnāh"),
            ("הַמְלִיךְ", "hamlīḵ"), ("הַמְלֵךְ", "hamlēḵ"),
            ("מַמְלִיךְ", "mamlīḵ"), ("מַמְלִיכָה", "mamlīḵāh"),
            ("מַמְלִיכִים", "mamlīḵīm"), ("מַמְלִיכוֹת", "mamlīḵōṯ"),
        ],
    },
    # ═══════════════════════════════════════════════════════════════════════
    # HOPHAL — passive of Hiphil (no imperative)
    # ═══════════════════════════════════════════════════════════════════════
    ("hophal", "שׁמר"): {
        "root_transliteration": "š-m-r",
        "citation": "הֻשְׁמַר",
        "citation_transliteration": "hušmar",
        "definition": "to be caused to keep (model form)",
        "forms": [
            # Perfect (huqṭal)
            ("הֻשְׁמַר", "hušmar"), ("הֻשְׁמְרָה", "hušmᵊrāh"),
            ("הֻשְׁמַרְתָּ", "hušmartā"), ("הֻשְׁמַרְתְּ", "hušmart"),
            ("הֻשְׁמַרְתִּי", "hušmartī"), ("הֻשְׁמְרוּ", "hušmᵊrū"),
            ("הֻשְׁמַרְתֶּם", "hušmartem"),
            ("הֻשְׁמַרְתֶּן", "hušmarten"),
            ("הֻשְׁמַרְנוּ", "hušmarnū"),
            # Imperfect (yuqṭal)
            ("יֻשְׁמַר", "yušmar"), ("תֻּשְׁמַר", "tušmar"),
            ("תֻּשְׁמַר", "tušmar"), ("תֻּשְׁמְרִי", "tušmᵊrī"),
            ("אֻשְׁמַר", "ʾušmar"), ("יֻשְׁמְרוּ", "yušmᵊrū"),
            ("תֻּשְׁמַרְנָה", "tušmarnāh"),
            ("תֻּשְׁמְרוּ", "tušmᵊrū"),
            ("תֻּשְׁמַרְנָה", "tušmarnāh"),
            ("נֻשְׁמַר", "nušmar"),
            # Infinitives
            ("הֻשְׁמַר", "hušmar"), ("הֻשְׁמַר", "hušmar"),
            # Participle (muqṭāl)
            ("מֻשְׁמָר", "mušmār"), ("מֻשְׁמֶרֶת", "mušmereṯ"),
            ("מֻשְׁמָרִים", "mušmārīm"), ("מֻשְׁמָרוֹת", "mušmārōṯ"),
        ],
    },
    ("hophal", "מלך"): {
        "root_transliteration": "m-l-k",
        "citation": "הֻמְלַךְ",
        "citation_transliteration": "humlak",
        "definition": "to be made king, be enthroned",
        "forms": [
            ("הֻמְלַךְ", "humlak"), ("הֻמְלְכָה", "humlᵊkāh"),
            ("הֻמְלַכְתָּ", "humlaktā"), ("הֻמְלַכְתְּ", "humlakt"),
            ("הֻמְלַכְתִּי", "humlaktī"), ("הֻמְלְכוּ", "humlᵊkū"),
            ("הֻמְלַכְתֶּם", "humlaktem"),
            ("הֻמְלַכְתֶּן", "humlakten"),
            ("הֻמְלַכְנוּ", "humlaknū"),
            ("יֻמְלַךְ", "yumlak"), ("תֻּמְלַךְ", "tumlak"),
            ("תֻּמְלַךְ", "tumlak"), ("תֻּמְלְכִי", "tumlᵊkī"),
            ("אֻמְלַךְ", "ʾumlak"), ("יֻמְלְכוּ", "yumlᵊkū"),
            ("תֻּמְלַכְנָה", "tumlaknāh"),
            ("תֻּמְלְכוּ", "tumlᵊkū"),
            ("תֻּמְלַכְנָה", "tumlaknāh"),
            ("נֻמְלַךְ", "numlak"),
            ("הֻמְלַךְ", "humlak"), ("הֻמְלַךְ", "humlak"),
            ("מֻמְלָךְ", "mumlāk"), ("מֻמְלֶכֶת", "mumlekeṯ"),
            ("מֻמְלָכִים", "mumlākīm"), ("מֻמְלָכוֹת", "mumlākōṯ"),
        ],
    },
    # ═══════════════════════════════════════════════════════════════════════
    # HITHPAEL — reflexive / reciprocal
    # Note: שׁמר shows sibilant metathesis (hitš → hišt)
    # ═══════════════════════════════════════════════════════════════════════
    ("hithpael", "שׁמר"): {
        "root_transliteration": "š-m-r",
        "citation": "הִשְׁתַּמֵּר",
        "citation_transliteration": "hištammēr",
        "definition": "to guard oneself, be on one's guard",
        "forms": [
            # Perfect (with metathesis: hitšammēr → hištammēr)
            ("הִשְׁתַּמֵּר", "hištammēr"),
            ("הִשְׁתַּמְּרָה", "hištammᵊrāh"),
            ("הִשְׁתַּמַּרְתָּ", "hištammartā"),
            ("הִשְׁתַּמַּרְתְּ", "hištammart"),
            ("הִשְׁתַּמַּרְתִּי", "hištammartī"),
            ("הִשְׁתַּמְּרוּ", "hištammᵊrū"),
            ("הִשְׁתַּמַּרְתֶּם", "hištammartem"),
            ("הִשְׁתַּמַּרְתֶּן", "hištammarten"),
            ("הִשְׁתַּמַּרְנוּ", "hištammarnū"),
            # Imperfect
            ("יִשְׁתַּמֵּר", "yištammēr"),
            ("תִּשְׁתַּמֵּר", "tištammēr"),
            ("תִּשְׁתַּמֵּר", "tištammēr"),
            ("תִּשְׁתַּמְּרִי", "tištammᵊrī"),
            ("אֶשְׁתַּמֵּר", "ʾeštammēr"),
            ("יִשְׁתַּמְּרוּ", "yištammᵊrū"),
            ("תִּשְׁתַּמַּרְנָה", "tištammarnāh"),
            ("תִּשְׁתַּמְּרוּ", "tištammᵊrū"),
            ("תִּשְׁתַּמַּרְנָה", "tištammarnāh"),
            ("נִשְׁתַּמֵּר", "ništammēr"),
            # Imperative
            ("הִשְׁתַּמֵּר", "hištammēr"),
            ("הִשְׁתַּמְּרִי", "hištammᵊrī"),
            ("הִשְׁתַּמְּרוּ", "hištammᵊrū"),
            ("הִשְׁתַּמַּרְנָה", "hištammarnāh"),
            # Infinitives
            ("הִשְׁתַּמֵּר", "hištammēr"), ("הִשְׁתַּמֵּר", "hištammēr"),
            # Participle (with metathesis: mitšammēr → mištammēr)
            ("מִשְׁתַּמֵּר", "mištammēr"),
            ("מִשְׁתַּמֶּרֶת", "mištammereṯ"),
            ("מִשְׁתַּמְּרִים", "mištammᵊrīm"),
            ("מִשְׁתַּמְּרוֹת", "mištammᵊrōṯ"),
        ],
    },
    ("hithpael", "פקד"): {
        "root_transliteration": "p-q-d",
        "citation": "הִתְפַּקֵּד",
        "citation_transliteration": "hitpaqqēḏ",
        "definition": "to be mustered, be numbered",
        "forms": [
            ("הִתְפַּקֵּד", "hitpaqqēḏ"),
            ("הִתְפַּקְּדָה", "hitpaqqᵊḏāh"),
            ("הִתְפַּקַּדְתָּ", "hitpaqqaḏtā"),
            ("הִתְפַּקַּדְתְּ", "hitpaqqaḏt"),
            ("הִתְפַּקַּדְתִּי", "hitpaqqaḏtī"),
            ("הִתְפַּקְּדוּ", "hitpaqqᵊḏū"),
            ("הִתְפַּקַּדְתֶּם", "hitpaqqaḏtem"),
            ("הִתְפַּקַּדְתֶּן", "hitpaqqaḏten"),
            ("הִתְפַּקַּדְנוּ", "hitpaqqaḏnū"),
            ("יִתְפַּקֵּד", "yitpaqqēḏ"),
            ("תִּתְפַּקֵּד", "titpaqqēḏ"),
            ("תִּתְפַּקֵּד", "titpaqqēḏ"),
            ("תִּתְפַּקְּדִי", "titpaqqᵊḏī"),
            ("אֶתְפַּקֵּד", "ʾetpaqqēḏ"),
            ("יִתְפַּקְּדוּ", "yitpaqqᵊḏū"),
            ("תִּתְפַּקַּדְנָה", "titpaqqaḏnāh"),
            ("תִּתְפַּקְּדוּ", "titpaqqᵊḏū"),
            ("תִּתְפַּקַּדְנָה", "titpaqqaḏnāh"),
            ("נִתְפַּקֵּד", "nitpaqqēḏ"),
            ("הִתְפַּקֵּד", "hitpaqqēḏ"),
            ("הִתְפַּקְּדִי", "hitpaqqᵊḏī"),
            ("הִתְפַּקְּדוּ", "hitpaqqᵊḏū"),
            ("הִתְפַּקַּדְנָה", "hitpaqqaḏnāh"),
            ("הִתְפַּקֵּד", "hitpaqqēḏ"), ("הִתְפַּקֵּד", "hitpaqqēḏ"),
            ("מִתְפַּקֵּד", "mitpaqqēḏ"),
            ("מִתְפַּקֶּדֶת", "mitpaqqeḏeṯ"),
            ("מִתְפַּקְּדִים", "mitpaqqᵊḏīm"),
            ("מִתְפַּקְּדוֹת", "mitpaqqᵊḏōṯ"),
        ],
    },
}


# ── Core functions ───────────────────────────────────────────────────────────


def available_binyanim() -> list[str]:
    """Return list of supported binyan keys."""
    return list(BINYANIM.keys())


def available_roots(binyan: str = "qal") -> list[str]:
    """Return list of roots that have paradigm data for a given binyan."""
    return [root for (b, root) in _VERB_DATA if b == binyan]


def get_paradigm(
    binyan: str = "qal",
    root: str | None = None,
) -> VerbParadigm | None:
    """
    Get the full paradigm for a verb root in a given binyan.
    If root is None, pick a random verb from that binyan.
    """
    roots = available_roots(binyan)
    if not roots:
        return None
    if root is None:
        root = random.choice(roots)

    data = _VERB_DATA.get((binyan, root))
    if data is None:
        return None

    meta = BINYANIM.get(binyan)
    if meta is None:
        return None

    template = meta["template"]
    forms = []
    for i, (conj, person, number, gender, label) in enumerate(template):
        heb, translit = data["forms"][i]
        forms.append(
            ParadigmForm(
                conjugation=conj,
                person=person,
                number=number,
                gender=gender,
                label=label,
                hebrew=heb,
                transliteration=translit,
            )
        )

    return VerbParadigm(
        binyan=binyan,
        binyan_display=meta["display"],
        root=root,
        root_transliteration=data["root_transliteration"],
        citation=data["citation"],
        citation_transliteration=data["citation_transliteration"],
        definition=data["definition"],
        forms=forms,
    )


def generate_worksheet(
    binyan: str = "qal",
    root: str | None = None,
    num_blanks: int = 10,
    conjugations: list[str] | None = None,
) -> VerbWorksheet | None:
    """
    Generate a worksheet: a full paradigm with some forms blanked out.

    Args:
        binyan: Which binyan to use.
        root: Verb root (random if None).
        num_blanks: How many forms to blank out.
        conjugations: If provided, only blank forms from these conjugations.
    """
    paradigm = get_paradigm(binyan, root)
    if paradigm is None:
        return None

    eligible = list(range(len(paradigm.forms)))
    if conjugations:
        eligible = [
            i
            for i in eligible
            if paradigm.forms[i].conjugation in conjugations
        ]

    num_blanks = min(num_blanks, len(eligible))
    blank_indices = set(random.sample(eligible, num_blanks))

    worksheet_forms = []
    for i, form in enumerate(paradigm.forms):
        is_blank = i in blank_indices
        worksheet_forms.append(
            WorksheetForm(
                conjugation=form.conjugation,
                person=form.person,
                number=form.number,
                gender=form.gender,
                label=form.label,
                hebrew="" if is_blank else form.hebrew,
                transliteration="" if is_blank else form.transliteration,
                answer_hebrew=form.hebrew,
                answer_transliteration=form.transliteration,
                is_blank=is_blank,
            )
        )

    return VerbWorksheet(
        binyan=paradigm.binyan,
        binyan_display=paradigm.binyan_display,
        root=paradigm.root,
        root_transliteration=paradigm.root_transliteration,
        citation=paradigm.citation,
        citation_transliteration=paradigm.citation_transliteration,
        definition=paradigm.definition,
        forms=worksheet_forms,
        num_blanks=num_blanks,
    )


def _normalize_hebrew(text: str) -> str:
    """Normalize Hebrew text for comparison."""
    return unicodedata.normalize("NFC", text.strip())


def grade_worksheet(
    answers: list[tuple[int, str]],
    worksheet: VerbWorksheet,
) -> list[WorksheetGradeResult]:
    """
    Grade worksheet answers.

    Args:
        answers: List of (form_index, submitted_hebrew) pairs.
        worksheet: The original worksheet for answer checking.
    """
    results = []
    for index, submitted in answers:
        if index < 0 or index >= len(worksheet.forms):
            continue
        form = worksheet.forms[index]
        expected = form.answer_hebrew
        correct = _normalize_hebrew(submitted) == _normalize_hebrew(expected)
        if correct:
            feedback = (
                f"Correct! {form.label}: "
                f"{expected} ({form.answer_transliteration})"
            )
        else:
            feedback = (
                f"Expected {expected} ({form.answer_transliteration})"
            )
        results.append(
            WorksheetGradeResult(
                index=index,
                label=form.label,
                correct=correct,
                expected=expected,
                submitted=submitted,
                feedback=feedback,
            )
        )
    return results
