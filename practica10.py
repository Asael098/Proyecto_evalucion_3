# ----------------------------------------------------
# IMPORTS
# ----------------------------------------------------

# Importa la clase datetime para manejar fechas y horas
from datetime import datetime

# Importa Optional para declarar campos que pueden ser nulos en los modelos de validación
from typing import Optional

# Importa FastAPI y componentes para manejar formularios, archivos subidos y errores HTTP
from fastapi import FastAPI, UploadFile, Form, File, HTTPException

# Importa funciones de SQLAlchemy para definir esquemas de validación y serialización de datos
from sqlalchemy import create_engine, Column, Integer, String, TIMESTAMP

# Importa la función para declarar una base común para los modelos de base de datos
from sqlalchemy.ext.declarative import declarative_base

# Importa el manejador de sesiones para interactuar con la base de datos
from sqlalchemy.orm import sessionmaker

# Importa BaseModel para definir esquemas de validación y serialización de datos
from pydantic import BaseModel

# Importa StaticFiles para servir archivos estáticos como imágenes desde una carpeta
from fastapi.staticfiles import StaticFiles

# Importa CORSMiddleware para permitir peticiones desde otros dominios (por ejemplo, Flutter Web)
from fastapi.middleware.cors import CORSMiddleware

# Importa shutil para copiar archivos desde el buffer de subida al sistema de archivos
import shutil

# Importa os para crear carpetas y manejar rutas de archivos
import os

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ----------------------------------------------------
# CONFIGURACIÓN DE FASTAPI Y CORS
# ----------------------------------------------------

# Inicializa la aplicación FastAPI
app = FastAPI()

# Monta la carpeta 'uploads' como ruta accesible públicamente desde el navegador
# Esto permite acceder a las imágenes subidas mediante URLs como /uploads/foto.jpg
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Configura el middleware CORS para permitir peticiones desde cualquier origen
# Esto es necesario para que aplicaciones como Flutter Web puedan comunicarse con esta API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Se puede restringir a dominios específicos si se desea mayor seguridad
    allow_credentials=True,
    allow_methods=["*"], # Permite todos los métodos HTTP (GET, POST, etc.)
    allow_headers=["*"], # Permite todos los encabezados en las peticiones
)

# ----------------------------------------------------
# CONFIGURACIÓN DE BASE DE DATOS (MySQL con SQLAlchemy)
# ----------------------------------------------------

# Define la cadena de conexión a la base de datos MySQL
# El formato es: mysql+pymysql://usuario:contraseña@host/nombre_base_de_datos
DATABASE_URL = "mysql+pymysql://root@localhost/p10_fotos"

# Crea el motor de conexión a la base de datos usando SQLAlchemy
engine = create_engine(DATABASE_URL)

# Crea una clase de sesión que se usará para interactuar con la base de datos
SessionLocal = sessionmaker(bind=engine)

# Define una base común para los modelos de base de datos
Base = declarative_base()

# ----------------------------------------------------
# MODELOS DE BASE DE DATOS (SQLAlchemy ORM)
# ----------------------------------------------------

# Define el modelo de datos que representa la tabla 'P10_foto' en la base de datos
# Cada instancia de esta clase representa una fila en la tabla
class Foto(Base):
    __tablename__ = "P10_foto" # Nombre de la tabla en la base de datos

    # Define una columna 'id' de tipo entero, que es clave primaria y tiene índice
    # Column recibe parámetros: tipo de dato, si es clave primaria, si tiene índice, si puede ser nulo, etc.
    id = Column(Integer, primary_key=True, index=True)
    
    # Define una columna 'descripcion' de tipo cadena (máximo 255 caracteres), obligatoria
    descripcion = Column(String(255), nullable=False)
    
    # Define una columna 'ruta_foto' que guarda la ruta del archivo en el servidor, también obligatoria
    ruta_foto = Column(String(255), nullable=False)
    
    # Define una columna 'fecha' de tipo TIMESTAMP, con valor por defecto igual a la fecha actual
    fecha = Column(TIMESTAMP, default=datetime.utcnow)

# Crea las tablas en la base de datos si no existen, usando la definición del modelo anterior
Base.metadata.create_all(bind=engine)

# ----------------------------------------------------
# ESQUEMAS PYDANTIC (Serialización)
# ----------------------------------------------------

# Define un esquema de validación y serialización usando Pydantic
# Este esquema se usa para devolver datos al cliente de forma estructurada
class FotoSchema(BaseModel):
    id: int # Identificador Único de la foto
    descripcion: str # Descripción textual proporcionada por el usuario
    ruta_foto: str # Ruta del archivo en el servidor
    fecha: Optional[datetime] # Fecha de subida (puede ser nula si no se especifica)
    
    # Configura el esquema para que pueda construirse a partir de una instancia del modelo de base de datos
    class Config:
        from_attributes = True

# ----------------------------------------------------
# ENDPOINTS DE FASTAPI
# ----------------------------------------------------

# Define el endpoint POST para subir una foto
# Recibe una descripción como campo de formulario y un archivo como imagen
@app.post("/fotos/")
async def subir_foto(descripcion: str = Form(...), file: UploadFile = File(...)):
    db = SessionLocal() # Crea una sesión para interactuar con la base de datos
    try:
        ruta = f"uploads/{file.filename}" # Define la ruta donde se guardará el archivo
        os.makedirs("uploads", exist_ok=True) # Crea la carpeta 'uploads' si no existe

        # Guarda el archivo en el sistema de archivos
        # open recibe parámetros: la ruta del archivo y el modo de apertura
        # "wb" significa escritura en binario, necesario para imágenes
        with open(ruta, "wb") as buffer:
            # shutil.copyfileobj copia los datos desde el archivo subido (file.file) hacia el archivo destino (buffer)
            shutil.copyfileobj(file.file, buffer)

        # Crea una nueva instancia del modelo Foto con los datos recibidos
        nueva_foto = Foto(descripcion=descripcion, ruta_foto=ruta)

        # Agrega la nueva foto a la sesión y guarda los cambios en la base de datos
        db.add(nueva_foto)
        db.commit()
        db.refresh(nueva_foto) # Actualiza la instancia con los datos definitivos (como el ID generado)

        # Devuelve una respuesta estructurada con los datos de la foto recién guardada
        return {
            "msg": "Foto subida correctamente",
            "foto": FotoSchema.from_orm(nueva_foto),
        }
    except Exception as e:
        # Si ocurre un error, lanza una excepción HTTP con código 500 y detalle del error
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    finally:
        db.close() # Cierra la sesión de base de datos

# Define el endpoint GET para listar todas las fotos guardadas en la base de datos
@app.get("/fotos/", response_model=list[FotoSchema])
def listar_fotos():
    try:
        db = SessionLocal() # Crea una sesión para consultar la base de datos
        fotos = db.query(Foto).all() # Obtiene todas las filas de la tabla 'P10_foto'
        db.close() # Cierra la sesión
        
        # Convierte cada fila en un objeto serializado usando FotoSchema
        return [FotoSchema.from_orm(f) for f in fotos]
    except Exception as e:
        # Si ocurre un error, lanza una excepción HTTP con código 500 y detalle del error
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    finally:
        db.close() # Cierra la sesión de base de datos