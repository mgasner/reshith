# Reshith

A language learning application for acquiring reading/translation ability in classical languages with substantial written corpora.

> "The fear of the LORD is the beginning (reshith) of knowledge" - Proverbs 1:7

## Features

- **Flashcards** with spaced repetition (SM-2 algorithm)
- **LLM-backed translation drills** for contextual learning
- **Modular language support**: Biblical Hebrew, Latin, Greek, Sanskrit, Pali, Buddhist Hybrid Sanskrit, Aramaic, Midrashic Hebrew, and more
- **Corpus-based learning** optimized for reading classical texts

## Tech Stack

- **Backend**: Python, FastAPI, Strawberry GraphQL, SQLAlchemy, PostgreSQL
- **Frontend**: React, TypeScript, Vite, Apollo Client, TailwindCSS

## Quick Start

### 1. Install dependencies

```bash
make dev_install
```

This will install [uv](https://github.com/astral-sh/uv) and [nvm](https://github.com/nvm-sh/nvm) if not already present, then use them to install the correct Node version (defined in `.nvmrc`), frontend npm packages, and backend Python dependencies (including dev tools).

### 2. Run the dev servers

```bash
make dev
```

Starts both the frontend and backend with hot-reloading:

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **GraphQL Playground**: http://localhost:8000/graphql

Press `Ctrl+C` to stop both servers.

## Make Commands

| Command | Description |
|---|---|
| `make dev` | Start frontend + backend with hot-reloading |
| `make dev_install` | Install all frontend and backend dependencies |
| `make backend` | Start only the backend |
| `make frontend` | Start only the frontend |
| `make test` | Run all tests and linting |

## Manual Setup

If you prefer to run services separately:

### Backend

```bash
cd backend
uv sync --extra dev                        # Install dependencies (inc. dev tools)
uv run alembic upgrade head                # Run database migrations
uv run uvicorn reshith.main:app --reload   # Start the server
```

### Frontend

```bash
cd frontend
nvm use        # Activate correct Node version
npm install    # Install dependencies
npm run dev    # Start the dev server
```

### Running Tests

```bash
cd backend
uv run pytest tests/ -v      # Run tests
uv run ruff check reshith/   # Run linting
```

## Project Structure

```
reshith/
├── backend/           # Python FastAPI + Strawberry GraphQL
│   ├── reshith/       # Main application package
│   │   ├── api/       # GraphQL schema and resolvers
│   │   ├── core/      # Configuration, security, dependencies
│   │   ├── db/        # Database models and migrations
│   │   ├── exercises/ # Exercise generators (prepositions, articles, etc.)
│   │   └── services/  # Business logic (LLM, TTS, SRS)
│   └── tests/
├── frontend/          # React + TypeScript
│   ├── src/
│   │   ├── components/  # Reusable UI components
│   │   ├── pages/       # Page components
│   │   ├── graphql/     # GraphQL queries and mutations
│   │   └── hooks/       # Custom React hooks
│   └── public/
├── data/              # Language data
│   ├── hebrew/        # Hebrew vocabulary by lesson
│   └── references/    # Reference grammars (raw text + embedding index)
├── .nvmrc             # Pinned Node.js version (for nvm)
├── Makefile           # Dev workflow commands
└── run.sh             # Development helper script
```

## Reference Grammars

Reshith ships with the full text of *Gesenius' Hebrew Grammar* (Gesenius-Kautzsch-Cowley, 28th ed., 1910 — public domain) in `data/references/gesenius_hebrew_grammar.txt`. The translation-help feature automatically retrieves the most relevant sections and injects them into the LLM context so it can cite GKC section numbers in its explanations.

### Building the embedding index

The semantic search index is not committed to the repo (it requires an OpenAI API call to generate). Build it once after cloning:

```bash
uv run --directory backend python scripts/build_gesenius_index.py
```

This reads `OPENAI_API_KEY` from `backend/.env`, embeds the 164 GKC sections using `text-embedding-3-small`, and writes the index to `data/references/gesenius_index.jsonl`. The script is incremental — re-running it only embeds sections not already present in the index.

If the index has not been built, the reference service automatically falls back to keyword search, so the app remains fully functional without it.

## Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Required for LLM features (translation help, drill generation)
OPENAI_API_KEY=your-api-key

# Optional: Google Cloud TTS for pronunciation
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

## License

MIT
