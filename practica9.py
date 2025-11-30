from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    TIMESTAMP,
    ForeignKey,
    DECIMAL,
    desc,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from pydantic import BaseModel
import hashlib  # Para encriptar con MD5
import requests
from datetime import datetime, timezone
from fastapi.middleware.cors import CORSMiddleware

# Conexión a la base de datos
DATABASE_URL = "mysql+mysqlconnector://root@localhost/db_gmartin_dapps"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

app = FastAPI()

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Puedes poner "*" para permitir todos los orígenes, o una lista específica
    allow_credentials=True,
    allow_methods=["*"], # Permite todos los métodos: GET, POST, PUT, DELETE
    allow_headers=["*"], # Permite todas las cabeceras
)

# Modelos SQLAlchemy
class User(Base):
    __tablename__ = "P9_users"
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    created_at = Column(TIMESTAMP, default=datetime.now(timezone.utc))

class Attendance(Base):
    __tablename__ = "P9_attendance"
    attendance_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("P9_users.user_id"))
    latitude = Column(
        DECIMAL(10, 8), nullable=False
    ) # DECIMAL con precisión 10 y 8 decimales
    longitude = Column(
        DECIMAL(11, 8), nullable=False
    ) # DECIMAL con precisión 11 y 8 decimales
    address = Column(String(255))
    registered_at = Column(TIMESTAMP, default=datetime.now(timezone.utc)) 
    user = relationship("User")

Base.metadata.create_all(bind=engine)

# Modelos Pydantic para validación de datos
class RegisterModel(BaseModel):
    username: str
    password: str
    full_name: str

class LoginModel(BaseModel):
    username: str
    password: str

class AttendanceModel(BaseModel):
    user_id: int
    latitude: float
    longitude: float
    
# Modelo Pydantic para la respuesta del historial (necesario para serializar)
class AttendanceResponse(BaseModel):
    registered_at: datetime
    address: str
    latitude: float
    longitude: float

# Dependencia DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Función para encriptar con MD5
def md5_hash(password: str) -> str:
    return hashlib.md5(password.encode()).hexdigest()

# Endpoint: Registro de usuario
@app.post("/register/")
def register(data: RegisterModel, db=Depends(get_db)):
    hashed_pw = md5_hash(data.password) # Encriptación con MD5
    user = User(
        username=data.username, password_hash=hashed_pw, full_name=data.full_name
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"msg": "Usuario registrado", "user_id": user.user_id}

# Endpoint: Login
@app.post("/login/")
def login(data: LoginModel, db=Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or user.password_hash != md5_hash(data.password):
        raise HTTPException(status_code=400, detail="Credenciales inválidas")
    return {"msg": "Login exitoso", "user_id": user.user_id}

# --- CORRECCIÓN 1: Endpoint de Historial (Filtrado y formato de hora) ---
@app.get("/attendance/history", response_model=list[AttendanceResponse])
def get_attendance_history(
    user_id: int = Query(..., description="ID del usuario para filtrar el historial"), 
    db: Session = Depends(get_db)
):
    # Filtra por user_id, asegurando que solo se obtengan los registros del usuario logueado
    records = (
        db.query(Attendance)
        .filter(Attendance.user_id == user_id)
        .order_by(desc(Attendance.registered_at))
        .all()
    )
    
    # La respuesta incluye 'registered_at' como objeto datetime, lo cual es serializado a ISO 8601 por FastAPI.
    return records
# --------------------------------------------------------------------------

# --- CORRECCIÓN 2: Endpoint de Registro (Mejora en la obtención de la dirección) ---
@app.post("/attendance/")
def attendance(data: AttendanceModel, db=Depends(get_db)):
    try:
        # Consumir API pública de Nominatim con cabecera obligatoria
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={data.latitude}&lon={data.longitude}"
        headers = {"User-Agent": "FastAPIApp/1.0"} # Cabecera requerida
        response = requests.get(url, headers=headers)

        address = "Dirección no disponible"

        if response.status_code == 200:
            result = response.json()
            
            # Intenta obtener una dirección detallada o el nombre de la vía
            if 'address' in result and result['address']:
                addr = result['address']
                # Construye una dirección más específica, priorizando calle y número
                street = addr.get('road')
                house = addr.get('house_number')
                city = addr.get('city') or addr.get('town') or addr.get('village')

                if street and house:
                    address = f"{street} #{house}, {city or 'Localidad desconocida'}"
                elif street:
                    address = f"{street}, {city or 'Localidad desconocida'}"
                else:
                    # Si no hay calle, usa la descripción general de Nominatim
                    address = result.get("display_name", "Dirección general no disponible")
            else:
                 address = result.get("display_name", "Dirección general no disponible")

        # Guardar registro en BD
        record = Attendance(
            user_id=data.user_id,
            latitude=data.latitude,
            longitude=data.longitude,
            address=address,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return {
            "msg": "Registro guardado",
            "attendance_id": record.attendance_id,
            "address": address,
            "registered_at": record.registered_at # Devuelve la hora precisa para confirmación
        }

    except Exception as e:
        # Se lanza un 500 para errores internos (DB, Nominatim, etc.)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")