import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from app.routes import (
    chat,
    summary,
)

app = FastAPI(title="Creator Signal Prototype API")

_frontend_origin = os.environ.get("FRONTEND_ORIGIN")
_allowed_origins = [_frontend_origin] if _frontend_origin else []

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    # Next's dev server picks whatever port is free (3000, 3001, ...), so allow
    # any localhost port in dev rather than hardcoding one.
    allow_origin_regex=r"http://localhost:\d+",
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(summary.router)
app.include_router(chat.router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
