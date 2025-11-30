# Importamos FastAPI y herramientas para validación
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List,Literal
import sqlite3

# Inicializamos la aplicación FastAPI
app = FastAPI()

# Conectamos a la base de datos SQLite (se crea automáticamente si no existe)
conn = sqlite3.connect("alumnos.db", check_same_thread=False)
cursor = conn.cursor()

# Creamos la tabla si no existe
cursor.execute("""
CREATE TABLE IF NOT EXISTS alumnos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    edad INTEGER NOT NULL,
    correo TEXT UNIQUE NOT NULL,
    grupo TEXT NOT NULL,
    origen TEXT
)
""")
conn.commit()

# Definimos el modelo de datos con validaciones
class Alumno(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=100)
    edad: int = Field(..., ge=5, le=100)
    correo: EmailStr
    grupo: str = Field(..., min_length=1)
    origen: Literal["rural", "urbano"]

# Endpoint para registrar un alumno (POST con JSON)
@app.post("/registrar")
def registrar(alumno: Alumno):
    try:
        cursor.execute("""
            INSERT INTO alumnos (nombre, edad, correo, grupo, origen)
            VALUES (?, ?, ?, ?, ?)
        """, (alumno.nombre, alumno.edad, alumno.correo, alumno.grupo, alumno.origen))
        conn.commit()
        return {"mensaje": f"Alumno {alumno.nombre} registrado correctamente"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Correo ya registrado")

# Endpoint para consultar alumnos (GET con filtros opcionales)
@app.get("/consultar")
def consultar(grupo: Optional[str] = None, edad_minima: Optional[int] = None):
    query = "SELECT * FROM alumnos WHERE 1=1"
    params = []

    if grupo:
        query += " AND grupo = ?"
        params.append(grupo)
    if edad_minima:
        query += " AND edad >= ?"
        params.append(edad_minima)

    cursor.execute(query, params)
    datos = cursor.fetchall()
    return datos

# Endpoint para actualizar alumno por ID (PUT con JSON)
@app.put("/actualizar/{id}")
def actualizar(id: int, alumno: Alumno):
    cursor.execute("""
        UPDATE alumnos
        SET nombre = ?, edad = ?, correo = ?, grupo = ?, origen = ?
        WHERE id = ?
    """, (alumno.nombre, alumno.edad, alumno.correo, alumno.grupo, alumno.origen, id))
    conn.commit()
    return {"mensaje": f"Alumno con ID {id} actualizado"}

# Endpoint para eliminar alumno por ID (DELETE)
@app.delete("/eliminar/{id}")
def eliminar(id: int):
    cursor.execute("DELETE FROM alumnos WHERE id = ?", (id,))
    conn.commit()
    return {"mensaje": f"Alumno con ID {id} eliminado"}
    
@app.get("/estadisticas")
def obtener_estadisticas():
    """
    Devuelve un resumen estadístico de los alumnos.
    - Total de alumnos registrados.
    - Desglose de alumnos por grupo.
    - Desglose de alumnos por origen (rural/urbano).
    """
    estadisticas = {}

    # 1. Total de alumnos registrados
    try:
        cursor.execute("SELECT COUNT(*) FROM alumnos")
        total_alumnos = cursor.fetchone()[0]
        estadisticas["total_alumnos_registrados"] = total_alumnos

        # 2. Total por grupo
        cursor.execute("SELECT grupo, COUNT(*) FROM alumnos GROUP BY grupo")
        grupos_data = cursor.fetchall()
        # Convertimos la lista de tuplas [('A', 5), ('B', 10)] a un diccionario {'A': 5, 'B': 10}
        estadisticas["total_por_grupo"] = {grupo: count for grupo, count in grupos_data}

        # 3. Total por origen
        cursor.execute("SELECT origen, COUNT(*) FROM alumnos GROUP BY origen")
        origen_data = cursor.fetchall()
        
        total_por_origen = {}
        for origen, count in origen_data:
            # Manejamos el caso de que 'origen' sea NULL (None en Python)
            key = origen if origen is not None else "no_especificado"
            total_por_origen[key] = count
        
        estadisticas["total_por_origen"] = total_por_origen

        return estadisticas
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al consultar estadísticas: {e}")