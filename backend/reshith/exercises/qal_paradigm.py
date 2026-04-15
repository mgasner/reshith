"""
Qal verb paradigm generator for Biblical Hebrew.

Provides full paradigm tables for strong Qal verbs and generates
worksheets with configurable numbers of blanked-out forms.

Paradigm data covers: perfect, imperfect, imperative, infinitives,
and participles (active + passive) for common strong verbs.
"""

import random
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
    """Complete Qal paradigm for a single verb."""

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
    hebrew: str  # empty string if blanked
    transliteration: str  # empty string if blanked
    answer_hebrew: str  # always filled
    answer_transliteration: str  # always filled
    is_blank: bool


@dataclass
class QalWorksheet:
    """A paradigm worksheet with some forms blanked out."""

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


# ── Form template ────────────────────────────────────────────────────────────
# Ordered list of (conjugation, person, number, gender, label) for all forms
# in a Qal paradigm. Each verb supplies the hebrew/transliteration data
# in this same order.

FORM_TEMPLATE: list[tuple[str, str, str, str, str]] = [
    # Perfect
    ("perfect", "3", "sg", "m", "3ms Perfect"),
    ("perfect", "3", "sg", "f", "3fs Perfect"),
    ("perfect", "2", "sg", "m", "2ms Perfect"),
    ("perfect", "2", "sg", "f", "2fs Perfect"),
    ("perfect", "1", "sg", "c", "1cs Perfect"),
    ("perfect", "3", "pl", "c", "3cp Perfect"),
    ("perfect", "2", "pl", "m", "2mp Perfect"),
    ("perfect", "2", "pl", "f", "2fp Perfect"),
    ("perfect", "1", "pl", "c", "1cp Perfect"),
    # Imperfect
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
    # Imperative
    ("imperative", "2", "sg", "m", "2ms Imperative"),
    ("imperative", "2", "sg", "f", "2fs Imperative"),
    ("imperative", "2", "pl", "m", "2mp Imperative"),
    ("imperative", "2", "pl", "f", "2fp Imperative"),
    # Infinitives
    ("inf_construct", "", "", "", "Inf. Construct"),
    ("inf_absolute", "", "", "", "Inf. Absolute"),
    # Active Participle
    ("ptc_active", "", "sg", "m", "Act. Ptc. ms"),
    ("ptc_active", "", "sg", "f", "Act. Ptc. fs"),
    ("ptc_active", "", "pl", "m", "Act. Ptc. mp"),
    ("ptc_active", "", "pl", "f", "Act. Ptc. fp"),
    # Passive Participle
    ("ptc_passive", "", "sg", "m", "Pass. Ptc. ms"),
    ("ptc_passive", "", "sg", "f", "Pass. Ptc. fs"),
    ("ptc_passive", "", "pl", "m", "Pass. Ptc. mp"),
    ("ptc_passive", "", "pl", "f", "Pass. Ptc. fp"),
]


# ── Paradigm data ────────────────────────────────────────────────────────────
# Each entry: (hebrew, transliteration) in FORM_TEMPLATE order.

