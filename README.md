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

The easiest way to run Reshith is with the helper script:

```bash
./run.sh
```

This starts both the frontend and backend with hot-reloading. Once running:

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **GraphQL Playground**: http://localhost:8000/graphql

Press `Ctrl+C` to stop both servers.

### Other Commands

```bash
./run.sh backend   # Start only the backend
./run.sh frontend  # Start only the frontend
./run.sh test      # Run all tests and linting
./run.sh help      # Show all available commands
```

## Prerequisites

Before running, ensure you have:

- **[uv](https://github.com/astral-sh/uv)** - Python package manager
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

- **[Node.js](https://nodejs.org/)** (v18+) - For the frontend

## Manual Setup

If you prefer to run services separately:

### Backend

```bash
cd backend
uv sync                                    # Install dependencies
uv run alembic upgrade head                # Run database migrations
uv run uvicorn reshith.main:app --reload   # Start the server
```

### Frontend

```bash
cd frontend
npm install      # Install dependencies
npm run dev      # Start the dev server
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
│   └── hebrew/        # Hebrew vocabulary by lesson
└── run.sh             # Development helper script
```

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
