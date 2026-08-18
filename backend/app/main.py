import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import chat, summary

app = FastAPI(title="Creator Signal Prototype API")

_frontend_origin = os.environ.get("FRONTEND_ORIGIN")
_allowed_origins = ["http://localhost:3000"]
if _frontend_origin:
    _allowed_origins.append(_frontend_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(summary.router)
app.include_router(chat.router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
