import os
import hashlib
import shutil
import requests # <--- NUEVA IMPORTACIÓN
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Enum, ForeignKey, DECIMAL, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel
from datetime import datetime

# --- CONFIGURACIÓN DE BASE DE DATOS ---
DATABASE_URL = "mysql+mysqlconnector://root:@localhost:3306/db_paquexpress"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELOS SQLALCHEMY ---
class User(Base):
    __tablename__ = "P9_users"
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True)
    password_hash = Column(String(255))
    full_name = Column(String(100))
    role = Column(Enum('ADMIN', 'WORKER'))

class Package(Base):
    __tablename__ = "P9_packages"
    package_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("P9_users.user_id"))
    destination_address = Column(String(255))
    description = Column(String(255))
    delivery_status = Column(Enum('PENDIENTE', 'ENTREGADO', 'FALLIDO'), default='PENDIENTE')
    agent = relationship("User")

class Delivery(Base):
    __tablename__ = "P9_deliveries"
    delivery_id = Column(Integer, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("P9_packages.package_id"))
    agent_id = Column(Integer, ForeignKey("P9_users.user_id"))
    latitude = Column(DECIMAL(10, 8))
    longitude = Column(DECIMAL(11, 8))
    location_address = Column(String(255))
    photo_path = Column(String(255))
    registered_at = Column(TIMESTAMP, default=datetime.now)

Base.metadata.create_all(bind=engine)

# --- SCHEMAS PYDANTIC ---
class LoginRequest(BaseModel):
    username: str
    password: str

class PackageCreate(BaseModel):
    user_id: int
    destination_address: str
    description: str

class PackageUpdate(BaseModel):
    user_id: Optional[int] = None
    destination_address: Optional[str] = None
    description: Optional[str] = None
    
class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None

# --- APP FASTAPI ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- ENDPOINTS ---

@app.post("/login")
def login(creds: LoginRequest, db: Session = Depends(get_db)):
    hashed_pw = hashlib.md5(creds.password.encode()).hexdigest()
    user = db.query(User).filter(User.username == creds.username, User.password_hash == hashed_pw).first()
    if not user:
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")
    return {"user_id": user.user_id, "full_name": user.full_name, "role": user.role}

@app.get("/workers")
def get_workers(db: Session = Depends(get_db)):
    return db.query(User).filter(User.role == 'WORKER').all()

@app.post("/register/worker")
def register_worker(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    hashed_pw = hashlib.md5(user.password.encode()).hexdigest()
    new_user = User(username=user.username, password_hash=hashed_pw, full_name=user.full_name, role='WORKER')
    db.add(new_user)
    db.commit()
    return {"message": "Trabajador registrado"}

@app.put("/workers/{user_id}")
def update_worker(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.user_id == user_id, User.role == 'WORKER').first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Trabajador no encontrado")
    if user_update.full_name: db_user.full_name = user_update.full_name
    if user_update.password: db_user.password_hash = hashlib.md5(user_update.password.encode()).hexdigest()
    db.commit()
    return {"message": "Trabajador actualizado"}

@app.delete("/workers/{user_id}")
def delete_worker(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.user_id == user_id, User.role == 'WORKER').first()
    if not db_user: raise HTTPException(status_code=404, detail="Trabajador no encontrado")
    try:
        db.delete(db_user)
        db.commit()
    except:
        db.rollback()
        raise HTTPException(status_code=400, detail="No se puede eliminar (tiene datos asociados)")
    return {"message": "Trabajador eliminado"}

@app.get("/packages")
def get_all_packages(db: Session = Depends(get_db)):
    return db.query(Package).all()

@app.post("/packages")
def create_package(pkg: PackageCreate, db: Session = Depends(get_db)):
    new_pkg = Package(user_id=pkg.user_id, destination_address=pkg.destination_address, description=pkg.description)
    db.add(new_pkg)
    db.commit()
    return new_pkg

@app.delete("/packages/{pkg_id}")
def delete_package(pkg_id: int, db: Session = Depends(get_db)):
    db_pkg = db.query(Package).filter(Package.package_id == pkg_id).first()
    if not db_pkg: raise HTTPException(status_code=404, detail="Paquete no encontrado")
    db_delivery = db.query(Delivery).filter(Delivery.package_id == pkg_id).first()
    if db_delivery: db.delete(db_delivery)
    db.delete(db_pkg)
    db.commit()
    return {"message": "Paquete eliminado"}

@app.get("/my-packages/{user_id}")
def get_my_packages(user_id: int, db: Session = Depends(get_db)):
    return db.query(Package).filter(Package.user_id == user_id, Package.delivery_status == 'PENDIENTE').all()

# --- ENDPOINT MODIFICADO CON TU LÓGICA DE NOMINATIM ---
@app.post("/deliver")
def register_delivery(
    package_id: int = Form(...),
    agent_id: int = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    # location_address: str = Form(""), # Ya no es obligatorio que lo envíe el frontend
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. Guardar archivo
    file_location = f"uploads/{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 2. IMPLEMENTACIÓN DE TU CÓDIGO (Nominatim)
    address_detected = "Dirección no disponible"
    try:
        # Consumir API pública de Nominatim
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}"
        headers = {"User-Agent": "PaquexpressApp/1.0"} # Header personalizado
        response = requests.get(url, headers=headers, timeout=5) # Timeout de seguridad

        if response.status_code == 200:
            result = response.json()
            
            # Intenta obtener una dirección detallada o el nombre de la vía
            if 'address' in result and result['address']:
                addr = result['address']
                # Construye una dirección más específica
                street = addr.get('road')
                house = addr.get('house_number')
                # Priorizar ciudad, pueblo o villa
                city = addr.get('city') or addr.get('town') or addr.get('village') or addr.get('county')

                if street and house:
                    address_detected = f"{street} #{house}, {city or ''}"
                elif street:
                    address_detected = f"{street}, {city or ''}"
                else:
                    address_detected = result.get("display_name", "Dirección general no disponible")
            else:
                address_detected = result.get("display_name", "Dirección general no disponible")
    except Exception as e:
        print(f"Error en Nominatim: {e}")
        # Si falla, address_detected se queda como "Dirección no disponible"
    
    # 3. Crear registro en BD usando la dirección obtenida
    new_delivery = Delivery(
        package_id=package_id,
        agent_id=agent_id,
        latitude=latitude,
        longitude=longitude,
        location_address=address_detected, # Guardamos la dirección calculada
        photo_path=file_location
    )
    
    # 4. Actualizar estado del paquete
    pkg = db.query(Package).filter(Package.package_id == package_id).first()
    if pkg:
        pkg.delivery_status = 'ENTREGADO'
    
    db.add(new_delivery)
    db.commit()
    
    return {
        "message": "Entrega registrada exitosamente",
        "detected_address": address_detected
    }