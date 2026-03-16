"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

import reshith.languages.hebrew  # noqa: F401 - Register language modules
from reshith.api.schema import schema
from reshith.core.config import get_settings
from reshith.db.session import async_session_maker
from reshith.services import tts

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    tts.init_tts()
    yield


async def get_context():
    async with async_session_maker() as session:
        yield {"db": session}


graphql_app = GraphQLRouter(
    schema,
    context_getter=get_context,
)

app = FastAPI(
    title=settings.app_name,
    description="Language learning application for classical languages",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(graphql_app, prefix="/graphql")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
