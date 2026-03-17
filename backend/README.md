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

## Speech Synthesis

The backend supports three TTS engines:

| Language | Engine | Notes |
|---|---|---|
| Hebrew (`he-IL`) | Google Cloud TTS | Falls back to browser Web Speech API if unavailable |
| Latin (`la`) | Facebook MMS-TTS (`facebook/mms-tts-lat`) | ~100 MB; downloads automatically on first use |
| Sanskrit (`sa`) | AI4Bharat Indic Parler-TTS (`ai4bharat/indic-parler-tts`) | ~1 GB; gated model — requires HuggingFace token |

### Google Cloud TTS (Hebrew)

Set `GOOGLE_CLOUD_API_KEY` in `.env`:

```
GOOGLE_CLOUD_API_KEY=your_key_here
GOOGLE_TTS_VOICE=he-IL-Wavenet-A
```

### Sanskrit TTS (Indic Parler-TTS)

`ai4bharat/indic-parler-tts` is a gated model. To enable it:

1. Accept the license at https://huggingface.co/ai4bharat/indic-parler-tts
2. Generate an access token at https://huggingface.co/settings/tokens
3. Add to `.env`:

```
HF_TOKEN=hf_...
```

Both MMS-TTS (Latin) and Parler-TTS (Sanskrit) models are downloaded automatically on first use and cached by HuggingFace in `~/.cache/huggingface/hub/`. Synthesized audio is also cached in `backend/tts_cache/` so repeated requests are served from disk.
