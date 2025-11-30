# Importamos FastAPI para crear la aplicación web
from fastapi import FastAPI, Query

# Importamos herramientas de Pydantic para validar los datos
from pydantic import BaseModel, Field, EmailStr

# Creamos una instancia de la aplicación FastAPI
app = FastAPI()

# Simulamos una base de datos como una lista vacía
base_alumnos = []

# Definimos un modelo Alumno usando Pydantic para validar los datos
class Alumno(BaseModel):
    # El nombre debe tener entre 2 y 50 caracteres
    nombre: str = Field(..., min_length=2, max_length=50)
    
    # La edad debe estar entre 5 y 100 años
    edad: int = Field(..., ge=5, le=100)
    
    # El correo debe tener formato válido (se valida como EmailStr)
    correo: EmailStr
    
    # El grupo debe tener al menos 1 carácter
    grupo: str = Field(..., min_length=1)

# Definimos un endpoint GET para registrar alumnos usando parámetros en la URL
@app.get("/registrar")
def registrar_alumno(
    # Cada parámetro se valida igual que en el modelo, pero se recibe desde la URL
    nombre: str = Query(..., min_length=2, max_length=50),
    edad: int = Query(..., ge=5, le=100),
    correo: EmailStr = Query(...),
    grupo: str = Query(..., min_length=1)
):
    # Creamos un objeto Alumno con los datos recibidos
    alumno = Alumno(nombre=nombre, edad=edad, correo=correo, grupo=grupo)
    
    # Lo agregamos a la base simulada
    base_alumnos.append(alumno)
    
    # Devolvemos un mensaje de confirmación como texto plano
    return f"Alumno {alumno.nombre} registrado correctamente en el grupo {alumno.grupo}"