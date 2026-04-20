import json
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.v1.router import api_router


def _agent_dbg(location: str, message: str, hypothesis_id: str, data: dict | None = None) -> None:
    # #region agent log
    try:
        with open("debug-f41686.log", "a", encoding="utf-8") as _f:
            _f.write(
                json.dumps(
                    {
                        "sessionId": "f41686",
                        "hypothesisId": hypothesis_id,
                        "location": location,
                        "message": message,
                        "data": data or {},
                        "timestamp": int(time.time() * 1000),
                    }
                )
                + "\n"
            )
    except Exception:
        pass
    # #endregion


@asynccontextmanager
async def lifespan(app: FastAPI):
    # #region agent log
    _agent_dbg("main.py:lifespan", "lifespan_enter", "C", {"app_title": getattr(app, "title", None)})
    # #endregion
    # ASCII-only: Windows consoles often use cp1252; emoji in print() raises UnicodeEncodeError at startup.
    print(f"[Hospital] {settings.APP_NAME} v{settings.APP_VERSION} iniciando...")
    # #region agent log
    _agent_dbg("main.py:lifespan", "after_startup_print", "C", {})
    # #endregion
    yield
    print("Cerrando conexiones...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Error interno del servidor"},
    )


app.include_router(api_router)


@app.get("/health", tags=["Sistema"])
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
