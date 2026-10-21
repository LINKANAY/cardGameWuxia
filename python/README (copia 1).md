# Backend — Sendero del Inmortal

Backend Python por capas del juego de cartas xianxia. Fuente de verdad del
comportamiento: el monolito `index.html` + `js/` en la raíz del repo.

## Estructura (Fase 0)

```
python/
├── app/
│   ├── main.py               # factory FastAPI, lifespan, CORS
│   ├── config.py             # Settings (env + defaults)
│   ├── core/
│   │   ├── errors.py         # excepciones de dominio + handler global
│   │   └── logging.py
│   ├── engine/               # lógica pura (sin FastAPI ni I/O)
│   │   └── state.py          # estado inicial de partida (placeholder Fase 1)
│   ├── schemas/
│   │   ├── envelope.py       # {ok, data|error} uniforme
│   │   └── game.py
│   ├── repositories/
│   │   └── save_repo.py      # saves/*.json, atómico + backup
│   ├── state/
│   │   └── session_store.py  # sesiones en memoria + auto-save
│   ├── services/
│   │   └── game_service.py
│   └── routers/
│       ├── health.py
│       └── game.py
├── tests/
│   ├── unit/
│   └── integration/
└── requirements.txt
```

## Arrancar

```bash
make backend          # Linux/macOS/WSL/Git Bash
make.bat backend      # Windows nativo
# → http://127.0.0.1:8765/api/health
```

## Tests

```bash
make test
```

## API (Fase 0)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/health` | Versión y uptime |
| POST | `/api/game/new` | Crear partida `{slot}` |
| GET | `/api/game/{slot}` | Snapshot (404 si no existe) |

Todas las respuestas usan el envelope `{ok, data}` / `{ok, error:{code,message}}`.
