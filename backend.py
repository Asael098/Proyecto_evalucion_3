# --- Importaciones Adicionales ---
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr # Usaremos EmailStr para validar email
# ... (tus otras importaciones de sqlalchemy, fastapi, etc.)

# --- Configuración de Hashing ---
# Configura el contexto de hashing (usando bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Modelos SQLAlchemy ---
# ... (Aquí va tu clase Alumno) ...

# NUEVO: Modelo de Usuario para la DB
class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100))
    email = Column(String(100), unique=True, index=True) # Email debe ser único
    hashed_password = Column(String(255)) # Columna para la contraseña hasheada

# --- Creación de Tablas ---
# Asegúrate de que esta línea se ejecute para crear la nueva tabla 'usuarios'
Base.metadata.create_all(bind=engine)


# --- Esquemas Pydantic ---
# ... (Tus esquemas de Alumno) ...

# NUEVO: Esquemas para Usuario
class UserCreateSchema(BaseModel):
    nombre: str
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str

# --- Endpoints de Autenticación ---

# NUEVO: Endpoint para registrar un usuario
@app.post("/register/")
def registrar_usuario(user: UserCreateSchema):
    db = SessionLocal()
    
    # 1. Verificar si el email ya existe
    db_user = db.query(Usuario).filter(Usuario.email == user.email).first()
    if db_user:
        db.close()
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    # 2. Hashear la contraseña
    hashed_password = pwd_context.hash(user.password)
    
    # 3. Crear el nuevo usuario
    nuevo_usuario = Usuario(
        nombre=user.nombre,
        email=user.email,
        hashed_password=hashed_password
    )
    
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    db.close()
    
    return {"mensaje": "Usuario creado exitosamente", "email": nuevo_usuario.email}


# NUEVO: Endpoint de Login
@app.post("/login/")
def login_usuario(user_data: UserLoginSchema):
    db = SessionLocal()
    
    # 1. Buscar al usuario por email
    user = db.query(Usuario).filter(Usuario.email == user_data.email).first()
    db.close()

    # 2. Verificar si el usuario existe Y si la contraseña es correcta
    if not user:
        # Error genérico para no dar pistas a atacantes
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

    # 3. Compara la contraseña enviada con el hash guardado
    if not pwd_context.verify(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

    # 4. ¡Login Exitoso!
    # En una app real, aquí es donde generarías un Token (JWT)
    return {"mensaje": "Login exitoso", "usuario_id": user.id, "nombre": user.nombre}

# ... (Tus endpoints de Alumnos) ...