# Reshith — Agent Guide

Reshith is a language-learning platform for classical and Biblical languages (Hebrew, Latin, Greek, Sanskrit, and others). It has a Python/GraphQL backend and a React/TypeScript frontend.

---

## Repository Layout

```
reshith/
├── backend/            Python package (FastAPI + Strawberry GraphQL)
├── frontend/           React + TypeScript (Vite)
├── data/               Language corpora, lesson files, lexica
├── backend/scripts/    Utility/pipeline scripts (not part of the server)
├── run.sh              Dev launcher (starts both servers, watches deps)
└── Makefile            Convenience targets: dev, test, dev_install
```

---

## Running the project

```bash
make dev            # start backend (port 8000) + frontend (port 5173)
make backend        # backend only
make frontend       # frontend only
make test           # pytest + ruff
```

Backend runs with `uv`. Frontend uses `npm`. The `run.sh` script handles dependency watching and restarts.

To verify the GraphQL schema compiles without starting the full server:
```bash
cd backend && uv run python -c "from reshith.api.schema import schema; print('OK')"
```

---

## Backend

### Stack

- **FastAPI** — ASGI web framework
- **Strawberry** — GraphQL schema, types, and resolvers
- **SQLAlchemy 2 (async)** + **asyncpg** — PostgreSQL ORM
- **Alembic** — Migrations (`backend/alembic/versions/`)
- **uv** — Package/env manager (replaces pip/venv)
- **ruff** — Linter; **mypy** — Type checker (Strawberry plugin enabled)

### Package structure

```
backend/reshith/
├── api/
│   ├── schema.py       # Strawberry Query + Mutation classes
│   ├── types.py        # All @strawberry.type / @strawberry.input / @strawberry.enum
│   └── resolvers.py    # All resolver + mutator functions
├── core/
│   ├── config.py       # Settings (pydantic-settings, reads backend/.env)
│   └── dependencies.py # FastAPI DI helpers (DB session, current user)
├── db/
│   ├── models.py       # ORM models: User, Deck, Card, SRSState, Review, LexiconEntry
│   ├── session.py      # Async session factory
│   └── seed.py         # Dev seed data (runs when debug=True)
├── exercises/          # Exercise generators (see below)
├── languages/          # Language modules (transliteration, normalization)
└── services/           # Business logic and external integrations
    ├── auth.py         # JWT encode/decode (bcrypt passwords)
    ├── llm.py          # OpenAI: translation help, drill generation
    ├── srs.py          # SM-2 spaced repetition algorithm
    ├── tahot.py        # TAHOT Hebrew OT corpus parser + index
    ├── tbesh.py        # TBESH/TBESG Extended Strong's lexicon
    ├── tts.py          # Google Cloud TTS (Hebrew) + MMS-TTS (Latin)
    └── vulgate.py      # Vulgate Latin corpus parser + index
```

### Configuration

`backend/.env` (not committed). Key variables:

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://localhost:5432/reshith` | Postgres |
| `OPENAI_API_KEY` | `""` | Translation help + drill generation |
| `OPENAI_MODEL` | `gpt-4o` | Model used by llm.py |
| `GOOGLE_CLOUD_API_KEY` | `""` | Google TTS (Hebrew, etc.) |
| `JWT_SECRET` | `dev-secret-change-in-production` | Auth tokens |
| `DEBUG` | `false` | Enables seed data on startup |

### Adding a GraphQL field

1. **Define types** in `api/types.py` using `@strawberry.type` / `@strawberry.input` / `@strawberry.enum`.
2. **Write the resolver** in `api/resolvers.py` as a plain function or async function.
3. **Add the field** to `Query` or `Mutation` in `api/schema.py` with `@strawberry.field` or `@strawberry.mutation`.
4. **Export the resolver** in the `schema.py` import block.

Strawberry converts `snake_case` Python to `camelCase` GraphQL automatically — don't rename manually.

### Adding an exercise type

Each exercise type follows this pattern:

1. **`backend/reshith/exercises/<language>/<type>.py`** — Generator:
   - `load_lessons_up_to(max_lesson)` → list of vocabulary items from `data/<language>/lesson*.json`
   - Dataclass for the exercise object
   - `generate_<type>_exercises(count, max_lesson, ...) -> list[Exercise]`
   - A grading function `grade_<type>_exercise(input) -> GradeResult`

