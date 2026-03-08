# api/main.py
"""
FastAPI application entry point.

Run from backend/:
    uvicorn api.main:app --reload --port 8000

Docs at: http://localhost:8000/docs
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import dining, explore, profile, meals
from api.services.index_service import build_index
from src.db.user_db import delete_stale_usda_foods

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Startup: load all non-dining foods from Postgres and build the in-memory index.
    Dining hall foods are scraped on-demand per request (menus change daily).
    """
    logger.info("Starting up — loading foods from database...")
    try:
        # Purge non-dining foods older than 30 days
        deleted = delete_stale_usda_foods(older_than_days=30)
        if deleted:
            logger.info("Purged %d stale USDA foods (>30 days old).", deleted)

        from src.db.postgres import fetch_foods
        foods = fetch_foods(limit=5000)
        non_dining = [f for f in foods if not f.source.startswith("uci_dining_")]
        await build_index(non_dining)
        logger.info("Loaded %d non-dining foods into index.", len(non_dining))
    except Exception as exc:
        logger.error("Could not load foods from DB: %s — explore search will be empty.", exc)
        await build_index([])

    yield

    logger.info("Shutting down.")


app = FastAPI(
    title="Personalized Dining Recommendation API",
    description="UCI CS 125 — nutrition-aware food recommendations for UCI students.",
    version="0.1.0",
    lifespan=lifespan,
)

# Allow the Expo dev client and local simulator to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile.router)
app.include_router(meals.router)
app.include_router(dining.router)
app.include_router(explore.router)

# ---------------------------------------------------------------------------
# Note on auth: individual routers use Depends(require_auth) per-endpoint.
# Search and recommendation endpoints do NOT require auth so anonymous users
# can still get recommendations (using goals supplied in the request body).
# Profile and meal log endpoints DO require auth.
# ---------------------------------------------------------------------------


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
