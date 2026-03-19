# Plan: Adding Targumim to the Hebrew Biblical Text Viewer

## Overview

This document details the full implementation plan for adding Targum support to the
Hebrew viewer (`TahotViewerPage`). The feature covers:

1. **Data acquisition** — fetching Aramaic Targum text and English translations from Sefaria
2. **Multiple Targum selection** — UI for choosing between Targumim where more than one exists
3. **Aramaic lexicon** — Jastrow dictionary integration for word lookup
4. **Frontend display** — text rendering, layout, and simultaneous Rashi+Targum view

---

## Part 1: Targum Corpus

### 1.1 Which Targumim Exist per Section

**Torah — four Targumim available on Sefaria:**

| Targum | Character |
|--------|-----------|
| **Onkelos** | Most authoritative; literal, close to MT; standard in synagogue use. Only Torah Targum with an English translation on Sefaria (Etheridge 1862, public domain). |
| **Pseudo-Jonathan** | Expansive paraphrase with midrashic additions; attributed to Jonathan b. Uzziel but is a later composite. Also called Targum Yerushalmi I. |
| **Neofiti** | Palestinian Targum discovered in 1956 in the Vatican library; complete manuscript. |
| **Fragment Targum** | Also called Targum Yerushalmi II; fragmentary text preserving Palestinian readings. |

Torah books covered: Genesis, Exodus, Leviticus, Numbers, Deuteronomy.

**Former Prophets — Targum Jonathan only:**

Joshua, Judges, 1–2 Samuel, 1–2 Kings. No competing Targum.

**Latter Prophets — Targum Jonathan only:**

Isaiah, Jeremiah, Ezekiel, and the Twelve (Hosea through Malachi). No competing Targum.

**Writings — one per book, except Esther:**

| Book | Targum | Notes |
|------|--------|-------|
| Psalms | Targum Psalms | |
| Proverbs | Targum Proverbs | |
| Job | Targum Job | |
| Song of Songs | Targum Song of Songs | Extensive midrashic allegorization |
| Ruth | Targum Ruth | |
| Lamentations | Targum Lamentations | |
| Ecclesiastes | Targum Qohelet | |
| Esther | **Targum Rishon** + **Targum Sheni** | Rishon = closer to MT; Sheni = greatly expanded |
| 1–2 Chronicles | Targum Chronicles | |

**Books with no Targum (already substantially Aramaic in MT):**

Ezra, Nehemiah, Daniel. We silently suppress the Targum toggle for these books.

---

### 1.2 Sefaria API Names

These are the known Sefaria text slugs. They should be verified against `https://www.sefaria.org/api/index/`
when writing the fetch script — Sefaria occasionally adjusts slug naming.

**Torah — Onkelos:**
```
Targum_Onkelos_Genesis
Targum_Onkelos_Exodus
Targum_Onkelos_Leviticus
Targum_Onkelos_Numbers
Targum_Onkelos_Deuteronomy
```

**Torah — Pseudo-Jonathan** (Sefaria labels this "Targum Jonathan on…" for Torah):
```
Targum_Jonathan_on_Genesis
Targum_Jonathan_on_Exodus
Targum_Jonathan_on_Leviticus
Targum_Jonathan_on_Numbers
Targum_Jonathan_on_Deuteronomy
```

**Torah — Neofiti:**
```
Targum_Neofiti_Genesis
Targum_Neofiti_Exodus
Targum_Neofiti_Leviticus
Targum_Neofiti_Numbers
Targum_Neofiti_Deuteronomy
```

**Torah — Fragment Targum:**
```
Fragment_Targum_Genesis
Fragment_Targum_Exodus
Fragment_Targum_Leviticus
Fragment_Targum_Numbers
Fragment_Targum_Deuteronomy
```

