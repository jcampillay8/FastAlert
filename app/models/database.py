# app/models/database.py
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Vecino(Base):
    __tablename__ = "vecinos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    telefono = Column(String, unique=True, index=True)
    activo = Column(Boolean, default=True)
    
    alertas = relationship("LogAlerta", back_populates="vecino")

class LogAlerta(Base):
    __tablename__ = "logs_alerta"

    id = Column(Integer, primary_key=True, index=True)
    vecino_id = Column(Integer, ForeignKey("vecinos.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    fotos_count = Column(Integer, default=0)
    
    vecino = relationship("Vecino", back_populates="alertas")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Inicializar DB
def init_db():
    Base.metadata.create_all(bind=engine)
