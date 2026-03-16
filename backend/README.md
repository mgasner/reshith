# Reshith Backend

Python backend for the Reshith language learning application.

## Setup

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn reshith.main:app --reload
```

## Testing

```bash
uv run pytest
```

## GraphQL

Access the GraphQL playground at http://localhost:8000/graphql
