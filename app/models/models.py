import enum
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey,
    Integer, String, Text, Time, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.orm import relationship, Mapped
from app.db.session import Base


def now_utc():
    return datetime.now(timezone.utc)


class EstadoTurno(str, enum.Enum):
    reservado  = "reservado"
    confirmado = "confirmado"
    cancelado  = "cancelado"
    completado = "completado"
    ausente    = "ausente"


class TipoNotificacion(str, enum.Enum):
    email = "email"
    sms   = "sms"
    push  = "push"


class EstadoNotificacion(str, enum.Enum):
    pendiente = "pendiente"
    enviado   = "enviado"
    fallido   = "fallido"


class EstadoEspera(str, enum.Enum):
    activo     = "activo"
    notificado = "notificado"
    expirado   = "expirado"
    asignado   = "asignado"


class DiaSemana(str, enum.Enum):
    lunes     = "lunes"
    martes    = "martes"
    miercoles = "miercoles"
    jueves    = "jueves"
    viernes   = "viernes"
    sabado    = "sabado"
    domingo   = "domingo"


class RolUsuario(str, enum.Enum):
    paciente   = "paciente"
    secretario = "secretario"
    admin      = "admin"


class ObraSocial(Base):
    __tablename__ = "obras_sociales"
    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre         = Column(String(120), nullable=False)
    codigo         = Column(String(20),  nullable=False, unique=True)
    descripcion    = Column(Text)
    activo         = Column(Boolean, nullable=False, default=True)
    creado_en      = Column(DateTime(timezone=True), default=now_utc)
    actualizado_en = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)
    pacientes: Mapped[List["Paciente"]] = relationship(back_populates="obra_social")


class Especialidad(Base):
    __tablename__ = "especialidades"
    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre         = Column(String(100), nullable=False, unique=True)
    descripcion    = Column(Text)
    activo         = Column(Boolean, nullable=False, default=True)
    creado_en      = Column(DateTime(timezone=True), default=now_utc)
    actualizado_en = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)
    medicos:      Mapped[List["Medico"]]      = relationship(back_populates="especialidad")
    lista_espera: Mapped[List["ListaEspera"]] = relationship(back_populates="especialidad")


class Paciente(Base):
    __tablename__ = "pacientes"
    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre           = Column(String(80),  nullable=False)
    apellido         = Column(String(80),  nullable=False)
    dni              = Column(String(20),  nullable=False, unique=True)
    fecha_nacimiento = Column(DateTime,    nullable=False)
    email            = Column(String(150), nullable=False, unique=True)
    telefono         = Column(String(30))
    direccion        = Column(Text)
    obra_social_id   = Column(UUID(as_uuid=True), ForeignKey("obras_sociales.id", ondelete="SET NULL"), nullable=True)
    contrasena_hash  = Column(Text, nullable=False)
    activo           = Column(Boolean, nullable=False, default=True)
    email_verificado = Column(Boolean, nullable=False, default=False)
    creado_en        = Column(DateTime(timezone=True), default=now_utc)
    actualizado_en   = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)
    obra_social:  Mapped[Optional["ObraSocial"]] = relationship(back_populates="pacientes")
    turnos:       Mapped[List["Turno"]]          = relationship(back_populates="paciente")
    lista_espera: Mapped[List["ListaEspera"]]    = relationship(back_populates="paciente")


class UsuarioAdmin(Base):
    __tablename__ = "usuarios_admin"
    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre          = Column(String(80),  nullable=False)
    apellido        = Column(String(80),  nullable=False)
    email           = Column(String(150), nullable=False, unique=True)
    contrasena_hash = Column(Text, nullable=False)
    rol             = Column(Enum(RolUsuario), nullable=False, default=RolUsuario.secretario)
    activo          = Column(Boolean, nullable=False, default=True)
    creado_en       = Column(DateTime(timezone=True), default=now_utc)
    actualizado_en  = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


class Medico(Base):
    __tablename__ = "medicos"
    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre          = Column(String(80),  nullable=False)
    apellido        = Column(String(80),  nullable=False)
    matricula       = Column(String(30),  nullable=False, unique=True)
    especialidad_id = Column(UUID(as_uuid=True), ForeignKey("especialidades.id", ondelete="RESTRICT"), nullable=False)
    email           = Column(String(150), nullable=False, unique=True)
    telefono        = Column(String(30))
    activo          = Column(Boolean, nullable=False, default=True)
    creado_en       = Column(DateTime(timezone=True), default=now_utc)
    actualizado_en  = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)
    especialidad:   Mapped["Especialidad"]               = relationship(back_populates="medicos")
    turnos:         Mapped[List["Turno"]]                = relationship(back_populates="medico")
    disponibilidad: Mapped[List["DisponibilidadHoraria"]] = relationship(back_populates="medico")
    lista_espera:   Mapped[List["ListaEspera"]]          = relationship(back_populates="medico")


