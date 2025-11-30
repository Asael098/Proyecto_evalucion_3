from fastapi import FastAPI
import datetime
app = FastAPI()



def saludo():
    actual= datetime.datetime.now()
    if actual.hour<12:
        saludo="buenos dias"
    elif actual.hour>=12 and actual.hour<18 :
        saludo="buenas tardes"
    else:
        saludo="buenas noches"
    
    return saludo

@app.get("/")
def read_root():
    return {"mensaje": "Hola Mundo"}

@app.get("/saludo/{nombre}")
def saludar(nombre: str):
    longitud= len(nombre)
    if(longitud>8):
        text1="tu nombre es largo y elegante"
    else:
        text1="tu nombre es corto y poderoso"
    
        
    
    return {"mensaje": f"Hola, {saludo()} {nombre}, {text1} "}
