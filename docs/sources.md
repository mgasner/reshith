# Data Sources, Licenses, and Copyright

This file records every external data source used in Reshith, its provenance, license, and where it lives in the repository. Keep it up to date whenever a new source is added.

---

## Corpora

### STEPBible TAHOT — Translators Amalgamated Hebrew Old Testament
- **Description:** Every word of the Leningrad Codex tagged with disambiguated Extended Strong's numbers, ETCBC morphology, and English glosses. Covers the full Hebrew OT (39 books).
- **Source:** https://github.com/STEPBible/STEPBible-Data (Tyndale House, Cambridge / STEPBible.org)
- **License:** CC BY 4.0
- **Attribution required:** Yes — "Data from STEPBible.org CC BY"
- **Repo path:** `data/hebrew/tahot_raw/`
- **Processing script:** `data/hebrew/process_tahot.py`

### STEPBible TANTT — Translators Amalgamated Greek New Testament
- **Description:** Greek NT text (NA28 base) with morphological tagging and Extended Strong's numbers.
- **Source:** https://github.com/STEPBible/STEPBible-Data
- **License:** CC BY 4.0
- **Attribution required:** Yes — "Data from STEPBible.org CC BY"
- **Repo path:** `data/nt_greek/TANTT.txt`
- **Processing script:** `data/nt_greek/prepare_gnt.py`

### STEPBible TALXX — Translators Amalgamated Septuagint (LXX)
- **Description:** Greek Septuagint text with morphological tagging and Strong's numbers.
- **Source:** https://github.com/STEPBible/STEPBible-Data
- **License:** CC BY 4.0
- **Attribution required:** Yes — "Data from STEPBible.org CC BY"
- **Repo path:** `data/nt_greek/TALXX.txt`
- **Processing script:** `data/nt_greek/prepare_lxx.py`

### PROIEL Latin NT Treebank
- **Description:** Human-reviewed dependency treebank of the Latin New Testament (27 books) — Vulgate. Provides lemma, POS, morphology, and syntactic dependency for the Vulgate NT interlinear.
- **Source:** https://github.com/proiel/proiel-treebank
- **License:** CC BY-NC-SA 4.0
- **Attribution required:** Yes. **Non-commercial only.**
- **Repo path:** `data/vulgate/latin-nt.xml`
- **Processing script:** `data/vulgate/process_proiel.py`

### Scrollmapper Clementine Vulgate
- **Description:** Latin Vulgate (Clementine edition) OT text used as source for the Vulgate OT interlinear.
- **Source:** https://github.com/scrollmapper/bible_databases (VulgClementine.csv)
- **License:** MIT
- **Attribution required:** Yes (MIT attribution)
- **Repo path:** `data/vulgate/vulgclementine_raw.csv`
- **Processing script:** `data/vulgate/process_ot_stanza.py`

### DCS — Digital Corpus of Sanskrit (Oliver Hellwig)
- **Description:** CoNLL-U annotated Sanskrit corpus covering Mahābhārata, Hitopadeśa, Manusmṛti, and Ṛgveda. Powers the Sanskrit reader interlinear.
- **Source:** https://github.com/OliverHellwig/sanskrit
- **License:** CC BY 4.0
- **Attribution required:** Yes — credit Oliver Hellwig / DCS
- **Repo path:** `data/sanskrit/dcs_cache/`
- **Processing script:** `data/sanskrit/fetch_dcs.py`

### GRETIL — Hitopadeśa Text (Nārāyaṇa)
- **Description:** Plain-text TEI transformation of the Hitopadeśa from the Göttingen Register of Electronic Texts in Indian Languages. Used as a reference for story boundary identification in DCS data.
- **Source:** http://gretil.sub.uni-goettingen.de/gretil/corpustei/sa_nArAyaNa-hitopadeza.xml
- **License:** CC BY-NC-SA 4.0
- **Attribution required:** Yes. **Non-commercial only.**
- **Repo path:** `data/sanskrit/dcs_cache/hitopadesa_gretil.txt`

### Beowulf — Old English Text (Harrison & Sharp edition, Wikisource)
- **Description:** Old English text of Beowulf in the Harrison and Sharp edition (1883), fetched via the Wikisource API.
- **Source:** https://en.wikisource.org/wiki/Beowulf_(Harrison_and_Sharp)
- **License:** Public domain
- **Repo path:** `frontend/public/data/old_english/beowulf.json`
- **Processing script:** `data/old_english/process_beowulf.py`

---

## Lexica

### STEPBible TBESH — Translators Brief Extended Strong's Lexicon (Hebrew)
- **Description:** Hebrew lexicon keyed by Extended Strong's numbers, with glosses and morphological codes. Based on abridged Brown-Driver-Briggs (BDB) with Tyndale House edits.
- **Source:** https://github.com/STEPBible/STEPBible-Data
- **License:** CC BY 4.0. Note: the "Meaning" field derives from Online Bible's Abridged BDB — obtain Online Bible's permission for any commercial use.
- **Attribution required:** Yes — "Data from STEPBible.org CC BY"
- **Repo path:** `data/hebrew/TBESH.txt`

