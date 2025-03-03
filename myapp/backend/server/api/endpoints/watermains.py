from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..schemas import watermains as schemas
from ..db.models import WaterMain
from ..db.session import get_db

router = APIRouter()

@router.get("/", response_model=list[schemas.WaterMainResponse])
async def get_water_mains(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WaterMain))
    return result.scalars().all()

@router.get("/{object_id}", response_model=schemas.WaterMainResponse)
async def get_water_main(object_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WaterMain).where(WaterMain.object_id == object_id))
    water_main = result.scalars().first()
    if not water_main:
        raise HTTPException(status_code=404, detail="Water main not found")
    return water_main

@router.post("/", response_model=schemas.WaterMainResponse)
async def create_water_main(data: schemas.WaterMainCreate, db: AsyncSession = Depends(get_db)):
    water_main = WaterMain(**data.dict())
    db.add(water_main)
    await db.commit()
    await db.refresh(water_main)
    return water_main