2. **`api/types.py`** — Add `@strawberry.type` for the exercise and grade result, `@strawberry.input` for grade input.

3. **`api/resolvers.py`** — Add `resolve_<type>_exercises(...)` and `mutate_grade_<type>_exercise(...)`.

4. **`api/schema.py`** — Wire up query and mutation fields.

5. **`frontend/src/graphql/operations.ts`** — Add `GET_<TYPE>_EXERCISES` query and `GRADE_<TYPE>_EXERCISE` mutation.

6. **`frontend/src/pages/<Type>ExercisePage.tsx`** — New page using `useLazyQuery` + `useMutation` + `<ExerciseRunner>`.

7. **`frontend/src/App.tsx`** — Add route.

### Corpus services (TAHOT, Vulgate)

Both services parse TSV/JSON files at startup and build an in-memory index (book → chapter → verse → tokens). They expose:

- `get_index()` — returns the full parsed index (lazy, cached)
- `get_range(book, start_ch, start_v, end_ch, end_v)` — returns `dict[(ch, v), [Token]]`
- `get_chapter_verse_counts(book)` — returns `dict[chapter, verse_count]`

The `interlinear_passage` GraphQL field is the generic entry point — `source="TAHOT"` dispatches to tahot service. New corpora should follow the same pattern.

---

## Frontend

### Stack

- **React 18** + **TypeScript**
- **Vite** — dev server (port 5173) + bundler
- **React Router v7** — file-based-style routing defined in `App.tsx`
- **Apollo Client** — GraphQL queries/mutations with normalized cache
- **TailwindCSS** — utility-first CSS

### Source structure

```
frontend/src/
├── App.tsx             # All route definitions
├── main.tsx            # React root, Apollo + Router providers
├── graphql/
│   └── operations.ts   # Every gql query and mutation (single file)
├── pages/              # One component per route (40+ pages)
├── components/         # Shared UI components
│   ├── Layout.tsx      # Nav header + <Outlet>
│   ├── ExerciseRunner.tsx  # Generic exercise UI
│   ├── SpeakButton.tsx     # TTS trigger
│   └── ...
├── contexts/           # React contexts (AuthContext, etc.)
├── hooks/              # Custom hooks
└── utils/              # hebrewTranslit.ts, etc.
```

### Routing conventions

| Path prefix | Content |
|---|---|
| `/hebrew/*` | Hebrew lessons, alphabet, vowels |
| `/exercises/hebrew/*` | Hebrew exercises |
| `/latin/*` | Classical Latin |
| `/exercises/latin/*` | Latin exercises |
| `/nt-greek/*` | Koine/NT Greek |
| `/exercises/nt-greek/*` | NT Greek exercises |
| `/ecclesiastical-latin/*` | Ecclesiastical Latin |
| `/sanskrit/*` | Sanskrit |
| `/exercises/sanskrit/*` | Sanskrit exercises |

### Exercise page pattern

```tsx
// 1. Fetch exercises on demand
const [fetchExercises, { data, loading }] = useLazyQuery(GET_FOO_EXERCISES)

// 2. Grade on submit
const [gradeExercise] = useMutation(GRADE_FOO_EXERCISE)

// 3. Render
<ExerciseRunner
  prompt={current.prompt}
  onSubmit={(answer) => gradeExercise({ variables: { input: { ... } } })}
  feedback={gradeResult}
/>
```

### GraphQL operations

All operations live in `frontend/src/graphql/operations.ts`. Add new `gql` tagged template constants there — no other files should define inline `gql` queries for data fetching (local component-level gql for Vulgate viewer is an exception, kept local for now).

---

## Data

```
data/
├── hebrew/
│   ├── lesson01-05.json   # Vocabulary cards (Lambdin-based)
│   ├── TBESH.txt          # Extended Strong's Hebrew lexicon
│   └── tahot_raw/         # TAHOT corpus TSV files
├── latin/lesson01-03.json
├── ecclesiastical_latin/lesson01-03.json
├── greek/lesson01-03.json
├── nt_greek/lesson01-03.json
├── sanskrit/lesson01-03.json
├── vulgate/               # Vulgate Latin corpus + DRC commentary
└── references/
    ├── gesenius_hebrew_grammar.txt   # GKC public domain text
    └── gesenius_index.jsonl          # Semantic search index (build with scripts/)
```

