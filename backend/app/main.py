from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.infrastructure.models import Base
from app.infrastructure.seed import seed_if_empty
from app.presentation.deps import build_engine, get_settings
from app.presentation.http import register_handlers
from app.presentation.routers import auth, banking, security

logger = logging.getLogger("andesbank")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    engine = build_engine(settings)
    Base.metadata.create_all(engine)
    rounds = 4 if settings.app_env == "test" else 12
    with Session(engine) as session:
        seed_if_empty(session, rounds)
        session.commit()
    app.state.engine = engine
    logger.info("AndesBank API lista (%s)", settings.app_env)
    yield
    engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="AndesBank API",
        version="1.0.0",
        summary="API de laboratorio para la asignatura SI-988. No es una entidad financiera.",
        lifespan=lifespan,
    )
    origins = ["*"] if settings.app_env in {"local", "test", "development"} else []
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_handlers(app)

    @app.middleware("http")
    async def security_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    @app.get("/health", tags=["Operación"])
    def health():
        return {"status": "ok", "service": "andesbank-api"}

    @app.get("/ready", tags=["Operación"])
    def ready():
        with app.state.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ready"}

    app.include_router(auth.router)
    app.include_router(auth.me)
    app.include_router(banking.router)
    app.include_router(security.router)
    return app


app = create_app()