class Consultorio(Base):
    __tablename__ = "consultorios"
    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    numero      = Column(String(10), nullable=False)
    piso        = Column(String(10))
    descripcion = Column(String(200))
    activo      = Column(Boolean, nullable=False, default=True)
    creado_en   = Column(DateTime(timezone=True), default=now_utc)
    turnos: Mapped[List["Turno"]] = relationship(back_populates="consultorio")


class DisponibilidadHoraria(Base):
    __tablename__ = "disponibilidad_horaria"
    id                 = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    medico_id          = Column(UUID(as_uuid=True), ForeignKey("medicos.id", ondelete="CASCADE"), nullable=False)
    dia                = Column(Enum(DiaSemana), nullable=False)
    hora_inicio        = Column(Time, nullable=False)
    hora_fin           = Column(Time, nullable=False)
    duracion_turno_min = Column(Integer, nullable=False, default=30)
    activo             = Column(Boolean, nullable=False, default=True)
    creado_en          = Column(DateTime(timezone=True), default=now_utc)
    actualizado_en     = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)
    __table_args__ = (CheckConstraint("hora_fin > hora_inicio", name="hora_valida"),)
    medico: Mapped["Medico"] = relationship(back_populates="disponibilidad")


class Turno(Base):
    __tablename__ = "turnos"
    id                 = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paciente_id        = Column(UUID(as_uuid=True), ForeignKey("pacientes.id",    ondelete="RESTRICT"), nullable=False)
    medico_id          = Column(UUID(as_uuid=True), ForeignKey("medicos.id",      ondelete="RESTRICT"), nullable=False)
    consultorio_id     = Column(UUID(as_uuid=True), ForeignKey("consultorios.id", ondelete="SET NULL"), nullable=True)
    fecha_hora         = Column(DateTime(timezone=True), nullable=False)
    estado             = Column(Enum(EstadoTurno), nullable=False, default=EstadoTurno.reservado)
    motivo_consulta    = Column(Text)
    notas_medico       = Column(Text)
    cancelado_en       = Column(DateTime(timezone=True), nullable=True)
    motivo_cancelacion = Column(Text)
    creado_en          = Column(DateTime(timezone=True), default=now_utc)
    actualizado_en     = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)
    __table_args__ = (
        UniqueConstraint("medico_id",   "fecha_hora", name="uq_medico_horario"),
        UniqueConstraint("paciente_id", "fecha_hora", name="uq_paciente_horario"),
    )
    paciente:       Mapped["Paciente"]               = relationship(back_populates="turnos")
    medico:         Mapped["Medico"]                 = relationship(back_populates="turnos")
    consultorio:    Mapped[Optional["Consultorio"]]  = relationship(back_populates="turnos")
    notificaciones: Mapped[List["Notificacion"]]     = relationship(back_populates="turno")


class ListaEspera(Base):
    __tablename__ = "lista_espera"
    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paciente_id     = Column(UUID(as_uuid=True), ForeignKey("pacientes.id",      ondelete="CASCADE"),  nullable=False)
    medico_id       = Column(UUID(as_uuid=True), ForeignKey("medicos.id",        ondelete="SET NULL"), nullable=True)
    especialidad_id = Column(UUID(as_uuid=True), ForeignKey("especialidades.id", ondelete="RESTRICT"), nullable=False)
    fecha_solicitud = Column(DateTime(timezone=True), default=now_utc)
    estado          = Column(Enum(EstadoEspera), nullable=False, default=EstadoEspera.activo)
    notificado_en   = Column(DateTime(timezone=True), nullable=True)
    creado_en       = Column(DateTime(timezone=True), default=now_utc)
    paciente:     Mapped["Paciente"]          = relationship(back_populates="lista_espera")
    medico:       Mapped[Optional["Medico"]]  = relationship(back_populates="lista_espera")
    especialidad: Mapped["Especialidad"]      = relationship(back_populates="lista_espera")


class Notificacion(Base):
    __tablename__ = "notificaciones"
    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    turno_id   = Column(UUID(as_uuid=True), ForeignKey("turnos.id", ondelete="CASCADE"), nullable=False)
    tipo       = Column(Enum(TipoNotificacion),   nullable=False)
    estado     = Column(Enum(EstadoNotificacion), nullable=False, default=EstadoNotificacion.pendiente)
    asunto     = Column(String(200))
    cuerpo     = Column(Text)
    enviado_en = Column(DateTime(timezone=True), nullable=True)
    error_msg  = Column(Text)
    creado_en  = Column(DateTime(timezone=True), default=now_utc)
    turno: Mapped["Turno"] = relationship(back_populates="notificaciones")


class Auditoria(Base):
    __tablename__ = "auditoria"
    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id       = Column(UUID(as_uuid=True), nullable=True)
    tipo_usuario     = Column(String(20))
    accion           = Column(String(100), nullable=False)
    tabla_afectada   = Column(String(60))
    registro_id      = Column(UUID(as_uuid=True), nullable=True)
    datos_anteriores = Column(JSONB)
    datos_nuevos     = Column(JSONB)
    ip               = Column(INET)
    user_agent       = Column(Text)
    creado_en        = Column(DateTime(timezone=True), default=now_utc)
