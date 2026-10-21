"""Excepciones de dominio + registro de handlers FastAPI.

Regla: los routers no devuelven errores ad-hoc; lanzan estas excepciones y el
handler global produce el envelope {ok:false, error:{code,message}} sin
tracebacks en la terminal del servidor.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("sendero.errors")


class AppError(Exception):
    """Base de todos los errores de dominio."""

    code = "app_error"
    status = 400

    def __init__(
        self, message: str, *, code: str | None = None, status: int | None = None
    ):
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status is not None:
            self.status = status


class NotFoundError(AppError):
    code = "not_found"
    status = 404


class ValidationError(AppError):
    code = "validation_error"
    status = 400


class ConflictError(AppError):
    code = "conflict"
    status = 409


def register_exception_handlers(aplicacion) -> None:
    """Registra los handlers globales en la app FastAPI.

    Args:
        aplicacion: instancia de `FastAPI` sobre la que montar los
            handlers. (Starlette los invoca con `(request, excepcion)`
            por posición, así que el nombre de los parámetros es libre.)
    """
    from fastapi import Request
    from fastapi.responses import JSONResponse

    from app.schemas.envelope import fallo

    @aplicacion.exception_handler(AppError)
    async def _app_error_handler(
        request: Request, excepcion: AppError
    ) -> JSONResponse:
        logger.warning(
            "%s %s → %s (%s)",
            request.method,
            request.url.path,
            excepcion.code,
            excepcion.message,
        )
        return JSONResponse(
            status_code=excepcion.status,
            content=fallo(excepcion.code, excepcion.message),
        )

    @aplicacion.exception_handler(Exception)
    async def _unhandled_handler(
        request: Request, excepcion: Exception
    ) -> JSONResponse:
        """500 con envelope. No vuelca traceback (requisito Fase 0)."""
        del excepcion  # firmado por Starlette; el detalle se omite a propósito
        logger.exception(
            "Error inesperado en %s %s",
            request.method,
            request.url.path,
        )
        return JSONResponse(
            status_code=500,
            content=fallo("internal_error", "Error interno del servidor"),
        )
