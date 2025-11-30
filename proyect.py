from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from sqlalchemy import (
    create_engine, Column, Integer, String,
    DateTime, DECIMAL, ForeignKey
)
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

# ==============================
# Conexión a MySQL
# ==============================
# Usuario: root
# Contraseña: escuela_2025
# Servidor: localhost
# Base de datos: tienda_blog  (cámbiala si usas otro nombre)

DATABASE_URL = "mysql+mysqlconnector://root@localhost/blog"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# ==============================
# Inicializar FastAPI
# ==============================
app = FastAPI(title="API Blog y Tienda")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================================================
# MODELOS SQLALCHEMY (Tablas)
# ======================================================

class Usuario(Base):
    __tablename__ = "usuario"
    id_usr = Column(Integer, primary_key=True, index=True)
    nom_usr = Column(String(100), nullable=False)
    mail = Column(String(150), nullable=False, unique=True)
    passw = Column("pass", String(255), nullable=False)
    dir_usr = Column(String(255))
    tip_usu = Column(Integer, nullable=False)

class Blog(Base):
    __tablename__ = "blog"
    id_blog = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)
    descr = Column(String(500))  # <- YA ES descr
    img = Column(String(255))
    tags = Column(String(255))


class Catalogo(Base):
    __tablename__ = "catalogo"
    id_prod = Column(Integer, primary_key=True, index=True)
    nom_prod = Column(String(200), nullable=False)
    descr = Column(String(500))  # <- YA ES descr
    prec = Column(DECIMAL(10, 2), nullable=False)
    img = Column(String(255))
    estatus = Column(Integer, nullable=False)
    stock = Column(Integer, nullable=False)


class Compra(Base):
    __tablename__ = "compra"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("usuario.id_usr"), nullable=False)
    prod_id = Column(Integer, ForeignKey("catalogo.id_prod"), nullable=False)
    fecha = Column(DateTime, default=datetime.utcnow, nullable=False)
    importe = Column(Integer, nullable=False)


class Comentario(Base):
    __tablename__ = "comentarios"
    id_com = Column(Integer, primary_key=True, index=True)
    comentario = Column(String(500), nullable=False)
    fecha = Column(DateTime, default=datetime.utcnow, nullable=False)
    estatus = Column(Integer, nullable=False)
    usr_id = Column(Integer, ForeignKey("usuario.id_usr"), nullable=False)
    blog_id = Column(Integer, ForeignKey("blog.id_blog"), nullable=False)


# Crear tablas si no existen
Base.metadata.create_all(bind=engine)

# ======================================================
# ESQUEMAS PYDANTIC
# ======================================================

# ---------- USUARIO ----------

class LoginSimple(BaseModel):
    email: EmailStr
    password: str
    
    
    
class UsuarioBase(BaseModel):
    nom_usr: str = Field(..., min_length=2, max_length=100)
    mail: EmailStr
    dir_usr: Optional[str] = None
    tip_usu: int = Field(..., ge=0)


class UsuarioCreate(UsuarioBase):
    passw: str = Field(..., min_length=4, max_length=255)


class UsuarioOut(UsuarioBase):
    id_usr: int

    class Config:
        orm_mode = True


# ---------- BLOG ----------
class BlogBase(BaseModel):
    titulo: str = Field(..., min_length=2, max_length=200)
    descr: Optional[str] = None
    img: Optional[str] = None
    tags: Optional[str] = None


class BlogCreate(BlogBase):
    pass


class BlogOut(BlogBase):
    id_blog: int

    class Config:
        orm_mode = True


# ---------- CATALOGO ----------
class CatalogoBase(BaseModel):
    nom_prod: str = Field(..., min_length=2, max_length=200)
    descr: Optional[str] = None
    prec: float = Field(..., ge=0)
    img: Optional[str] = None
    estatus: int
    stock: int = Field(..., ge=0)


class CatalogoCreate(CatalogoBase):
    pass


class CatalogoOut(CatalogoBase):
    id_prod: int

    class Config:
        orm_mode = True


# ---------- COMPRA ----------
class CompraBase(BaseModel):
    cliente_id: int
    prod_id: int
    importe: int = Field(..., ge=0)
    fecha: Optional[datetime] = None


class CompraCreate(CompraBase):
    pass


class CompraOut(CompraBase):
    id: int

    class Config:
        orm_mode = True


# ---------- COMENTARIO ----------
class ComentarioBase(BaseModel):
    comentario: str = Field(..., min_length=1, max_length=500)
    estatus: int
    usr_id: int
    blog_id: int
    fecha: Optional[datetime] = None


class ComentarioCreate(ComentarioBase):
    pass


