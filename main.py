from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import Optional, List

# Настройка подключения к базе данных
SQLALCHEMY_DATABASE_URL = "postgresql://dbapkvers:AVNS_FGItGmY_X-k6IMY21_n@app-c2631fda-54d2-47d7-a6ba-be9f90500b67-do-user-8735824-0.b.db.ondigitalocean.com:25060/dbapkvers?sslmode=require"
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
    vers: Optional[float]
    isdismiss: Optional[bool] = True
    description: Optional[str] = ''

    class Config:
        orm_mode = True

class ApkCreate(ApkBase):
    pass

class Apk(ApkBase):
    id: int

app = FastAPI()

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

@app.get("/apks/", response_model=List[Apk])
def read_apks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    apks = db.query(ApkModel).offset(skip).limit(limit).all()
    return apks

@app.get("/apk/name/{name}", response_model=Apk)
def get_first_apk_by_name(name: str, db: Session = Depends(get_db)):
    apk = db.query(ApkModel).filter(ApkModel.name == name).first()
    if not apk:
        raise HTTPException(status_code=404, detail="APK not found with the given name")
    return apk

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)