**Former + Latter Prophets — Jonathan:**
```
Targum_Jonathan_on_Joshua
Targum_Jonathan_on_Judges
Targum_Jonathan_on_I_Samuel
Targum_Jonathan_on_II_Samuel
Targum_Jonathan_on_I_Kings
Targum_Jonathan_on_II_Kings
Targum_Jonathan_on_Isaiah
Targum_Jonathan_on_Jeremiah
Targum_Jonathan_on_Ezekiel
Targum_Jonathan_on_Hosea
Targum_Jonathan_on_Joel
Targum_Jonathan_on_Amos
Targum_Jonathan_on_Obadiah
Targum_Jonathan_on_Jonah
Targum_Jonathan_on_Micah
Targum_Jonathan_on_Nahum
Targum_Jonathan_on_Habakkuk
Targum_Jonathan_on_Zephaniah
Targum_Jonathan_on_Haggai
Targum_Jonathan_on_Zechariah
Targum_Jonathan_on_Malachi
```

**Writings:**
```
Targum_on_Psalms
Targum_on_Proverbs
Targum_on_Job
Targum_on_Song_of_Songs
Targum_on_Ruth
Targum_on_Lamentations
Targum_on_Ecclesiastes
Targum_Rishon_on_Esther    (First Targum)
Targum_Sheni_on_Esther     (Second Targum)
Targum_on_I_Chronicles
Targum_on_II_Chronicles
```

> **Note on Writings naming:** Sefaria uses `Targum_on_X` for most Writings books (not `Targum_X`).
> This differs from the Torah and Prophets conventions. Verify each slug against the live index.

> **Note on naming:** Sefaria uses "Targum Jonathan on Genesis" etc. for Pseudo-Jonathan on
> the Torah. This is historically confusing (the same name is also used for the Prophets Targum)
> but is Sefaria's convention. Our UI should display the full traditional names:
> "Onkelos", "Pseudo-Jonathan", "Neofiti" — not the Sefaria API slug.

---

### 1.3 English Translations

Only **Targum Onkelos** has a confirmed English translation on Sefaria: the J.W. Etheridge
translation (1862), which is in the public domain. No English is available on Sefaria for
Pseudo-Jonathan, Neofiti, Fragment Targum, Jonathan on the Prophets, or any of the Writings
Targumim.

The fetch script should nonetheless attempt an English fetch for every Targum/book combination
using `?language=en`, store the result where text comes back non-empty, and gracefully skip
otherwise. This ensures we automatically pick up any new English translations Sefaria adds
in the future.

---

## Part 2: Data Acquisition Pipeline

### 2.1 Storage Layout

```
frontend/public/data/hebrew/targum/
  {abbrev}/{slug}/
    aramaic.json      # Aramaic text
    english.json      # English translation (where available)
```

Examples:
```
targum/gen/onkelos/aramaic.json
targum/gen/onkelos/english.json
targum/gen/pseudo_jonathan/aramaic.json
targum/gen/neofiti/aramaic.json
targum/est/rishon/aramaic.json
targum/est/sheni/aramaic.json
```

JSON format (same as rashi): `{ "1": { "1": "text…", "2": "text…" }, "2": { … } }`

### 2.2 Fetch Script: `data/hebrew/fetch_targum.py`

Modeled directly on `fetch_rashi.py`. Key differences:

- **Multi-targum map:** each TAHOT abbrev maps to a list of `(slug, display_name, sefaria_ref)` tuples
- **Two-pass fetch:** first Aramaic (`language=he`), then English (`language=en`) for each
- **Output directory:** per-targum subdirectory (see 2.1)
- **Depth detection:** Targum texts are depth-2 (Chapter.Verse), not depth-3 like Rashi, so
  the range fetch is `{ref}.{ch}.1-{n}` with the same `language=he&context=0` params —
  but verify against the API shape response, as a few Targumim (e.g. Pseudo-Jonathan)
  may contain sub-verse segments