### Lesson file format

```json
{
  "id": "hebrew-lesson-01",
  "name": "Lesson 1",
  "language": "hbo",
  "cards": [
    {
      "category": "nouns",
      "hebrew": "נַעַר",
      "transliteration": "náʿar",
      "definition": "young man, boy"
    }
  ]
}
```

Exercise generators load lesson files via `load_lessons_up_to(max_lesson)` and filter by lesson number. When adding vocabulary, add to the appropriate `lesson0N.json` — exercises automatically pick it up.

### Frontend static data

Files served from `frontend/public/data/` are loaded directly by frontend pages (Rashi JSON, Lanman reader, etc.) — they are not served through GraphQL.

---

## Languages supported

| Code | Language | Lessons | Exercise types |
|---|---|---|---|
| `hbo` | Biblical Hebrew | 5 | prepositions, articles, sentences, translation, verbal, comparative, relative clauses |
| `lat` | Classical Latin | 3 | declension, conjugation |
| `ecl` | Ecclesiastical Latin | 3 | declension, conjugation |
| `grc` | Ancient Greek | 3 | declension, conjugation |
| `gnt` | NT/Koine Greek | 3 | declension, conjugation |
| `san` | Sanskrit | 3 | declension |

Adding a new language:
1. Create `data/<lang>/lesson01.json` with vocabulary.
2. Create `backend/reshith/languages/<lang>.py` subclassing `LanguageModule`.
3. Create `backend/reshith/exercises/<lang>/` with generator modules.
4. Register types in `api/types.py`, resolvers in `api/resolvers.py`, fields in `api/schema.py`.
5. Add frontend pages and routes following the patterns of Latin or Greek.

---

## Adding a new data source

Whenever you pull in a new external dataset, corpus, lexicon, translation, font, or API, you **must** add an entry to `docs/sources.md` before the task is complete. This keeps the license record accurate and avoids legal surprises later.

For each new source, record:

1. **Name** — the dataset's official name and edition (e.g. "STEPBible TAHOT").
2. **Description** — one or two sentences on what it is and how it is used in the project.
3. **Source** — the canonical URL (GitHub repo, API root, project homepage, Gutenberg link, etc.).
4. **License** — the exact SPDX identifier or license name (e.g. `CC BY 4.0`, `Public domain`, `MIT`). If unknown, research it before proceeding; do not leave it blank.
5. **Attribution required** — Yes/No, and the required credit string if Yes.
6. **Repo path** — where the data (or its processed output) lives in this repo.
7. **Processing script** — the script that fetches or transforms it, if any.

Place the entry under the appropriate section in `docs/sources.md` (Corpora, Lexica, Translations, Commentaries, APIs and NLP Services, Pedagogical Texts, or Fonts). If no existing section fits, add one.

Also update the **License Compatibility Notes** table if the new license is not already represented there.

---

## Common pitfalls

- **`uv run` not plain `python`** — The backend imports `jose`, `strawberry`, etc. which are only in the uv-managed venv. Always use `uv run python` or `uv run pytest` in the `backend/` directory.
- **Strawberry `snake_case` → `camelCase`** — Python resolver args use `snake_case`; the GraphQL schema and frontend operations use `camelCase`. They are the same field — don't alias or rename.
- **Edit tool after file changes** — If a file has been modified since it was last read, the Edit tool will fail. Re-read the file first.
- **RTL/LTR in React** — Hebrew text containers use `dir="rtl"`. Detail panels that mix RTL and LTR content need an explicit `dir="ltr"` to override the inherited direction.
- **`text-start` in RTL context** — `text-start` is direction-aware: it means right-aligned in `dir="rtl"` containers. Use it (not `text-right`) for Hebrew text alignment.
- **TTS cache** — `backend/tts_cache/` is gitignored. Cached `.wav` files accumulate there; safe to delete if disk space is a concern.
- **Semantic search index** — `data/references/gesenius_index.jsonl` must be built explicitly with `scripts/build_gesenius_index.py` before GKC context is available to the LLM. The LLM falls back to keyword search without it.
