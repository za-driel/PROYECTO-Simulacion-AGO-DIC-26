"""M: acceso a datos de usuarios."""
import pymysql
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_db


def crear(nombre, correo, password, rol="alumno"):
    """Devuelve el id del usuario nuevo, o None si el correo ya existe."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO usuarios (nombre, correo, password_hash, rol) VALUES (%s, %s, %s, %s)",
                (nombre, correo, generate_password_hash(password), rol),
            )
            usuario_id = cur.lastrowid
        db.commit()
        return usuario_id
    except pymysql.err.IntegrityError:
        db.rollback()
        return None


def listar():
    with get_db().cursor() as cur:
        cur.execute("SELECT usuario_id, nombre, correo, rol, fecha_registro FROM usuarios ORDER BY fecha_registro DESC")
        return cur.fetchall()


def obtener_por_correo(correo):
    with get_db().cursor() as cur:
        cur.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
        return cur.fetchone()


def autenticar(correo, password):
    """Devuelve el usuario si las credenciales son válidas, si no None."""
    usuario = obtener_por_correo(correo)
    if usuario and check_password_hash(usuario["password_hash"], password):
        return usuario
    return None