```python
# Core data structure
TARGUMIM: dict[str, list[tuple[str, str, str]]] = {
    # abbrev → [(file_slug, display_name, sefaria_ref), ...]
    "Gen": [
        ("onkelos",         "Onkelos",         "Targum_Onkelos_Genesis"),
        ("pseudo_jonathan", "Pseudo-Jonathan",  "Targum_Jonathan_on_Genesis"),
        ("neofiti",         "Neofiti",          "Targum_Neofiti_Genesis"),
        ("fragment",        "Fragment Targum",  "Fragment_Targum_Genesis"),
    ],
    "Exo": [
        ("onkelos",         "Onkelos",         "Targum_Onkelos_Exodus"),
        ("pseudo_jonathan", "Pseudo-Jonathan",  "Targum_Jonathan_on_Exodus"),
        ("neofiti",         "Neofiti",          "Targum_Neofiti_Exodus"),
        ("fragment",        "Fragment Targum",  "Fragment_Targum_Exodus"),
    ],
    # … Lev, Num, Deu similarly with all four …
    "Jos": [("jonathan", "Targum Jonathan", "Targum_Jonathan_on_Joshua")],
    # … Former + Latter Prophets all single Targum …
    "Est": [
        ("rishon", "Targum Rishon", "Targum_Rishon_on_Esther"),
        ("sheni",  "Targum Sheni",  "Targum_Sheni_on_Esther"),
    ],
    # Writings use Targum_on_X pattern:
    "Psa": [("targum", "Targum Psalms",   "Targum_on_Psalms")],
    "Pro": [("targum", "Targum Proverbs", "Targum_on_Proverbs")],
    # … etc …
}

NO_TARGUM = {"Ezr", "Neh", "Dan"}
```

CLI usage (mirroring the Rashi script):
```bash
python data/hebrew/fetch_targum.py           # all books, all Targumim
python data/hebrew/fetch_targum.py Gen Exo   # specific books
python data/hebrew/fetch_targum.py --en-only # re-fetch English only
```

---

## Part 3: Aramaic Lexicon

### 3.1 Chosen Source: Jastrow Dictionary

**Jastrow's Dictionary of the Targumim, Talmud Babli and Yerushalmi, and the Midrashic
Literature** (Marcus Jastrow, 1903) is the standard reference for Targumic Aramaic. It is
in the public domain and is integrated into Sefaria's lexicon system.

**Option A — Live API (simpler to start):**

Sefaria exposes a lexicon lookup endpoint:
```
GET https://www.sefaria.org/api/words/{word}?lookup_ref={sefaria_ref}&with_lemmas=1
```
Returns Jastrow (and other lexicon) entries for the given word form. Fields:
- `headword`: dictionary entry form
- `transliteration`
- `content`: HTML definition
- `parent_lexicon`: e.g. "Jastrow Dictionary"

No bulk download needed — entries fetched on demand when a user clicks an Aramaic word.

**Option B — Bulk data from Sefaria Export (preferred long-term):**

The `github.com/Sefaria/Sefaria-Export` repository contains a full Jastrow JSON dump,
updated periodically. License: **CC-BY-NC**. Downloading and bundling this data
eliminates the runtime Sefaria dependency for lexicon lookups, gives faster response
times, and allows offline use.

If we go with Option B, the Jastrow JSON would be stored at
`backend/reshith/data/jastrow.json` and loaded into memory at startup by `jastrow.py`,
with a simple lemma-keyed lookup — analogous to how `tbesh.py` loads TBESH.txt.

**Recommended approach:** Start with Option A (live API via backend proxy) and migrate to
Option B once we have confirmed the data format from the Sefaria Export repo.

### 3.2 Alternative: STEPBible TBESH for OT Aramaic

The TBESH file already in the project (`data/hebrew/TBESH.txt`) contains entries for the
Aramaic portions of the Hebrew Bible (Daniel, Ezra) using H-numbers with Aramaic flag.
However, this covers only ~300 Aramaic lemmas from the MT, not the full Targumic vocabulary.
It is useful as a quick fallback for words shared between MT Aramaic and the Targumim.

### 3.3 Lexicon Integration Strategy

Because the Targum is displayed as a prose block (not word-by-word interlinear), lexicon
lookup is **user-initiated on a selected word**, not automatic per token:

1. User enables Targum display; sees Aramaic prose text
2. User double-clicks or selects an Aramaic word
3. Frontend sends a lookup request (either directly to Sefaria, or proxied through our
   backend) for that word form + the current Sefaria passage reference