### STEPBible TBESG — Translators Brief Extended Strong's Lexicon (Greek)
- **Description:** Greek lexicon (NT and LXX) keyed by Extended Strong's numbers. Based on Abbott-Smith definitions with Middle Liddell supplementation.
- **Source:** https://github.com/STEPBible/STEPBible-Data
- **License:** CC BY 4.0
- **Attribution required:** Yes — "Data from STEPBible.org CC BY"
- **Repo path:** `data/greek/TBESG.txt`

### Cologne Digital Sanskrit Dictionaries — Monier-Williams (1899)
- **Description:** Monier-Williams Sanskrit-English Dictionary (1899), accessed via the Cologne Sanskrit Lexicon API to build a lexicon for Lanman selection lemmas.
- **Source:** https://www.sanskrit-lexicon.uni-koeln.de/
- **License:** Dictionary: public domain (1899). Cologne API and digital edition: CC BY-SA 4.0.
- **Attribution required:** Yes (CC BY-SA — share-alike applies to derivatives)
- **Repo path:** `data/sanskrit/mw.txt` (raw), `data/sanskrit/mw_cache.json` (cache)
- **Processing script:** `data/sanskrit/build_lanman_lexicon.py`

### DICTLINE — Whitaker's Words Latin Lexicon
- **Description:** Machine-readable Latin dictionary from William Whitaker's Words project (1993–2010). Contains Latin lemmas, parts of speech, definitions, and morphological data.
- **Source:** Whitaker's Words project (public domain)
- **License:** Public domain
- **Repo path:** `data/latin/lexicon/DICTLINE.GEN`

