from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import decode_token
from app.db.session import get_db
from app.models.models import Paciente, UsuarioAdmin

bearer_scheme = HTTPBearer()


async def get_current_paciente(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Paciente:
    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access" or payload.get("role") != "paciente":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    result = await db.execute(
        select(Paciente).where(Paciente.id == UUID(payload["sub"]), Paciente.activo == True)
    )
    paciente = result.scalar_one_or_none()
    if not paciente:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Paciente no encontrado")
    return paciente


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> UsuarioAdmin:
    payload = decode_token(credentials.credentials)
    print("PAYLOAD:", payload)  # 👈 ACÁ
    if payload.get("type") != "access" or payload.get("role") not in ["secretario", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")
    result = await db.execute(
        select(UsuarioAdmin).where(UsuarioAdmin.id == UUID(payload["sub"]), UsuarioAdmin.activo == True)
    )
    admin = result.scalar_one_or_none()
    print("USER DB:", admin)  # 👈 ACÁ
    if not admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")
    return admin


async def get_current_superadmin(
    admin: UsuarioAdmin = Depends(get_current_admin),
) -> UsuarioAdmin:
    if admin.rol != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Se requiere rol admin")
    return admin