4. Response is displayed in a popover/panel, same UX as the expanded `WordCard` for Hebrew

**Backend proxy approach (preferred):** Add a new GraphQL resolver `aramaic_lexicon_entry(word, passage_ref)` in `resolvers.py` that calls Sefaria's lexicon API and returns a structured entry. This avoids CORS issues with direct browser→Sefaria requests and lets us cache results.

```python
# New GraphQL type (types.py)
@strawberry.type
class AramaicLexiconEntry:
    word: str
    headword: str
    transliteration: str
    definition_html: str
    lexicon_name: str   # e.g. "Jastrow Dictionary"
```

### 3.4 Future: Morphological Analysis

A word-level Aramaic interlinear Targum (like our TAHOT Hebrew display) would require a
morphologically analyzed Targum corpus. The main candidates:

- **CALOT** (Comprehensive Aramaic Lexicon of the Old Testament) — Göttingen corpus,
  restricted access
- **CAL** (Comprehensive Aramaic Lexicon, cal.huc.edu) — web interface only, no bulk API
- **Accordance/Logos** — commercial, not open

This is explicitly **out of scope** for this phase. The Targum is displayed as prose,
analogous to Rashi, not as an interlinear.

---

## Part 4: Frontend Integration

### 4.1 State Shape

New state in `TahotViewerPage.tsx`:

```typescript
// Which Targumim are loaded (keyed by "{abbrev}/{slug}")
const [targumData, setTargumData] = useState<
  Record<string, Record<string, Record<string, string>>>
>({});

// Whether Targum layer is shown
const [showTargum, setShowTargum] = useState(false);

// Currently selected Targum slug per book (persisted to localStorage)
const [selectedTargum, setSelectedTargum] = useState<Record<string, string>>({});

// "flow" | "side" layout (shared toggle with Rashi or independent?)
const [targumLayout, setTargumLayout] = useState<"flow" | "side">("flow");

// Loading state
const [targumLoading, setTargumLoading] = useState(false);

// Whether to show English Targum translation (when available)
const [showTargumEnglish, setShowTargumEnglish] = useState(false);
```

### 4.2 Static Metadata: Available Targumim per Book

A constant in the component (or a shared constants file) maps each book abbreviation to
its available Targumim:

```typescript
// frontend/src/data/targumim.ts
export type TargumMeta = {
  slug: string;
  displayName: string;
  shortName: string;  // for toggle buttons: "Onk", "P-J", "Neof", "Jon"
  hasEnglish: boolean;  // set after running fetch script
};

export const BOOK_TARGUMIM: Record<string, TargumMeta[]> = {
  Gen: [
    { slug: "onkelos",         displayName: "Targum Onkelos",        shortName: "Onk",  hasEnglish: true  },
    { slug: "pseudo_jonathan", displayName: "Targum Pseudo-Jonathan",shortName: "P-J",  hasEnglish: false },
    { slug: "neofiti",         displayName: "Targum Neofiti",        shortName: "Neof", hasEnglish: false },
    { slug: "fragment",        displayName: "Fragment Targum",       shortName: "Frag", hasEnglish: false },
  ],
  // … Exo, Lev, Num, Deu same four …
  Jos: [{ slug: "jonathan", displayName: "Targum Jonathan", shortName: "Jon", hasEnglish: false }],
  // … Former + Latter Prophets all single Jonathan entry …
  Est: [
    { slug: "rishon", displayName: "Targum Rishon", shortName: "TgI",  hasEnglish: false },
    { slug: "sheni",  displayName: "Targum Sheni",  shortName: "TgII", hasEnglish: false },
  ],
  // Writings: single targum per book, slug "targum"
  Psa: [{ slug: "targum", displayName: "Targum Psalms",   shortName: "TgPs", hasEnglish: false }],
  // … etc …
};

export const NO_TARGUM_BOOKS = new Set(["Ezr", "Neh", "Dan"]);
```

`hasEnglish` can be set once after running the fetch script by checking which `english.json`
files exist.

### 4.3 Toggle Button UI