_VERB_DATA: dict[str, dict] = {
    "שׁמר": {
        "root_transliteration": "š-m-r",
        "citation": "שָׁמַר",
        "citation_transliteration": "šāmar",
        "definition": "to keep, guard, watch over, observe",
        "forms": [
            # Perfect
            ("שָׁמַר", "šāmar"),
            ("שָׁמְרָה", "šāmᵊrāh"),
            ("שָׁמַרְתָּ", "šāmartā"),
            ("שָׁמַרְתְּ", "šāmart"),
            ("שָׁמַרְתִּי", "šāmartī"),
            ("שָׁמְרוּ", "šāmᵊrū"),
            ("שְׁמַרְתֶּם", "šᵊmartem"),
            ("שְׁמַרְתֶּן", "šᵊmarten"),
            ("שָׁמַרְנוּ", "šāmarnū"),
            # Imperfect
            ("יִשְׁמֹר", "yišmōr"),
            ("תִּשְׁמֹר", "tišmōr"),
            ("תִּשְׁמֹר", "tišmōr"),
            ("תִּשְׁמְרִי", "tišmᵊrī"),
            ("אֶשְׁמֹר", "ʾešmōr"),
            ("יִשְׁמְרוּ", "yišmᵊrū"),
            ("תִּשְׁמֹרְנָה", "tišmōrnāh"),
            ("תִּשְׁמְרוּ", "tišmᵊrū"),
            ("תִּשְׁמֹרְנָה", "tišmōrnāh"),
            ("נִשְׁמֹר", "nišmōr"),
            # Imperative
            ("שְׁמֹר", "šᵊmōr"),
            ("שִׁמְרִי", "šimrī"),
            ("שִׁמְרוּ", "šimrū"),
            ("שְׁמֹרְנָה", "šᵊmōrnāh"),
            # Infinitives
            ("שְׁמֹר", "šᵊmōr"),
            ("שָׁמוֹר", "šāmōr"),
            # Active Participle
            ("שֹׁמֵר", "šōmēr"),
            ("שֹׁמֶרֶת", "šōmereṯ"),
            ("שֹׁמְרִים", "šōmᵊrīm"),
            ("שֹׁמְרוֹת", "šōmᵊrōṯ"),
            # Passive Participle
            ("שָׁמוּר", "šāmūr"),
            ("שְׁמוּרָה", "šᵊmūrāh"),
            ("שְׁמוּרִים", "šᵊmūrīm"),
            ("שְׁמוּרוֹת", "šᵊmūrōṯ"),
        ],
    },
    "כתב": {
        "root_transliteration": "k-t-b",
        "citation": "כָּתַב",
        "citation_transliteration": "kāṯaḇ",
        "definition": "to write",
        "forms": [
            # Perfect
            ("כָּתַב", "kāṯaḇ"),
            ("כָּתְבָה", "kāṯᵊḇāh"),
            ("כָּתַבְתָּ", "kāṯaḇtā"),
            ("כָּתַבְתְּ", "kāṯaḇt"),
            ("כָּתַבְתִּי", "kāṯaḇtī"),
            ("כָּתְבוּ", "kāṯᵊḇū"),
            ("כְּתַבְתֶּם", "kᵊṯaḇtem"),
            ("כְּתַבְתֶּן", "kᵊṯaḇten"),
            ("כָּתַבְנוּ", "kāṯaḇnū"),
            # Imperfect
            ("יִכְתֹּב", "yiḵtōḇ"),
            ("תִּכְתֹּב", "tiḵtōḇ"),
            ("תִּכְתֹּב", "tiḵtōḇ"),
            ("תִּכְתְּבִי", "tiḵtᵊḇī"),
            ("אֶכְתֹּב", "ʾeḵtōḇ"),
            ("יִכְתְּבוּ", "yiḵtᵊḇū"),
            ("תִּכְתֹּבְנָה", "tiḵtōḇnāh"),
            ("תִּכְתְּבוּ", "tiḵtᵊḇū"),
            ("תִּכְתֹּבְנָה", "tiḵtōḇnāh"),
            ("נִכְתֹּב", "niḵtōḇ"),
            # Imperative
            ("כְּתֹב", "kᵊṯōḇ"),
            ("כִּתְבִי", "kiṯḇī"),
            ("כִּתְבוּ", "kiṯḇū"),
            ("כְּתֹבְנָה", "kᵊṯōḇnāh"),
            # Infinitives
            ("כְּתֹב", "kᵊṯōḇ"),
            ("כָּתוֹב", "kāṯōḇ"),
            # Active Participle
            ("כֹּתֵב", "kōṯēḇ"),
            ("כֹּתֶבֶת", "kōṯeḇeṯ"),
            ("כֹּתְבִים", "kōṯᵊḇīm"),
            ("כֹּתְבוֹת", "kōṯᵊḇōṯ"),
            # Passive Participle
            ("כָּתוּב", "kāṯūḇ"),
            ("כְּתוּבָה", "kᵊṯūḇāh"),
            ("כְּתוּבִים", "kᵊṯūḇīm"),
            ("כְּתוּבוֹת", "kᵊṯūḇōṯ"),
        ],
    },
    "מלך": {
        "root_transliteration": "m-l-k",
        "citation": "מָלַךְ",
        "citation_transliteration": "mālak",
        "definition": "to reign, be king",
        "forms": [
            # Perfect
            ("מָלַךְ", "mālak"),
            ("מָלְכָה", "mālᵊkāh"),
            ("מָלַכְתָּ", "mālaktā"),
            ("מָלַכְתְּ", "mālakt"),
            ("מָלַכְתִּי", "mālaktī"),
            ("מָלְכוּ", "mālᵊkū"),
            ("מְלַכְתֶּם", "mᵊlaktem"),
            ("מְלַכְתֶּן", "mᵊlakten"),
            ("מָלַכְנוּ", "mālaknū"),
            # Imperfect
            ("יִמְלֹךְ", "yimlōk"),
            ("תִּמְלֹךְ", "timlōk"),
            ("תִּמְלֹךְ", "timlōk"),
            ("תִּמְלְכִי", "timlᵊkī"),
            ("אֶמְלֹךְ", "ʾemlōk"),
            ("יִמְלְכוּ", "yimlᵊkū"),
            ("תִּמְלֹכְנָה", "timlōknāh"),
            ("תִּמְלְכוּ", "timlᵊkū"),
            ("תִּמְלֹכְנָה", "timlōknāh"),
            ("נִמְלֹךְ", "nimlōk"),
            # Imperative
            ("מְלֹךְ", "mᵊlōk"),
            ("מִלְכִי", "milkī"),
            ("מִלְכוּ", "milkū"),
            ("מְלֹכְנָה", "mᵊlōknāh"),
            # Infinitives
            ("מְלֹךְ", "mᵊlōk"),
            ("מָלוֹךְ", "mālōk"),
            # Active Participle
            ("מֹלֵךְ", "mōlēk"),
            ("מֹלֶכֶת", "mōlekeṯ"),
            ("מֹלְכִים", "mōlᵊkīm"),
            ("מֹלְכוֹת", "mōlᵊkōṯ"),
            # Passive Participle
            ("מָלוּךְ", "mālūk"),
            ("מְלוּכָה", "mᵊlūkāh"),
            ("מְלוּכִים", "mᵊlūkīm"),
            ("מְלוּכוֹת", "mᵊlūkōṯ"),
        ],
    },
    "למד": {
        "root_transliteration": "l-m-d",
        "citation": "לָמַד",
        "citation_transliteration": "lāmaḏ",
        "definition": "to learn",
        "forms": [
            # Perfect
            ("לָמַד", "lāmaḏ"),
            ("לָמְדָה", "lāmᵊḏāh"),
            ("לָמַדְתָּ", "lāmaḏtā"),
            ("לָמַדְתְּ", "lāmaḏt"),
            ("לָמַדְתִּי", "lāmaḏtī"),
            ("לָמְדוּ", "lāmᵊḏū"),
            ("לְמַדְתֶּם", "lᵊmaḏtem"),
            ("לְמַדְתֶּן", "lᵊmaḏten"),
            ("לָמַדְנוּ", "lāmaḏnū"),
            # Imperfect
            ("יִלְמַד", "yilmaḏ"),
            ("תִּלְמַד", "tilmaḏ"),
            ("תִּלְמַד", "tilmaḏ"),
            ("תִּלְמְדִי", "tilmᵊḏī"),
            ("אֶלְמַד", "ʾelmaḏ"),
            ("יִלְמְדוּ", "yilmᵊḏū"),
            ("תִּלְמַדְנָה", "tilmaḏnāh"),
            ("תִּלְמְדוּ", "tilmᵊḏū"),
            ("תִּלְמַדְנָה", "tilmaḏnāh"),
            ("נִלְמַד", "nilmaḏ"),
            # Imperative
            ("לְמַד", "lᵊmaḏ"),
            ("לִמְדִי", "limḏī"),
            ("לִמְדוּ", "limḏū"),
            ("לְמַדְנָה", "lᵊmaḏnāh"),
            # Infinitives
            ("לְמֹד", "lᵊmōḏ"),
            ("לָמוֹד", "lāmōḏ"),
            # Active Participle
            ("לֹמֵד", "lōmēḏ"),
            ("לֹמֶדֶת", "lōmeḏeṯ"),
            ("לֹמְדִים", "lōmᵊḏīm"),
            ("לֹמְדוֹת", "lōmᵊḏōṯ"),
            # Passive Participle
            ("לָמוּד", "lāmūḏ"),
            ("לְמוּדָה", "lᵊmūḏāh"),
            ("לְמוּדִים", "lᵊmūḏīm"),
            ("לְמוּדוֹת", "lᵊmūḏōṯ"),
        ],
    },
    "פקד": {
        "root_transliteration": "p-q-d",
        "citation": "פָּקַד",
        "citation_transliteration": "pāqaḏ",
        "definition": "to visit, appoint, number, punish",
        "forms": [
            # Perfect
            ("פָּקַד", "pāqaḏ"),
            ("פָּקְדָה", "pāqᵊḏāh"),
            ("פָּקַדְתָּ", "pāqaḏtā"),
            ("פָּקַדְתְּ", "pāqaḏt"),
            ("פָּקַדְתִּי", "pāqaḏtī"),
            ("פָּקְדוּ", "pāqᵊḏū"),
            ("פְּקַדְתֶּם", "pᵊqaḏtem"),
            ("פְּקַדְתֶּן", "pᵊqaḏten"),
            ("פָּקַדְנוּ", "pāqaḏnū"),
            # Imperfect
            ("יִפְקֹד", "yifqōḏ"),
            ("תִּפְקֹד", "tifqōḏ"),
            ("תִּפְקֹד", "tifqōḏ"),
            ("תִּפְקְדִי", "tifqᵊḏī"),
            ("אֶפְקֹד", "ʾefqōḏ"),
            ("יִפְקְדוּ", "yifqᵊḏū"),
            ("תִּפְקֹדְנָה", "tifqōḏnāh"),
            ("תִּפְקְדוּ", "tifqᵊḏū"),
            ("תִּפְקֹדְנָה", "tifqōḏnāh"),
            ("נִפְקֹד", "nifqōḏ"),
            # Imperative
            ("פְּקֹד", "pᵊqōḏ"),
            ("פִּקְדִי", "piqḏī"),
            ("פִּקְדוּ", "piqḏū"),
            ("פְּקֹדְנָה", "pᵊqōḏnāh"),
            # Infinitives
            ("פְּקֹד", "pᵊqōḏ"),
            ("פָּקוֹד", "pāqōḏ"),
            # Active Participle
            ("פֹּקֵד", "pōqēḏ"),
            ("פֹּקֶדֶת", "pōqeḏeṯ"),
            ("פֹּקְדִים", "pōqᵊḏīm"),
            ("פֹּקְדוֹת", "pōqᵊḏōṯ"),
            # Passive Participle
            ("פָּקוּד", "pāqūḏ"),
            ("פְּקוּדָה", "pᵊqūḏāh"),
            ("פְּקוּדִים", "pᵊqūḏīm"),
            ("פְּקוּדוֹת", "pᵊqūḏōṯ"),
        ],
    },
    "זכר": {
        "root_transliteration": "z-k-r",
        "citation": "זָכַר",
        "citation_transliteration": "zāḵar",
        "definition": "to remember",
        "forms": [
            # Perfect
            ("זָכַר", "zāḵar"),
            ("זָכְרָה", "zāḵᵊrāh"),
            ("זָכַרְתָּ", "zāḵartā"),
            ("זָכַרְתְּ", "zāḵart"),
            ("זָכַרְתִּי", "zāḵartī"),
            ("זָכְרוּ", "zāḵᵊrū"),
            ("זְכַרְתֶּם", "zᵊḵartem"),
            ("זְכַרְתֶּן", "zᵊḵarten"),
            ("זָכַרְנוּ", "zāḵarnū"),
            # Imperfect
            ("יִזְכֹּר", "yizkōr"),
            ("תִּזְכֹּר", "tizkōr"),
            ("תִּזְכֹּר", "tizkōr"),
            ("תִּזְכְּרִי", "tizkᵊrī"),
            ("אֶזְכֹּר", "ʾezkōr"),
            ("יִזְכְּרוּ", "yizkᵊrū"),
            ("תִּזְכֹּרְנָה", "tizkōrnāh"),
            ("תִּזְכְּרוּ", "tizkᵊrū"),
            ("תִּזְכֹּרְנָה", "tizkōrnāh"),
            ("נִזְכֹּר", "nizkōr"),
            # Imperative
            ("זְכֹר", "zᵊkōr"),
            ("זִכְרִי", "ziḵrī"),
            ("זִכְרוּ", "ziḵrū"),
            ("זְכֹרְנָה", "zᵊkōrnāh"),
            # Infinitives
            ("זְכֹר", "zᵊkōr"),
            ("זָכוֹר", "zāḵōr"),
            # Active Participle
            ("זֹכֵר", "zōḵēr"),
            ("זֹכֶרֶת", "zōḵereṯ"),
            ("זֹכְרִים", "zōḵᵊrīm"),
            ("זֹכְרוֹת", "zōḵᵊrōṯ"),
            # Passive Participle
            ("זָכוּר", "zāḵūr"),
            ("זְכוּרָה", "zᵊḵūrāh"),
            ("זְכוּרִים", "zᵊḵūrīm"),
            ("זְכוּרוֹת", "zᵊḵūrōṯ"),
        ],
    },
}


