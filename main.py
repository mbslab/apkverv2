import os
from fastapi import FastAPI, HTTPException, Depends, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from dotenv import load_dotenv
from fastapi.responses import FileResponse

# Загрузка переменных окружения
load_dotenv()

# Настройка подключения к базе данных
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
API_KEY = os.getenv("API_KEY")

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# ВСЕ модели SQLAlchemy ВМЕСТЕ
class ApkModel(Base):
    __tablename__ = "allapk"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    vers = Column(Float, index=True)
    isdismiss = Column(Boolean, default=True)
    description = Column(String, default='')

class BandleCorrModel(Base):
    __tablename__ = "bandleCorr"

    id = Column(Integer, primary_key=True, index=True)
    bandle = Column(String, index=True)
    project = Column(String, index=True)
    platform = Column(String, index=True)

# Создание ВСЕХ таблиц ПОСЛЕ определения ВСЕХ моделей
Base.metadata.create_all(bind=engine)

# Pydantic модели
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

class BandleCorrBase(BaseModel):
    bandle: Optional[str] = ''
    project: Optional[str] = ''
    platform: Optional[str] = ''

    model_config = ConfigDict(from_attributes=True)

class BandleCorrCreate(BandleCorrBase):
    pass

class BandleCorr(BandleCorrBase):
    id: int

class ApkResponse(BaseModel):
    apks: List[Apk]
    total: int

app = FastAPI(docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        if apk.name:
            result[apk.name] = apk.vers
    return result

@app.get("/")
def read_index(key: Optional[str] = None):
    if key != API_KEY:
        raise HTTPException(
            status_code=401, 
            detail="Access denied. Please provide valid API key."
        )
    return FileResponse('index.html')

@app.post("/apk/", response_model=Apk, dependencies=[Depends(verify_api_key)])
def create_apk_item(apk: ApkCreate, db: Session = Depends(get_db)):
    db_apk = ApkModel(**apk.dict())
    db.add(db_apk)
    db.commit()
    db.refresh(db_apk)
    return db_apk

@app.put("/apk/{apk_id}", response_model=Apk, dependencies=[Depends(verify_api_key)])
def update_apk_item(apk_id: int, apk: ApkCreate, db: Session = Depends(get_db)):
    db_apk = db.query(ApkModel).filter(ApkModel.id == apk_id).first()
    if db_apk is None:
        raise HTTPException(status_code=404, detail="APK not found")
    
    for field, value in apk.dict(exclude_unset=True).items():
        setattr(db_apk, field, value)
    
    db.commit()
    db.refresh(db_apk)
    return db_apk

@app.delete("/apk/{apk_id}")
def delete_apk_item(apk_id: int, db: Session = Depends(get_db), _: str = Depends(verify_api_key)):
    db_apk = db.query(ApkModel).filter(ApkModel.id == apk_id).first()
    if db_apk is None:
        raise HTTPException(status_code=404, detail="APK not found")
    
    db.delete(db_apk)
    db.commit()
    return {"message": "APK deleted successfully"}

# BandleCorr endpoint
@app.post("/bandlecorr/", response_model=BandleCorr, dependencies=[Depends(verify_api_key)])
def create_bandle_corr_item(bandle: BandleCorrCreate, db: Session = Depends(get_db)):
    try:
        db_bandle = BandleCorrModel(**bandle.dict())
        db.add(db_bandle)
        db.commit()
        db.refresh(db_bandle)
        return db_bandle
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
