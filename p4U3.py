from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Literal

app = FastAPI()
base_alumnos: List["Alumno"] = []

class Alumno(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=100)
    edad: int = Field(..., ge=5, le=100)
    correo: EmailStr
    grupo: str = Field(..., min_length=1)
    origen: Literal["rural", "urbano"]
    

@app.post("/registrar")
def registrar_alumno(alumno: Alumno):
    if any(a.correo == alumno.correo for a in base_alumnos):
        raise HTTPException(status_code=400, detail="El correo ya está registrado.")
    base_alumnos.append(alumno)
    return {"mensaje": f"Alumno {alumno.nombre} registrado correctamente en el grupo {alumno.grupo}"}

@app.get("/listar")
def listar_alumnos(grupo: Optional[str] = None, edad_minima: Optional[int] = None, origen: Optional[str]=None):
    resultado = base_alumnos
    if grupo:
        resultado = [a for a in resultado if a.grupo == grupo]
    if edad_minima:
        resultado = [a for a in resultado if a.edad >= edad_minima]
    return resultado

@app.get("/estadisticas")
def devolver_estatidisticas(grupo: Optional[str] = None):
    resultado = base_alumnos
    if grupo:
        gg=0
        for a in resultado:
            if a.grupo==grupo:
                gg=gg+1
                resultado = {"mensaje": f"el total de alumnos resgistrados del grupo: {grupo} es: {gg}"}
    else:
                
        
        
        cont=0
        cont2=0
        cont3=0
        
        for a in resultado:
            cont=cont+1
            if a.origen =="rural":
                cont2=cont2+1
            elif a.origen =="urbano":
                cont3=cont3+1
            resultado= {"mensaje": f"total de registros: {cont} total de rurales: {cont2} total de urbanos: {cont3}"}
     
    return resultado


