from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.models import Paciente, UsuarioAdmin
from app.schemas.schemas import (
    PacienteCreate, PacienteResponse,
    LoginRequest, TokenResponse, RefreshRequest, MensajeResponse
)
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token
)

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/registro", response_model=PacienteResponse, status_code=201)
async def registrar_paciente(datos: PacienteCreate, db: AsyncSession = Depends(get_db)):
    existente = await db.execute(
        select(Paciente).where((Paciente.email == datos.email) | (Paciente.dni == datos.dni))
    )
    if existente.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un paciente con ese email o DNI")
    paciente = Paciente(
        nombre=datos.nombre, apellido=datos.apellido, dni=datos.dni,
        fecha_nacimiento=datos.fecha_nacimiento, email=datos.email,
        telefono=datos.telefono, direccion=datos.direccion,
        obra_social_id=datos.obra_social_id,
        contrasena_hash=hash_password(datos.contrasena),
    )
    db.add(paciente)
    await db.flush()
    await db.refresh(paciente)
    return paciente


@router.post("/login", response_model=TokenResponse)
async def login(datos: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Intentar como paciente primero
    result = await db.execute(
        select(Paciente).where(Paciente.email == datos.email, Paciente.activo == True)
    )
    paciente = result.scalar_one_or_none()
    if paciente and verify_password(datos.contrasena, paciente.contrasena_hash):
        return TokenResponse(
            access_token=create_access_token(str(paciente.id), role="paciente"),
            refresh_token=create_refresh_token(str(paciente.id)),
            rol="paciente",
        )

    # Intentar como admin/secretario
    result = await db.execute(
        select(UsuarioAdmin).where(UsuarioAdmin.email == datos.email, UsuarioAdmin.activo == True)
    )
    admin = result.scalar_one_or_none()
    if admin and verify_password(datos.contrasena, admin.contrasena_hash):
        return TokenResponse(
            access_token=create_access_token(str(admin.id), role=admin.rol.value),
            refresh_token=create_refresh_token(str(admin.id)),
            rol=admin.rol.value,
        )

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(datos: RefreshRequest):
    payload = decode_token(datos.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Se requiere un refresh token")
    subject = payload.get("sub")
    role = payload.get("role", "paciente")
    return TokenResponse(
        access_token=create_access_token(subject, role=role),
        refresh_token=create_refresh_token(subject),
        rol=role,
    )


@router.post("/logout", response_model=MensajeResponse)
async def logout():
    return MensajeResponse(mensaje="Sesión cerrada. Eliminá los tokens del cliente.")
