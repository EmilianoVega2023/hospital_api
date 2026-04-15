from fastapi import APIRouter
from app.api.v1.endpoints import auth, turnos, medicos

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(turnos.router)
api_router.include_router(medicos.router)
