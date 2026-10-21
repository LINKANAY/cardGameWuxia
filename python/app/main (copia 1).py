"""Factory de la app FastAPI.

Uso:
    python -m app.main
    # o: uvicorn app.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import setup_logging
from app.routers import (
    alchemy,
    combat,
    data,
    decks,
    equipo,
    gacha,
    game,
    health,
    horno,
    jardin,
    market,
    misiones,
    slots,
)
from app.state.session_store import SessionStore


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(aplicacion: FastAPI):
        # Starlette llama `lifespan(app)` por posición: el nombre del
        # parámetro es libre.
        aplicacion.state.store = SessionStore()
        yield
        # shutdown: persistir todo lo que quede en memoria
        guardadas = aplicacion.state.store.save_all()
        if guardadas:
            import logging

            logging.getLogger("sendero.main").info(
                "Guardadas %d sesiones en shutdown", guardadas
            )

    app = FastAPI(
        title="Sendero del Inmortal", version=settings.version, lifespan=lifespan
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(game.router)
    app.include_router(combat.router)
    app.include_router(alchemy.router)
    app.include_router(decks.router)
    app.include_router(market.router)
    app.include_router(gacha.router)
    app.include_router(slots.router)
    app.include_router(data.router)
    app.include_router(misiones.router)
    app.include_router(equipo.router)
    app.include_router(horno.router)
    app.include_router(jardin.router)
    return app


app = create_app()


def main() -> None:
    import uvicorn

    ajustes = get_settings()
    uvicorn.run(
        "app.main:app",
        host=ajustes.host,
        port=ajustes.port,
        reload=True,
    )


if __name__ == "__main__":
    main()
