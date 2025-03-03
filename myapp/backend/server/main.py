from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.endpoints import watermains
from api.db.session import engine
from api.db import models
import asyncio

app = FastAPI(title="WebGIS-AI API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(watermains.router, prefix="/watermains", tags=["Water Mains"])

@app.get("/")
async def root():
    return {"message": "Welcome to WebGIS-AI API"}

# Create tables on startup
@app.on_event("startup")
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)