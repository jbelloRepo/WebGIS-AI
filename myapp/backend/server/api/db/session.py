from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os

# ✅ Make sure asyncpg is used
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://gis_user:password@postgis-db-service:5432/gis_data")

engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
