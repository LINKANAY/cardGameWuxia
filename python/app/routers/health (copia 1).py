"""GET /api/health"""

from __future__ import annotations

import time

from fastapi import APIRouter

from app.config import get_settings
from app.schemas.envelope import exito

_STARTED_AT = time.time()
router = APIRouter(tags=["health"])


@router.get("/api/health")
def health():
    return exito(
        {
            "version": get_settings().version,
            "uptime": round(time.time() - _STARTED_AT, 3),
        }
    )