The **Targum** button appears in the control strip alongside the Rashi button. When the
current book has multiple Targumim, a compact selector appears next to the toggle (only
when the toggle is on). When only one Targum exists for the book, no selector is shown.

Mockup:
```
[ Targum ▼ ]  [ Onk | P-J | Neof ]  [ flow | side ]  [ EN ]
```

- `▼` is just the toggle indicator (active/inactive), not a dropdown
- The Targum selector uses the same style as the existing Rashi layout switcher
- `[ EN ]` appears (enabled/disabled) only when `hasEnglish: true` for the selected Targum

When the book changes, `selectedTargum[newBook]` defaults to the first available Targum
(i.e., Onkelos for Torah, Jonathan for Prophets, Rishon for Esther).

### 4.4 On-Demand Fetch

```typescript
useEffect(() => {
  if (!showTargum || !currentBook) return;
  const metas = BOOK_TARGUMIM[currentBook];
  if (!metas) return;  // No Targum for this book (Dan, Ezr, Neh)

  const slug = selectedTargum[currentBook] ?? metas[0].slug;
  const cacheKey = `${currentBook}/${slug}`;
  if (targumData[cacheKey]) return;  // already loaded

  setTargumLoading(true);
  const abbrev = currentBook.toLowerCase();
  fetch(`/data/hebrew/targum/${abbrev}/${slug}/aramaic.json`)
    .then(r => r.json())
    .then(d => {
      setTargumData(prev => ({ ...prev, [cacheKey]: d }));
      setTargumLoading(false);
    });
}, [showTargum, currentBook, selectedTargum]);
```

When the user switches to a different Targum for the same book, the same effect re-runs
with the new slug.

### 4.5 Layout: Targum Text Display

The Targum is displayed as a prose block per verse, analogous to Rashi. The existing
`CommentaryFlow` / `CommentaryFlowItem` components are reused with a `variant` prop to
distinguish Targum styling from Rashi styling.

