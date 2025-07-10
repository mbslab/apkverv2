import os
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка подключения к базе данных
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Модель SQLAlchemy
class ApkModel(Base):
    __tablename__ = "allapk"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    vers = Column(Float, index=True)
    isdismiss = Column(Boolean, default=True)
    description = Column(String, default='')

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Pydantic модель
class ApkBase(BaseModel):
    name: Optional[str] = ''
    vers: Optional[float] = None
    isdismiss: Optional[bool] = True
    description: Optional[str] = ''

    model_config = ConfigDict(from_attributes=True)

class ApkCreate(ApkBase):
    pass

class Apk(ApkBase):
    id: int

app = FastAPI(docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешает все источники
    allow_credentials=True,
    allow_methods=["*"],  # Разрешает все методы
    allow_headers=["*"],  # Разрешает все заголовки
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/apk/id/{apk_id}", response_model=Apk)
def read_apk(apk_id: int, db: Session = Depends(get_db)):
    db_apk = db.query(ApkModel).filter(ApkModel.id == apk_id).first()
    if db_apk is None:
        raise HTTPException(status_code=404, detail="APK not found")
    return db_apk
class ApkResponse(BaseModel):
    apks: List[Apk]
    total: int

@app.get("/apks/", response_model=ApkResponse)
def read_apks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    apks = db.query(ApkModel).offset(skip).limit(limit).all()
    total = db.query(ApkModel).count()
    return ApkResponse(apks=apks, total=total)

@app.get("/apk/name/{name}", response_model=Apk)
def get_first_apk_by_name(name: str, db: Session = Depends(get_db)):
    apk = db.query(ApkModel).filter(ApkModel.name == name).first()
    if not apk:
        raise HTTPException(status_code=404, detail="APK not found with the given name")
    return apk

@app.get("/api/v2/apk/")
def get_apks_simple_format(db: Session = Depends(get_db)):
    """Возвращает APK в формате {name: version}"""
    apks = db.query(ApkModel).all()
    result = {}
    for apk in apks:
        if apk.name:  # Проверяем что имя не пустое
            result[apk.name] = apk.vers
    return result

@app.get("/debug/db-info")
def debug_db_info(db: Session = Depends(get_db)):
    total = db.query(ApkModel).count()
    all_names = [apk.name for apk in db.query(ApkModel).limit(10).all()]
    return {
        "total_apks": total,
        "first_10_names": all_names,
        "database_connection": "OK"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
