from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import json
from typing import List

from ..schemas import watermains as schemas
from ..schemas.watermains import ObjectIDListRequest as GeometryRequest
from ..db.models import WaterMain
from ..db.session import get_db
from ..db.redis_connection import redis_client  # Import Redis client

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

# ✅ New Redis-based endpoint
@router.get("/cached/", response_model=list[schemas.WaterMainResponse])
async def get_cached_water_mains():
    """
    Fetch all watermains data from Redis cache.
    """
    cached_data = redis_client.hgetall("watermains:all")
    if not cached_data:
        raise HTTPException(status_code=404, detail="No cached watermains data found.")

    # Convert Redis data to list of dictionaries
    return [json.loads(wm) for wm in cached_data.values()]

# ✅ Get all cached geometries with object_ids
@router.get("/cached/geometry", response_model=List[dict])
async def get_cached_geometries():
    """
    Fetch all geometries and object_ids from Redis cache.
    """
    cached_data = redis_client.hgetall("watermains:all")
    if not cached_data:
        raise HTTPException(status_code=404, detail="No cached watermains data found.")

    # Extract only object_id and geometry
    geometries = [
        {
            "object_id": int(obj_id),
            "geometry": json.loads(data).get("geometry")
        }
        for obj_id, data in cached_data.items()
        if json.loads(data).get("geometry")
    ]

    return geometries

# ✅ Get geometries for a list of object_ids using path parameters
@router.get("/cached/geometry/{object_ids}", response_model=list[dict])
async def get_cached_geometry_by_path(object_ids: str):
    """
    Fetch geometries for a list of object_ids from Redis cache via path parameters.

    Example request: `/cached/geometry/259489,259490`
    """
    ids_list = object_ids.split(",")  # Convert comma-separated string to list of IDs
    cached_geometries = []

    for obj_id in ids_list:
        cached_data = redis_client.hget("watermains:all", obj_id)
        if cached_data:
            watermain = json.loads(cached_data)
            if "geometry" in watermain:
                cached_geometries.append({"object_id": int(obj_id), "geometry": watermain["geometry"]})

    if not cached_geometries:
        raise HTTPException(status_code=404, detail="No matching geometries found in cache.")

    return cached_geometries

# ✅ Moved this BELOW `/cached/geometry` to avoid conflicts
@router.get("/cached/{object_id}", response_model=schemas.WaterMainResponse)
async def get_cached_water_main(object_id: int):
    """
    Fetch a single watermain from Redis cache by object_id.
    """
    cached_data = redis_client.hget("watermains:all", str(object_id))  # ✅ Use hget instead of get
    if not cached_data:
        raise HTTPException(status_code=404, detail="No cached watermains data found.")

    return json.loads(cached_data)

@router.post("/cached/geometry", response_model=List[dict])
async def get_geometries_by_ids(request: GeometryRequest):
    """
    Fetch geometries for multiple watermains from Redis cache by object_ids.
    """
    geometries = []
    for object_id in request.object_ids:
        cached_data = redis_client.hget("watermains:all", str(object_id))
        if cached_data:
            watermain = json.loads(cached_data)
            if "geometry" in watermain:
                geometries.append({
                    "object_id": object_id,
                    "geometry": watermain["geometry"]
                })
    
    if not geometries:
        raise HTTPException(status_code=404, detail="No geometries found for the provided IDs.")
    
    return geometries
