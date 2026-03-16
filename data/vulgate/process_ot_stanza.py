"""
Process Clementine Vulgate OT with Stanza Latin PROIEL pipeline.
Produces ot_tokens.tsv in the same format as nt_tokens.tsv.

Source: scrollmapper/bible_databases VulgClementine.csv (MIT license)
Morphological tagging: Stanford Stanza Latin/PROIEL (Apache 2.0 model)
Note: Stanza training data includes CC BY-NC-SA materials (UD Latin PROIEL/ITTB).
"""

import csv
import sys
from pathlib import Path

import stanza

BASE = Path(__file__).parent

BOOK_MAP = {
    "Genesis": "GEN", "Exodus": "EXO", "Leviticus": "LEV",
    "Numbers": "NUM", "Deuteronomy": "DEU", "Joshua": "JOS",
    "Judges": "JDG", "Ruth": "RUT", "I Samuel": "1SAM",
    "II Samuel": "2SAM", "I Kings": "1KGS", "II Kings": "2KGS",
    "I Chronicles": "1CHR", "II Chronicles": "2CHR",
    "Ezra": "EZR", "Nehemiah": "NEH", "Tobit": "TOB",
    "Judith": "JDT", "Esther": "EST", "Job": "JOB",
    "Psalms": "PSA", "Proverbs": "PRO", "Ecclesiastes": "ECC",
    "Song of Solomon": "SNG", "Wisdom": "WIS", "Sirach": "SIR",
    "Isaiah": "ISA", "Jeremiah": "JER", "Lamentations": "LAM",
    "Baruch": "BAR", "Ezekiel": "EZK", "Daniel": "DAN",
    "Hosea": "HOS", "Joel": "JOL", "Amos": "AMO",
    "Obadiah": "OBA", "Jonah": "JON", "Micah": "MIC",
    "Nahum": "NAH", "Habakkuk": "HAB", "Zephaniah": "ZEP",
    "Haggai": "HAG", "Zechariah": "ZEC", "Malachi": "MAL",
    "I Maccabees": "1MAC", "II Maccabees": "2MAC",
}

# ── Feats → 10-char PROIEL morphology ────────────────────────────────────────

INDECLINABLE_UPOS = {"ADP", "CCONJ", "SCONJ", "ADV", "INTJ", "PART", "PUNCT", "X"}


def feats_to_proiel(upos: str, feats_str: str | None) -> str:
    f: dict[str, str] = {}
    if feats_str and feats_str != "_":
        for pair in feats_str.split("|"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                f[k] = v

    person = {"1": "1", "2": "2", "3": "3"}.get(f.get("Person", ""), "-")
    number = {"Sing": "s", "Plur": "p", "Dual": "d"}.get(f.get("Number", ""), "-")

    # tense: Aspect=Perf → perfect; Tense=Past → also perfect in Latin
    tense_raw = f.get("Tense", "")
    aspect = f.get("Aspect", "")
    tense = "-"
    if tense_raw == "Pres":
        tense = "p"
    elif tense_raw == "Imp":
        tense = "i"
    elif tense_raw in ("Past",) or aspect == "Perf":
        tense = "r"
    elif tense_raw == "Pqp" or aspect == "Pqp":
        tense = "l"
    elif tense_raw == "Fut":
        tense = "f"
    elif tense_raw == "FutPerf":
        tense = "t"

    # mood: from Mood + VerbForm
    verb_form = f.get("VerbForm", "")
    mood_raw = f.get("Mood", "")
    mood = "-"
    if verb_form == "Inf":
        mood = "n"
    elif verb_form == "Part":
        mood = "p"
    elif verb_form == "Ger":
        mood = "d"
    elif verb_form == "Gdv":
        mood = "g"
    elif verb_form == "Sup":
        mood = "u"
    elif mood_raw == "Ind":
        mood = "i"
    elif mood_raw == "Sub":
        mood = "s"
    elif mood_raw == "Imp":
        mood = "m"

    voice = {"Act": "a", "Pass": "p", "Mid": "m"}.get(f.get("Voice", ""), "-")
    gender = {"Masc": "m", "Fem": "f", "Neut": "n"}.get(f.get("Gender", ""), "-")
    case = {
        "Nom": "n", "Acc": "a", "Gen": "g", "Dat": "d",
        "Abl": "b", "Voc": "v", "Loc": "l",
    }.get(f.get("Case", ""), "-")
    degree = {"Pos": "p", "Cmp": "c", "Sup": "s"}.get(f.get("Degree", ""), "-")
    inflection = "n" if upos in INDECLINABLE_UPOS else "i"

    return f"{person}{number}{tense}{mood}{voice}{gender}{case}{degree}-{inflection}"


def main():
    in_path = BASE / "vulgclementine_raw.csv"
    out_path = BASE / "ot_tokens.tsv"

    # Load OT verses
    verses = []
    with open(in_path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            abbrev = BOOK_MAP.get(row["Book"])
            if abbrev is None:
                continue  # skip NT and extra-canonical books
            verses.append((abbrev, int(row["Chapter"]), int(row["Verse"]), row["Text"].strip()))

    print(f"Loaded {len(verses)} OT verses", flush=True)

    print("Loading Stanza Latin PROIEL pipeline...", flush=True)
    nlp = stanza.Pipeline(
        "la",
        package="proiel",
        processors="tokenize,pos,lemma,depparse",
        verbose=False,
        use_gpu=False,
    )
    print("Pipeline ready", flush=True)

    written = 0
    with open(out_path, "w", encoding="utf-8", newline="") as out:
        writer = csv.writer(out, delimiter="\t")
        writer.writerow(["ref", "book", "chapter", "verse", "token",
                         "form", "lemma", "pos", "morphology", "relation"])

        for i, (book, chapter, verse_num, text) in enumerate(verses):
            if not text:
                continue
            try:
                doc = nlp(text)
            except Exception as e:
                print(f"  Error {book} {chapter}:{verse_num}: {e}", file=sys.stderr, flush=True)
                continue

            token_num = 1
            for sent in doc.sentences:
                for word in sent.words:
                    if (word.upos or "") == "PUNCT":
                        continue
                    pos = word.xpos or "X-"
                    morph = feats_to_proiel(word.upos or "", word.feats)
                    ref = f"{book}.{chapter}.{verse_num}#{token_num:02d}"
                    writer.writerow([
                        ref, book, chapter, verse_num, token_num,
                        word.text, word.lemma or word.text,
                        pos, morph, word.deprel or "_",
                    ])
                    token_num += 1
                    written += 1

            if (i + 1) % 1000 == 0:
                pct = (i + 1) / len(verses) * 100
                print(f"  {i+1}/{len(verses)} verses ({pct:.1f}%) — {written} tokens written", flush=True)

    print(f"Done. {written} tokens written to {out_path}", flush=True)


if __name__ == "__main__":
    main()
