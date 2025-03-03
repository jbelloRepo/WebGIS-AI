from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class WaterMainBase(BaseModel):
    city: str
    dataset_type: str
    object_id: int
    watmain_id: Optional[int] = None
    status: Optional[str] = "UNKNOWN"
    pressure_zone: Optional[str] = "UNKNOWN"
    material: Optional[str] = "UNKNOWN"
    condition_score: Optional[float] = -1
    shape_length: Optional[float] = None

class WaterMainCreate(WaterMainBase):
    pass

class WaterMainResponse(WaterMainBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
