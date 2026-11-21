"""
QUORUM FastAPI Main Application.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_compare import router as compare_router
from app.api.routes_markets import router as markets_router
from app.api.routes_sessions import router as sessions_router
from app.config.settings import FRONTEND_ORIGIN
from app.db.connection import init_tables

# Automatically initialize tables on start
init_tables()

app = FastAPI(
    title="QUORUM Decision API",
    description="Cross-market multi-agent decision support with supervised debate and risk governance.",
    version="1.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(markets_router)
app.include_router(sessions_router)
app.include_router(compare_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "app": "QUORUM", "version": "1.0.0"}
