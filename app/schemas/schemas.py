from datetime import datetime, date, time
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, field_validator, model_validator
import re
from app.models.models import EstadoTurno, DiaSemana, RolUsuario


class UUIDMixin(BaseModel):
    id: UUID
    class Config:
        from_attributes = True


class ObraSocialBase(BaseModel):
    nombre: str
    codigo: str
    descripcion: Optional[str] = None

class ObraSocialCreate(ObraSocialBase):
    pass

class ObraSocialResponse(UUIDMixin, ObraSocialBase):
    activo: bool


class EspecialidadBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class EspecialidadCreate(EspecialidadBase):
    pass

class EspecialidadResponse(UUIDMixin, EspecialidadBase):
    activo: bool


class PacienteBase(BaseModel):
    nombre: str
    apellido: str
    dni: str
    fecha_nacimiento: date
    email: EmailStr
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    obra_social_id: Optional[UUID] = None

class PacienteCreate(PacienteBase):
    contrasena: str

    @field_validator("contrasena")
    @classmethod
    def validar_contrasena(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Debe contener al menos una mayúscula")
        if not re.search(r"\d", v):
            raise ValueError("Debe contener al menos un número")
        return v

class PacienteResponse(UUIDMixin, PacienteBase):
    activo: bool
    email_verificado: bool
    creado_en: datetime


class UsuarioAdminCreate(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    contrasena: str
    rol: RolUsuario = RolUsuario.secretario

class UsuarioAdminResponse(UUIDMixin):
    nombre: str
    apellido: str
    email: EmailStr
    rol: RolUsuario
    activo: bool


class MedicoBase(BaseModel):
    nombre: str
    apellido: str
    matricula: str
    especialidad_id: UUID
    email: EmailStr
    telefono: Optional[str] = None

class MedicoCreate(MedicoBase):
    pass

class MedicoResponse(UUIDMixin, MedicoBase):
    activo: bool
    especialidad: Optional[EspecialidadResponse] = None


class DisponibilidadBase(BaseModel):
    medico_id: UUID
    dia: DiaSemana
    hora_inicio: time
    hora_fin: time
    duracion_turno_min: int = 30

    @model_validator(mode="after")
    def validar_horas(self) -> "DisponibilidadBase":
        if self.hora_fin <= self.hora_inicio:
            raise ValueError("hora_fin debe ser posterior a hora_inicio")
        return self

class DisponibilidadCreate(DisponibilidadBase):
    pass

class DisponibilidadResponse(UUIDMixin, DisponibilidadBase):
    activo: bool


class TurnoBase(BaseModel):
    medico_id: UUID
    consultorio_id: Optional[UUID] = None
    fecha_hora: datetime
    motivo_consulta: Optional[str] = None

class TurnoCreate(TurnoBase):
    paciente_id: Optional[UUID] = None  # secretario puede crear para otro paciente

class TurnoCancelar(BaseModel):
    motivo_cancelacion: Optional[str] = None

class TurnoResponse(UUIDMixin, TurnoBase):
    paciente_id: UUID
    estado: EstadoTurno
    notas_medico: Optional[str] = None
    cancelado_en: Optional[datetime] = None
    motivo_cancelacion: Optional[str] = None
    creado_en: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    contrasena: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    rol: str

class RefreshRequest(BaseModel):
    refresh_token: str


class ListaEsperaCreate(BaseModel):
    especialidad_id: UUID
    medico_id: Optional[UUID] = None

class ListaEsperaResponse(UUIDMixin, ListaEsperaCreate):
    paciente_id: UUID
    fecha_solicitud: datetime
    estado: str


class MensajeResponse(BaseModel):
    mensaje: str
    ok: bool = True
