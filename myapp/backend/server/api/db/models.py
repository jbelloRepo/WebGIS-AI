from sqlalchemy import Column, Integer, String, Numeric, TIMESTAMP, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry
from datetime import datetime
import uuid

Base = declarative_base()

class WaterMain(Base):
    __tablename__ = "water_mains"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String(100), nullable=False)
    dataset_type = Column(String(100), nullable=False)
    object_id = Column(Integer, unique=True, nullable=False)
    watmain_id = Column(Integer, nullable=True)
    status = Column(String(50), default="UNKNOWN")
    pressure_zone = Column(String(50), default="UNKNOWN")
    roadsegment_id = Column(Integer, nullable=True)
    map_label = Column(String(255), nullable=True)
    category = Column(String(50), default="TREATED")
    pipe_size = Column(Numeric, default=0)
    material = Column(String(100), default="UNKNOWN")
    lined = Column(String(20), default="NO")
    lined_date = Column(TIMESTAMP, nullable=True)
    lined_material = Column(String(50), default="NONE")
    installation_date = Column(TIMESTAMP, nullable=True)
    acquisition = Column(String(50), nullable=True)
    consultant = Column(String(250), nullable=True)
    ownership = Column(String(100), default="UNKNOWN")
    bridge_main = Column(String(1), default="N")
    bridge_details = Column(String(250), nullable=True)
    criticality = Column(Integer, default=-1)
    condition_score = Column(Numeric, default=-1)
    cleaned = Column(String(1), default="N")
    shape_length = Column(Numeric, nullable=True)
    geometry = Column(Geometry("LINESTRING", 4326))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), nullable=False)
    user_id = Column(String(36), nullable=True)  # For future user authentication
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), ForeignKey("chat_sessions.session_id"), nullable=False)
    message_type = Column(String(10), nullable=False)  # "user" or "ai"
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    message_metadata = Column(Text, nullable=True)  # Store additional information like filter IDs as JSON
