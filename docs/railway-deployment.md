# Railway Deployment Guide

This project deploys as two Railway services plus a managed PostgreSQL database.

## Architecture

```
[Frontend (nginx)]  --/graphql-->  [Backend (FastAPI)]  -->  [PostgreSQL]
     port 80                          port 8000
```

The frontend serves the React SPA and proxies `/graphql` requests to the backend via nginx.

## Setup

### 1. Create a Railway project

Go to [railway.com](https://railway.com) and create a new project from your GitHub repo.

### 2. Add a PostgreSQL database

In the Railway project dashboard, click **+ New** > **Database** > **PostgreSQL**.

### 3. Create the backend service

- Click **+ New** > **GitHub Repo** > select this repo
- Set **Root Directory** to `backend`
- Railway will auto-detect the `Dockerfile` and `railway.toml`

**Required environment variables:**

| Variable | Value | Notes |
|---|---|---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | Use Railway's reference variable; replace `postgresql://` prefix with `postgresql+asyncpg://` |
| `JWT_SECRET` | (generate a random string) | `openssl rand -hex 32` |
| `CORS_ORIGINS` | `["https://your-frontend.up.railway.app"]` | Your frontend's public URL |
| `OPENAI_API_KEY` | (your key) | Optional, for LLM features |
| `GOOGLE_CLOUD_API_KEY` | (your key) | Optional, for Google Cloud TTS |

**Note on DATABASE_URL:** Railway provides `DATABASE_URL` in the format `postgresql://...`. The backend uses SQLAlchemy's async driver and expects `postgresql+asyncpg://...`. Set the variable as:
```
postgresql+asyncpg://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/${PGDATABASE}
```
using Railway's individual Postgres reference variables.

### 4. Create the frontend service

- Click **+ New** > **GitHub Repo** > select this repo
- Set **Root Directory** to `frontend`

**Required environment variables:**

| Variable | Value | Notes |
|---|---|---|
| `BACKEND_URL` | `http://backend.railway.internal:8000` | Railway's private networking URL for the backend service |
| `PORT` | `80` | Railway assigns this automatically |

### 5. Generate a domain

For the **frontend** service, go to **Settings** > **Networking** > **Generate Domain** to get a public URL.

The backend does **not** need a public domain -- it is accessed internally by the frontend's nginx proxy.

## Local development

No changes needed. The Vite dev server proxies `/graphql` to `localhost:8000` as before:

```bash
# Terminal 1: backend
cd backend && uv run uvicorn reshith.main:app --reload

# Terminal 2: frontend
cd frontend && npm run dev
```

## ML/TTS features

The heavy ML dependencies (torch, transformers, parler-tts) are in the optional `[ml]` dependency group to keep the production image small. To enable local TTS:

```bash
cd backend && uv sync --extra ml
```

Google Cloud TTS works without these dependencies -- only the local model-based TTS requires them.