### Gesenius' Hebrew Grammar (GKC)
- **Description:** Gesenius-Kautzsch-Cowley, 28th edition (1910), the standard reference grammar of Biblical Hebrew. Used for semantic/keyword search to inject grammar context into LLM translation explanations.
- **Source:** Public domain (A.E. Cowley's 1910 English translation)
- **License:** Public domain
- **Repo path:** `data/references/gesenius_hebrew_grammar.txt`; embedding index at `data/references/gesenius_index.jsonl`
- **Processing script:** `scripts/build_gesenius_index.py`

---

## Translations

### Scrollmapper KJV NT
- **Description:** King James Version New Testament (27 books).
- **Source:** https://github.com/scrollmapper/bible_databases (`t_kjv.json`)
- **License:** Public domain
- **Repo path:** `data/nt_greek/kjv_nt.json`

### Scrollmapper Brenton LXX English Translation
- **Description:** Sir Lancelot Brenton's English translation of the Septuagint (1844).
- **Source:** https://github.com/scrollmapper/bible_databases (`t_lxx.json`)
- **License:** Public domain
- **Repo path:** `data/nt_greek/brenton_lxx.json`

### Scrollmapper JPS 1917 — Hebrew OT Translation
- **Description:** Jewish Publication Society 1917 English translation of the Hebrew Bible (39 books).
- **Source:** https://github.com/scrollmapper/bible_databases
- **License:** Public domain
- **Repo path:** `data/hebrew/jps1917.json`

### Beowulf — J. Lesslie Hall Translation (1892)
- **Description:** Prose translation of Beowulf by J. Lesslie Hall (1892), from Project Gutenberg #16328.
- **Source:** https://www.gutenberg.org/cache/epub/16328/pg16328.txt
- **License:** Public domain
- **Repo path:** `frontend/public/data/old_english/beowulf.json` (combined with OE text above)

---

## Commentaries

### Sefaria — Rashi Commentary (Hebrew)
- **Description:** Rashi's medieval Hebrew commentary on the Hebrew Bible (36 books; Chronicles omitted intentionally). Fetched as Hebrew HTML via the Sefaria API.
- **Source:** https://www.sefaria.org/api/texts (`Rashi_on_Genesis`, etc.)
- **License:** Rashi's text (11th c.) is public domain. Sefaria's API terms of service apply; see https://www.sefaria.org/terms.
- **Repo path:** `frontend/public/data/hebrew/rashi/`, enriched data in `data/rashi_enriched/`
- **Processing script:** `data/hebrew/fetch_rashi.py`

### Sefaria — Kitzur Baal HaTurim Commentary (Hebrew)
- **Description:** The abridged Baal HaTurim Torah commentary (Pentateuch only, 5 books). Fetched as Hebrew HTML via the Sefaria API.
- **Source:** https://www.sefaria.org/api/texts (`Kitzur_Ba'al_HaTurim_on_Genesis`, etc.)
- **License:** Medieval text, public domain. Sefaria API terms apply.
- **Repo path:** `frontend/public/data/hebrew/baal_haturim/`
- **Processing script:** `data/hebrew/fetch_baal_haturim.py`

### Douay-Rheims Challoner (DRC) Commentary
- **Description:** English commentary notes from the Douay-Rheims Challoner revision (1749/1752). Stored as pre-bundled structured JSON alongside the Vulgate corpus.
- **Source:** Pre-bundled (not fetched by a script). Original is public domain.
- **License:** Public domain (pre-1927)
- **Repo path:** `data/vulgate/drc.json`

---

## APIs and NLP Services

### Sefaria — BDB and Jastrow Lexicons (Word API)
- **Description:** Brown-Driver-Briggs (BDB) Biblical Hebrew and Jastrow Talmudic/Mishnaic Aramaic dictionary entries, used to enrich Rashi commentary tokens with definitions.
- **Source:** `https://www.sefaria.org/api/words/{word}`
- **License:** BDB (1906) and Jastrow (1903) dictionaries are public domain. Sefaria API terms apply.
- **Repo path:** Cached in `data/.pipeline_cache/`
- **Processing script:** `backend/scripts/rashi_pipeline/sefaria_lexicon.py`

### Dicta Nakdan API — Hebrew/Aramaic Morphological Analysis
- **Description:** Morphological analysis (lemmatization, vowelization, POS tagging) of Hebrew and Aramaic tokens in Rashi commentary text.
- **Source:** `https://nakdan-u1-0.loadbalancer.dicta.org.il/api` (Dicta — The Center for Digital Humanities at the National Library of Israel)
- **License:** API use; no explicit open-content license documented. Do not redistribute raw API responses.
- **Repo path:** Cached in `data/.pipeline_cache/`
- **Processing script:** `backend/scripts/rashi_pipeline/dicta_client.py`

### Stanford Stanza Latin NLP Model
- **Description:** Python NLP library with a Latin model trained on UD Latin PROIEL/ITTB data. Used to automatically tag the Clementine Vulgate OT with lemmas, POS, and morphology.
- **Source:** https://stanfordnlp.github.io/stanza/
- **License:** Model binary: Apache 2.0. Training data includes CC BY-NC-SA material from UD Latin PROIEL/ITTB — this constrains downstream use.
- **Repo path:** Runtime only (not stored in repo)
- **Processing script:** `data/vulgate/process_ot_stanza.py`

---

## Pedagogical Texts

### Lanman's Sanskrit Reader (PDF)
- **Description:** Charles Rockwell Lanman, *A Sanskrit Reader* (1884; 1963 reprint). A pedagogical anthology used as the table of contents and selection list for the Sanskrit reader. OCR'd to extract Devanagari text for conversion to IAST.
- **Source:** Manually supplied PDF at `pdf/Lanman's_Sanskrit_Reader.pdf`
- **License:** 1884 original: public domain. The 1963 Harvard reprint may carry a copyright interest — do not redistribute the PDF or derived text commercially without review.
- **Repo path:** `pdf/Lanman's_Sanskrit_Reader.pdf`; output at `frontend/public/data/sanskrit/lanman.json`
- **Processing script:** `data/sanskrit/process_lanman.py`

---

## Fonts

### Gveret Levin (Alef Alef Alef)
- **Description:** Hebrew handwritten-script font used for alphabet flashcard handwriting mode.
- **Source:** https://alefalefalef.co.il/en/resources/
- **License:** Free for print, app, and web use per the Alef Alef Alef website. No OSI open-source license; check the site for the current terms before redistribution.
- **Repo path:** `frontend/public/fonts/GveretLevinAlefAlefAlef-Regular.woff`, `.woff2`

### NachlieliCLM-Light (Culmus Project)
- **Description:** OTF Hebrew font from the Culmus open-source Hebrew font project, used as a fallback.
- **Source:** https://culmus.sourceforge.io/
- **License:** GPL
- **Repo path:** `frontend/public/fonts/NachlieliCLM-Light.otf`

---

## License Compatibility Notes

| License | Commercial use? | Derivatives? | Share-alike? |
|---|---|---|---|
| CC BY 4.0 | Yes | Yes | No |
| CC BY-SA 4.0 | Yes | Yes | **Yes — derivatives must use CC BY-SA** |
| CC BY-NC-SA 4.0 | **No** | Yes | **Yes** |
| MIT | Yes | Yes | No |
| Apache 2.0 | Yes | Yes | No |
| GPL | Yes | Yes | **Yes — derivatives must be GPL** |
| Public domain | Yes | Yes | No |

Sources under **CC BY-NC-SA 4.0** (PROIEL, GRETIL) restrict commercial use and require share-alike. Any product that incorporates those data files must be non-commercial or relicensed under compatible terms.

The Stanza Latin model's training data includes CC BY-NC-SA material, which may impose non-commercial constraints on annotated outputs derived from it.
