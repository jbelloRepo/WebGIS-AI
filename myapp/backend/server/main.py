from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.endpoints import watermains
from .db.session import engine
from .db import models

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="WebGIS-AI API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(watermains.router, prefix="/api/v1", tags=["watermains"])

@app.get("/")
def read_root():
    return {"message": "Welcome to WebGIS-AI API"}