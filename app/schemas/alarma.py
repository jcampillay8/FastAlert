# app/schemas/alarma.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AlarmStatus(BaseModel):
    active: bool

class AlarmActivate(BaseModel):
    telefono: str

class VecinoBase(BaseModel):
    nombre: str
    telefono: str
    activo: bool = True

class VecinoCreate(VecinoBase):
    pass

class VecinoSchema(VecinoBase):
    id: int

    class Config:
        from_attributes = True
