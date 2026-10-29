# NOTA: Cria o servidor FastAPI. Ao iniciar: cria/atualiza o banco, insere os dados de demonstração se o banco estiver vazio
#       e mostra avisos de configuração em produção. Também: define quais endereços do front podem chamar a API (CORS),
#       limita tentativas por IP nas rotas de login, trata erros de banco, responde /health
#       e entrega o site já compilado (frontend/dist) quando ele existe.

import logging
import os
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app.api.v1.api import api_router
from app.core import rate_limit
from app.core.audit import client_ip
from app.core.config import CORS_ORIGINS
from app.db.seed import seed_if_empty
from app.db.session import init_db

app = FastAPI(title="TechConnect API v2.0 - Clean Arch", version="2.0.0")

@app.on_event("startup")
async def on_startup():
    await init_db()
    await seed_if_empty()
    if os.getenv("APP_ENV", "development").lower() == "production":
        from app.core.readiness import production_warnings
        for warning in production_warnings():
            logging.getLogger("techconnect").warning("Configuração de produção: %s", warning)
    if os.getenv("DEMO_REFRESH_DATES") == "1":
        from app.db.demo_dates import refresh_demo_dates
        from app.db.session import async_session_maker
        async with async_session_maker() as db:
            await refresh_demo_dates(db)

app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"], expose_headers=["Content-Disposition", "X-Subscription", "Retry-After"])

@app.exception_handler(IntegrityError)
async def integrity_error(request, exc: IntegrityError):
    # Endpoints take free-form dicts; a missing required field or duplicate must be a 400, not a 500.
    logging.getLogger("techconnect").warning("IntegrityError em %s: %s", request.url.path, exc.orig)
    return JSONResponse(status_code=400, content={"detail": "Dados inválidos ou incompletos: verifique os campos obrigatórios"})


@app.middleware("http")
async def remember_client_ip(request, call_next):
    ip = rate_limit.resolve_client_ip(request)
    client_ip.set(ip)
    if rate_limit.is_limited(request.url.path, request.method):
        wait = rate_limit.check(ip)
        if wait:
            return JSONResponse(status_code=429, headers={"Retry-After": str(wait)},
                                content={"detail": f"Muitas tentativas. Aguarde {wait} segundos e tente de novo."})
    return await call_next(request)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health(): return {"status":"ok","version":"2.0.0","database":"ok","timestamp":datetime.now().isoformat()}

@app.get("/api/v1/health")
async def health2(): return {"status":"ok","version":"2.0.0","timestamp":datetime.now().isoformat()}

# Serve the built frontend (single-page app) when it exists next to the backend.
_DIST = next((d for d in ("frontend/dist", "../frontend/dist") if os.path.exists(d)), None)

if _DIST:
    app.mount("/assets", StaticFiles(directory=f"{_DIST}/assets"), name="assets")

    @app.exception_handler(404)
    async def not_found(request: Request, exc: StarletteHTTPException):
        if request.url.path.startswith(("/api/", "/health")):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        return FileResponse(f"{_DIST}/index.html")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith(("api/", "docs", "redoc")) or full_path in ("health", "openapi.json"):
            raise StarletteHTTPException(status_code=404, detail="Not Found")
        path = f"{_DIST}/{full_path}"
        if os.path.isfile(path):
            return FileResponse(path)
        return FileResponse(f"{_DIST}/index.html")
