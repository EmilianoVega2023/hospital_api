from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db.session import get_db
from app.api.v1.deps import get_current_paciente, get_current_admin
from app.models.models import Turno, Medico, DisponibilidadHoraria, EstadoTurno
from app.schemas.schemas import TurnoCreate, TurnoResponse, TurnoCancelar

router = APIRouter(prefix="/turnos", tags=["Turnos"])


async def _verificar_disponibilidad(db, medico_id, fecha_hora):
    result = await db.execute(select(Medico).where(Medico.id == medico_id, Medico.activo == True))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    dias_map = {
        "monday": "lunes", "tuesday": "martes", "wednesday": "miercoles",
        "thursday": "jueves", "friday": "viernes", "saturday": "sabado", "sunday": "domingo",
    }
    dia = dias_map.get(fecha_hora.strftime("%A").lower())
    disp = await db.execute(
        select(DisponibilidadHoraria).where(and_(
            DisponibilidadHoraria.medico_id == medico_id,
            DisponibilidadHoraria.dia == dia,
            DisponibilidadHoraria.hora_inicio <= fecha_hora.time(),
            DisponibilidadHoraria.hora_fin > fecha_hora.time(),
            DisponibilidadHoraria.activo == True,
        ))
    )
    if not disp.scalar_one_or_none():
        raise HTTPException(status_code=422, detail="Horario fuera de la disponibilidad del médico")
    ocupado = await db.execute(
        select(Turno).where(and_(
            Turno.medico_id == medico_id,
            Turno.fecha_hora == fecha_hora,
            Turno.estado.in_([EstadoTurno.reservado, EstadoTurno.confirmado]),
        ))
    )
    if ocupado.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Ese horario ya está reservado")


# Paciente reserva su propio turno
@router.post("/", response_model=TurnoResponse, status_code=201)
async def reservar_turno(
    datos: TurnoCreate,
    db: AsyncSession = Depends(get_db),
    paciente=Depends(get_current_paciente),
):
    if datos.fecha_hora <= datetime.now(timezone.utc):
        raise HTTPException(status_code=422, detail="La fecha debe ser futura")
    await _verificar_disponibilidad(db, datos.medico_id, datos.fecha_hora)
    turno = Turno(
        paciente_id=paciente.id,
        medico_id=datos.medico_id,
        consultorio_id=datos.consultorio_id,
        fecha_hora=datos.fecha_hora,
        motivo_consulta=datos.motivo_consulta,
    )
    db.add(turno)
    await db.flush()
    await db.refresh(turno)
    return turno


# Secretario crea turno para cualquier paciente
@router.post("/admin", response_model=TurnoResponse, status_code=201)
async def reservar_turno_admin(
    datos: TurnoCreate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    if not datos.paciente_id:
        raise HTTPException(status_code=422, detail="Se requiere paciente_id")
    if datos.fecha_hora <= datetime.now(timezone.utc):
        raise HTTPException(status_code=422, detail="La fecha debe ser futura")
    await _verificar_disponibilidad(db, datos.medico_id, datos.fecha_hora)
    turno = Turno(
        paciente_id=datos.paciente_id,
        medico_id=datos.medico_id,
        consultorio_id=datos.consultorio_id,
        fecha_hora=datos.fecha_hora,
        motivo_consulta=datos.motivo_consulta,
    )
    db.add(turno)
    await db.flush()
    await db.refresh(turno)
    return turno


@router.get("/", response_model=list[TurnoResponse])
async def listar_mis_turnos(
    estado: EstadoTurno | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    paciente=Depends(get_current_paciente),
):
    query = select(Turno).where(Turno.paciente_id == paciente.id)
    if estado:
        query = query.where(Turno.estado == estado)
    result = await db.execute(query.order_by(Turno.fecha_hora.desc()))
    return result.scalars().all()


# Secretario ve todos los turnos del día
@router.get("/admin/hoy", response_model=list[TurnoResponse])
async def turnos_de_hoy(
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    from datetime import date
    hoy = date.today()
    result = await db.execute(
        select(Turno).where(
            Turno.fecha_hora >= datetime(hoy.year, hoy.month, hoy.day, tzinfo=timezone.utc)
        ).order_by(Turno.fecha_hora)
    )
    return result.scalars().all()


@router.get("/{turno_id}", response_model=TurnoResponse)
async def obtener_turno(
    turno_id: UUID,
    db: AsyncSession = Depends(get_db),
    paciente=Depends(get_current_paciente),
):
    result = await db.execute(select(Turno).where(Turno.id == turno_id))
    turno = result.scalar_one_or_none()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    if turno.paciente_id != paciente.id:
        raise HTTPException(status_code=403, detail="No tenés permiso para ver este turno")
    return turno


@router.patch("/{turno_id}/cancelar", response_model=TurnoResponse)
async def cancelar_turno(
    turno_id: UUID,
    datos: TurnoCancelar,
    db: AsyncSession = Depends(get_db),
    paciente=Depends(get_current_paciente),
):
    result = await db.execute(select(Turno).where(Turno.id == turno_id))
    turno = result.scalar_one_or_none()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    if turno.paciente_id != paciente.id:
        raise HTTPException(status_code=403, detail="No tenés permiso")
    if turno.estado not in [EstadoTurno.reservado, EstadoTurno.confirmado]:
        raise HTTPException(status_code=422, detail=f"No se puede cancelar un turno en estado '{turno.estado}'")
    turno.estado = EstadoTurno.cancelado
    turno.cancelado_en = datetime.now(timezone.utc)
    turno.motivo_cancelacion = datos.motivo_cancelacion
    await db.flush()
    await db.refresh(turno)
    return turno
