from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import asyncio
import json
import logging
from sqlalchemy.sql import func  # Import SQL functions for geometry handling

from api.endpoints import watermains
from api.db.session import engine
from api.db import models
from api.db.models import WaterMain
from api.db.redis_connection import redis_client

app = FastAPI(title="WebGIS-AI API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(watermains.router, prefix="/watermains", tags=["Water Mains"])

# Retry Configuration
MAX_RETRIES = 5
INITIAL_RETRY_DELAY = 5  # seconds
MAX_RETRY_DELAY = 60     # seconds

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/")
async def root():
    return {"message": "Welcome to WebGIS-AI API"}

# ✅ Unified Startup Function (DB and Redis Preloading)
@app.on_event("startup")
async def startup_event():
    """Initialize database and preload Redis at startup."""
    try:
        # Initialize database tables
        async with engine.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)
            logger.info("✅ Database tables created successfully")

        # Attempt to preload Redis
        success = await preload_redis()
        if success:
            logger.info("✅ Application startup completed successfully")
        else:
            logger.warning("⚠️ Application started but Redis preload was unsuccessful")

    except Exception as e:
        logger.error(f"❌ Error during startup: {str(e)}")

# ✅ Fixed Redis Preloading Function
async def preload_redis(retry_count: int = 0) -> bool:
    """
    Preload Redis with all watermains data on startup, including geometry as WKT.
    Returns True if successful, False otherwise.
    """
    try:
        async with AsyncSession(engine) as db:
            # ✅ Convert Geometry to WKT using ST_AsText()
            result = await db.execute(
                select(
                    WaterMain.id,
                    WaterMain.city,
                    WaterMain.dataset_type,
                    WaterMain.object_id,
                    WaterMain.watmain_id,
                    WaterMain.status,
                    WaterMain.pressure_zone,
                    WaterMain.material,
                    WaterMain.condition_score,
                    WaterMain.shape_length,
                    func.ST_AsText(WaterMain.geometry).label("geometry"),  # Convert geometry to WKT
                    WaterMain.created_at,
                    WaterMain.updated_at,
                )
            )
            watermains_list = result.mappings().all()
            # print(watermains_list)

            logger.info(f"✅ Retrieved {len(watermains_list)} watermains from DB")

            if not watermains_list:
                delay = min(INITIAL_RETRY_DELAY * (2 ** retry_count), 60)
                
                if retry_count < 5:
                    logger.warning(f"⚠️ No watermains found in DB. Retrying in {delay} seconds... (Attempt {retry_count + 1}/5)")
                    await asyncio.sleep(delay)
                    return await preload_redis(retry_count + 1)
                else:
                    logger.error("❌ Max retries reached. No watermains data available to cache.")
                    return False

            # Store each watermain in Redis hash with object_id as field
            for wm in watermains_list:
                watermain_data = {
                    "id": wm["id"],
                    "city": wm["city"],
                    "dataset_type": wm["dataset_type"],
                    "object_id": wm["object_id"],
                    "watmain_id": wm["watmain_id"],
                    "status": wm["status"],
                    "pressure_zone": wm["pressure_zone"],
                    "material": wm["material"],
                    "condition_score": float(wm["condition_score"]) if wm["condition_score"] else None,
                    "shape_length": float(wm["shape_length"]) if wm["shape_length"] else None,
                    "geometry": wm["geometry"],
                    "created_at": wm["created_at"].isoformat() if wm["created_at"] else None,
                    "updated_at": wm["updated_at"].isoformat() if wm["updated_at"] else None,
                }
                redis_client.hset("watermains:all", str(wm["object_id"]), json.dumps(watermain_data))

            logger.info(f"✅ Successfully cached {len(watermains_list)} watermains in Redis, including geometry")
            return True

    except Exception as e:
        logger.error(f"❌ Error during Redis preload: {str(e)}")

        if retry_count < 5:
            delay = min(5 * (2 ** retry_count), 60)
            logger.warning(f"🔄 Retrying in {delay} seconds... (Attempt {retry_count + 1}/5)")
            await asyncio.sleep(delay)
            return await preload_redis(retry_count + 1)

        return False
