from sqlalchemy import Column, Integer, String, Float, DateTime, Numeric
from geoalchemy2 import Geometry
from .session import Base

class WaterMain(Base):
    __tablename__ = "water_mains"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, nullable=False)
    dataset_type = Column(String, nullable=False)
    object_id = Column(Integer, unique=True, nullable=False)
    watmain_id = Column(Integer)
    status = Column(String)
    pressure_zone = Column(String)
    material = Column(String)
    pipe_size = Column(Numeric)
    installation_date = Column(DateTime)
    geometry = Column(Geometry('LINESTRING', srid=4326)) 