def _build_paradigm(root: str) -> VerbParadigm | None:
    """Build a VerbParadigm from stored data."""
    data = _VERB_DATA.get(root)
    if data is None:
        return None

    forms = []
    for i, (conj, person, number, gender, label) in enumerate(FORM_TEMPLATE):
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
        root=root,
        root_transliteration=data["root_transliteration"],
        citation=data["citation"],
        citation_transliteration=data["citation_transliteration"],
        definition=data["definition"],
        forms=forms,
    )


def available_roots() -> list[str]:
    """Return list of roots that have paradigm data."""
    return list(_VERB_DATA.keys())


def get_paradigm(root: str | None = None) -> VerbParadigm | None:
    """
    Get the full Qal paradigm for a verb root.
    If root is None, pick a random verb.
    """
    if root is None:
        root = random.choice(available_roots())
    return _build_paradigm(root)


def generate_worksheet(
    root: str | None = None,
    num_blanks: int = 10,
    conjugations: list[str] | None = None,
) -> QalWorksheet | None:
    """
    Generate a worksheet: a full paradigm with some forms blanked out.

    Args:
        root: Verb root (random if None).
        num_blanks: How many forms to blank out.
        conjugations: If provided, only blank forms from these conjugations
                      (e.g. ["perfect", "imperfect"]).
    """
    paradigm = get_paradigm(root)
    if paradigm is None:
        return None

    # Determine which indices are eligible for blanking
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

    return QalWorksheet(
        root=paradigm.root,
        root_transliteration=paradigm.root_transliteration,
        citation=paradigm.citation,
        citation_transliteration=paradigm.citation_transliteration,
        definition=paradigm.definition,
        forms=worksheet_forms,
        num_blanks=num_blanks,
    )


def _normalize_hebrew(text: str) -> str:
    """Normalize Hebrew text for comparison: strip whitespace, normalize unicode."""
    import unicodedata

    return unicodedata.normalize("NFC", text.strip())


def grade_worksheet(
    answers: list[tuple[int, str]],
    worksheet: QalWorksheet,
) -> list[WorksheetGradeResult]:
    """
    Grade worksheet answers.

    Args:
        answers: List of (form_index, submitted_hebrew) pairs.
        worksheet: The original worksheet for answer checking.

    Returns:
        List of grade results, one per submitted answer.
    """
    results = []
    for index, submitted in answers:
        if index < 0 or index >= len(worksheet.forms):
            continue
        form = worksheet.forms[index]
        expected = form.answer_hebrew
        correct = _normalize_hebrew(submitted) == _normalize_hebrew(expected)
        if correct:
            feedback = f"Correct! {form.label}: {expected} ({form.answer_transliteration})"
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