class ComentarioOut(ComentarioBase):
    id_com: int

    class Config:
        orm_mode = True


# ======================================================
# RUTAS CRUD
# ======================================================



@app.post("/login")
def login_simple(datos: LoginSimple):
    db = SessionLocal()
    usuario = db.query(Usuario).filter(Usuario.mail == datos.email).first()
    db.close()

    if not usuario:
        return {"status": "error", "msg": "Usuario no encontrado"}

    # Contraseña SIN encriptar
    if usuario.passw != datos.password:
        return {"status": "error", "msg": "Contraseña incorrecta"}

    return {"status": "ok", "msg": "Login exitoso"}

# ---------- USUARIO ----------
@app.post("/usuarios/", response_model=UsuarioOut)
def crear_usuario(datos: UsuarioCreate):
    db = SessionLocal()
    nuevo = Usuario(
        nom_usr=datos.nom_usr,
        mail=datos.mail,
        passw=datos.passw,   
        dir_usr=datos.dir_usr,
        tip_usu=datos.tip_usu,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    db.close()
    return nuevo


@app.get("/usuarios/", response_model=List[UsuarioOut])
def listar_usuarios():
    db = SessionLocal()
    usuarios = db.query(Usuario).all()
    db.close()
    return usuarios


@app.get("/usuarios/{id_usr}", response_model=UsuarioOut)
def obtener_usuario(id_usr: int):
    db = SessionLocal()
    usuario = db.query(Usuario).filter(Usuario.id_usr == id_usr).first()
    db.close()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


@app.put("/usuarios/{id_usr}", response_model=UsuarioOut)
def actualizar_usuario(id_usr: int, datos: UsuarioCreate):
    db = SessionLocal()
    usuario = db.query(Usuario).filter(Usuario.id_usr == id_usr).first()
    if not usuario:
        db.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    usuario.nom_usr = datos.nom_usr
    usuario.mail = datos.mail
    usuario.passw = datos.passw
    usuario.dir_usr = datos.dir_usr
    usuario.tip_usu = datos.tip_usu
    db.commit()
    db.refresh(usuario)
    db.close()
    return usuario


@app.delete("/usuarios/{id_usr}")
def eliminar_usuario(id_usr: int):
    db = SessionLocal()
    usuario = db.query(Usuario).filter(Usuario.id_usr == id_usr).first()
    if not usuario:
        db.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.delete(usuario)
    db.commit()
    db.close()
    return {"mensaje": "Usuario eliminado"}


# ---------- BLOG ----------
@app.post("/blogs/", response_model=BlogOut)
def crear_blog(datos: BlogCreate):
    db = SessionLocal()
    nuevo = Blog(**datos.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    db.close()
    return nuevo


@app.get("/blogs/", response_model=List[BlogOut])
def listar_blogs():
    db = SessionLocal()
    blogs = db.query(Blog).all()
    db.close()
    return blogs


@app.get("/blogs/{id_blog}", response_model=BlogOut)
def obtener_blog(id_blog: int):
    db = SessionLocal()
    blog = db.query(Blog).filter(Blog.id_blog == id_blog).first()
    db.close()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog no encontrado")
    return blog


@app.put("/blogs/{id_blog}", response_model=BlogOut)
def actualizar_blog(id_blog: int, datos: BlogCreate):
    db = SessionLocal()
    blog = db.query(Blog).filter(Blog.id_blog == id_blog).first()
    if not blog:
        db.close()
        raise HTTPException(status_code=404, detail="Blog no encontrado")
    for key, value in datos.dict().items():
        setattr(blog, key, value)
    db.commit()
    db.refresh(blog)
    db.close()
    return blog


@app.delete("/blogs/{id_blog}")
def eliminar_blog(id_blog: int):
    db = SessionLocal()
    blog = db.query(Blog).filter(Blog.id_blog == id_blog).first()
    if not blog:
        db.close()
        raise HTTPException(status_code=404, detail="Blog no encontrado")
    db.delete(blog)
    db.commit()
    db.close()
    return {"mensaje": "Blog eliminado"}


# ---------- CATALOGO ----------
@app.post("/catalogo/", response_model=CatalogoOut)
def crear_producto(datos: CatalogoCreate):
    db = SessionLocal()
    nuevo = Catalogo(**datos.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    db.close()
    return nuevo


@app.get("/catalogo/", response_model=List[CatalogoOut])
def listar_productos():
    db = SessionLocal()
    productos = db.query(Catalogo).all()
    db.close()
    return productos


@app.get("/catalogo/{id_prod}", response_model=CatalogoOut)
def obtener_producto(id_prod: int):
    db = SessionLocal()
    prod = db.query(Catalogo).filter(Catalogo.id_prod == id_prod).first()
    db.close()
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return prod


@app.put("/catalogo/{id_prod}", response_model=CatalogoOut)
def actualizar_producto(id_prod: int, datos: CatalogoCreate):
    db = SessionLocal()
    prod = db.query(Catalogo).filter(Catalogo.id_prod == id_prod).first()
    if not prod:
        db.close()
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    for key, value in datos.dict().items():
        setattr(prod, key, value)
    db.commit()
    db.refresh(prod)
    db.close()
    return prod


@app.delete("/catalogo/{id_prod}")
def eliminar_producto(id_prod: int):
    db = SessionLocal()
    prod = db.query(Catalogo).filter(Catalogo.id_prod == id_prod).first()
    if not prod:
        db.close()
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    db.delete(prod)
    db.commit()
    db.close()
    return {"mensaje": "Producto eliminado"}


# ---------- COMPRA ----------
@app.post("/compras/", response_model=CompraOut)
def crear_compra(datos: CompraCreate):
    db = SessionLocal()
    valores = datos.dict()
    if not valores.get("fecha"):
        valores["fecha"] = datetime.utcnow()
    nuevo = Compra(**valores)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    db.close()
    return nuevo


@app.get("/compras/", response_model=List[CompraOut])
def listar_compras():
    db = SessionLocal()
    compras = db.query(Compra).all()
    db.close()
    return compras


@app.get("/compras/{id}", response_model=CompraOut)
def obtener_compra(id: int):
    db = SessionLocal()
    compra = db.query(Compra).filter(Compra.id == id).first()
    db.close()
    if not compra:
        raise HTTPException(status_code=404, detail="Compra no encontrada")
    return compra


@app.put("/compras/{id}", response_model=CompraOut)
def actualizar_compra(id: int, datos: CompraCreate):
    db = SessionLocal()
    compra = db.query(Compra).filter(Compra.id == id).first()
    if not compra:
        db.close()
        raise HTTPException(status_code=404, detail="Compra no encontrada")
    valores = datos.dict()
    if not valores.get("fecha"):
        valores["fecha"] = compra.fecha
    for key, value in valores.items():
        setattr(compra, key, value)
    db.commit()
    db.refresh(compra)
    db.close()
    return compra


@app.delete("/compras/{id}")
def eliminar_compra(id: int):
    db = SessionLocal()
    compra = db.query(Compra).filter(Compra.id == id).first()
    if not compra:
        db.close()
        raise HTTPException(status_code=404, detail="Compra no encontrada")
    db.delete(compra)
    db.commit()
    db.close()
    return {"mensaje": "Compra eliminada"}


# ---------- COMENTARIOS ----------
@app.post("/comentarios/", response_model=ComentarioOut)
def crear_comentario(datos: ComentarioCreate):
    db = SessionLocal()
    valores = datos.dict()
    if not valores.get("fecha"):
        valores["fecha"] = datetime.utcnow()
    nuevo = Comentario(**valores)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    db.close()
    return nuevo


@app.get("/comentarios/", response_model=List[ComentarioOut])
def listar_comentarios():
    db = SessionLocal()
    comentarios = db.query(Comentario).all()
    db.close()
    return comentarios


@app.get("/comentarios/{id_com}", response_model=ComentarioOut)
def obtener_comentario(id_com: int):
    db = SessionLocal()
    comentario = db.query(Comentario).filter(Comentario.id_com == id_com).first()
    db.close()
    if not comentario:
        raise HTTPException(status_code=404, detail="Comentario no encontrado")
    return comentario


@app.put("/comentarios/{id_com}", response_model=ComentarioOut)
def actualizar_comentario(id_com: int, datos: ComentarioCreate):
    db = SessionLocal()
    comentario = db.query(Comentario).filter(Comentario.id_com == id_com).first()
    if not comentario:
        db.close()
        raise HTTPException(status_code=404, detail="Comentario no encontrado")
    valores = datos.dict()
    if not valores.get("fecha"):
        valores["fecha"] = comentario.fecha
    for key, value in valores.items():
        setattr(comentario, key, value)
    db.commit()
    db.refresh(comentario)
    db.close()
    return comentario


@app.delete("/comentarios/{id_com}")
def eliminar_comentario(id_com: int):
    db = SessionLocal()
    comentario = db.query(Comentario).filter(Comentario.id_com == id_com).first()
    if not comentario:
        db.close()
        raise HTTPException(status_code=404, detail="Comentario no encontrado")
    db.delete(comentario)
    db.commit()
    db.close()
    return {"mensaje": "Comentario eliminado"}
