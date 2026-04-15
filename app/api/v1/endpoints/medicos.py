from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.api.v1.deps import get_current_admin
from app.models.models import Medico, DisponibilidadHoraria, Especialidad
from app.schemas.schemas import MedicoResponse, MedicoCreate, DisponibilidadResponse, DisponibilidadCreate, EspecialidadResponse

router = APIRouter(prefix="/medicos", tags=["Médicos"])


@router.get("/", response_model=list[MedicoResponse])
async def listar_medicos(
    especialidad_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Medico).where(Medico.activo == True)
    if especialidad_id:
        query = query.where(Medico.especialidad_id == especialidad_id)
    result = await db.execute(query.order_by(Medico.apellido))
    return result.scalars().all()


@router.get("/especialidades", response_model=list[EspecialidadResponse])
async def listar_especialidades(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Especialidad).where(Especialidad.activo == True).order_by(Especialidad.nombre))
    return result.scalars().all()


@router.get("/{medico_id}", response_model=MedicoResponse)
async def obtener_medico(medico_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Medico).where(Medico.id == medico_id, Medico.activo == True))
    medico = result.scalar_one_or_none()
    if not medico:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    return medico


@router.get("/{medico_id}/disponibilidad", response_model=list[DisponibilidadResponse])
async def obtener_disponibilidad(medico_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DisponibilidadHoraria).where(
            DisponibilidadHoraria.medico_id == medico_id,
            DisponibilidadHoraria.activo == True,
        ).order_by(DisponibilidadHoraria.dia, DisponibilidadHoraria.hora_inicio)
    )
    return result.scalars().all()


# Solo secretario/admin puede crear médicos
@router.post("/", response_model=MedicoResponse, status_code=201)
async def crear_medico(
    datos: MedicoCreate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    medico = Medico(**datos.model_dump())
    db.add(medico)
    await db.flush()
    await db.refresh(medico)
    return medico


@router.post("/{medico_id}/disponibilidad", response_model=DisponibilidadResponse, status_code=201)
async def agregar_disponibilidad(
    medico_id: UUID,
    datos: DisponibilidadCreate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    disp = DisponibilidadHoraria(**datos.model_dump())
    db.add(disp)
    await db.flush()
    await db.refresh(disp)
    return disp