**Visual distinction from Rashi:**
- Rashi: warm sepia/brown tone, smaller font (it's a commentary)
- Targum: cool blue/teal tone, same size as the Hebrew (it's a translation, not a gloss)
- Label above each Targum block: the `shortName` (e.g., "Onk", "Jon") in a small badge

**Aramaic rendering:**
- Uses the same `dir="rtl"` and Hebrew square-script font as the main text
- Since Targumic Aramaic uses the same alphabet, no special font is needed
- The Aramaic should be visually similar in weight to the Hebrew, not shrunk like Rashi

### 4.6 When Rashi and Targum Are Both Visible

Default strategy: **stacked flow** — in the commentary column (or flow-position),
Targum appears first (as a translation companion to the Hebrew), then Rashi below it.

Rationale: The Targum is a translation (same level as the verse), while Rashi is a
commentary on the verse. Displaying Targum first, then Rashi, matches the natural
reading order.

For the side-by-side layout, when both are active, offer a tab selector on the commentary
column:  `[ Targum | Rashi | Both ]` — "Both" stacks them vertically in the panel.

### 4.7 Lexicon Popover for Aramaic Words

When the user double-clicks an Aramaic word in the Targum text:

1. Extract the clicked word (using browser selection or a word-tokenization pass on the
   text string — split on whitespace + punctuation)
2. Dispatch a new GraphQL query `ARAMAIC_LEXICON_ENTRY` with the word and the current
   Sefaria passage ref (e.g., `"Genesis 1.1"`)
3. Display result in a small popover or in the existing detail panel (same position used
   by the expanded `WordCard` for Hebrew words)

The popover shows: headword, transliteration, HTML definition from Jastrow.

If no Jastrow entry is found, fall back to a TBESH lookup (for MT Aramaic overlap) and
then display "No lexicon entry found" if both fail.

---

## Part 5: Backend Changes

### 5.1 New GraphQL Resolver: `aramaic_lexicon_entry`

In `backend/reshith/api/resolvers.py`:

```python
@strawberry.field
def aramaic_lexicon_entry(self, word: str, passage_ref: str = "") -> AramaicLexiconEntry | None:
    return services.jastrow.lookup(word, passage_ref)
```

### 5.2 New Service: `backend/reshith/services/jastrow.py`

Calls Sefaria's lexicon API:
```
GET https://www.sefaria.org/api/words/{word}?lookup_ref={passage_ref}&with_lemmas=1
```

Parses the response and returns the first Jastrow entry found, or `None`.

Add simple in-process caching (dict) to avoid re-fetching the same words.

### 5.3 New GraphQL Type (in `types.py`)

```python
@strawberry.type
class AramaicLexiconEntry:
    word: str
    headword: str
    transliteration: str
    definition_html: str
    lexicon_name: str
```

### 5.4 No New Database Tables

Jastrow entries are fetched live from Sefaria and cached in memory. No schema migration
is needed.

---

## Part 6: UI Polish

- **Books without Targum** (Dan, Ezr, Neh): hide the Targum toggle entirely for these books,
  or show it greyed out with tooltip "No Targum (text is partially Aramaic)"
- **Partial verse coverage:** Some Targumim have gaps (missing verses). Display nothing for
  empty verses — same pattern as Rashi gaps
- **Loading state:** use the same spinner/skeleton pattern as the Rashi loading state
- **Persist selection:** store `selectedTargum` and `showTargum` in localStorage so they
  survive page reload, same as other view toggles
- **Attribution:** add source credit to Sefaria for Targum texts (same pattern as Rashi credit)
- **Mobile:** ensure the Targum selector (Onk / P-J / Neof) wraps gracefully on narrow screens
- **Book dropdown indicator:** add a small "TG" dot to books with Targum support in the
  book selector, similar to any existing Rashi availability indicator

---

## Implementation Order

| Step | Task | Notes |
|------|------|-------|
| 1 | Verify Sefaria API slugs | Run against `/api/index/` before writing full fetch script |
| 2 | `data/hebrew/fetch_targum.py` | Data pipeline; validate with `Gen` only first |
| 3 | Run fetch for all books | Populate `frontend/public/data/hebrew/targum/` |
| 4 | `frontend/src/data/targumim.ts` | Static metadata constant |
| 5 | State + fetch logic in `TahotViewerPage.tsx` | Wire up toggle and on-demand load |
| 6 | Targum block display (reuse CommentaryFlow) | Aramaic prose rendering |
| 7 | Multi-targum selector UI | Only for Torah + Esther initially |
| 8 | Rashi+Targum simultaneous layout | Stacked flow |
| 9 | `jastrow.py` service + GraphQL resolver | Backend lexicon proxy |
| 10 | Aramaic word-click popover in frontend | UX for lexicon lookup |
| 11 | English translation toggle | For books/Targumim with English available |
| 12 | Polish: attribution, persistence, mobile | |

---

## Open Questions

1. **English Targum fetch strategy:** Only Onkelos has confirmed English on Sefaria
   (Etheridge 1862). The fetch script will attempt English for all combinations and store
   where non-empty. The `hasEnglish` flag in `targumim.ts` should be set after the first
   run. For now, only Onkelos is expected to populate the English files.

2. **Simultaneous Rashi + Targum layout:** The stacked-flow default works, but the
   side-by-side mode with two commentary columns could be powerful for study. Worth a
   three-column layout option (Hebrew | Targum | Rashi)?

3. **Font for Aramaic:** The existing Hebrew font renders Aramaic correctly since they
   share the same Unicode block. But Targumic script sometimes uses square script
   conventions that differ slightly from Tiberian Hebrew. Is a dedicated Aramaic font
   (e.g., a font optimized for Eastern/Babylonian pointing) desired?

4. **Pseudo-Jonathan naming:** Sefaria calls this "Targum Jonathan on Genesis" for Torah.
   Our UI will call it "Pseudo-Jonathan" (the more accurate name used in scholarship).
   Confirm this is the right choice.

5. **Jastrow proxy vs. direct fetch:** The backend proxy approach adds latency vs. a direct
   browser fetch to `sefaria.org`. A client-side fetch is simpler but creates a Sefaria
   dependency in the browser. Which is preferred?
