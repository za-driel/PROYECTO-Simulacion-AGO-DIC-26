"""M: banco de preguntas y selección aleatoria sin repetición."""
import random

from app.db import get_db


def seleccionar_aleatorias(distribucion):
    """Elige preguntas al azar por nivel. distribucion = {nivel_id: cantidad}.

    Cada nivel se consulta por separado con ORDER BY RAND(): dentro de un nivel no hay
    duplicados y los niveles no se solapan, así que el resultado no repite preguntas.
    Se valida de todos modos y se devuelve la lista ya mezclada.
    """
    ids = []
    with get_db().cursor() as cur:
        for nivel_id, cantidad in distribucion.items():
            cur.execute(
                "SELECT pregunta_id FROM preguntas WHERE nivel_id = %s ORDER BY RAND() LIMIT %s",
                (nivel_id, cantidad),
            )
            filas = cur.fetchall()
            if len(filas) < cantidad:
                raise ValueError(f"El nivel {nivel_id} no tiene {cantidad} preguntas disponibles")
            ids.extend(f["pregunta_id"] for f in filas)
    if len(set(ids)) != len(ids):
        raise RuntimeError("Selección con preguntas repetidas")
    random.shuffle(ids)
    return ids


def obtener_con_opciones(pregunta_id, semilla):
    """Pregunta con sus 4 opciones en orden aleatorio.

    La semilla (id del detalle) hace que el orden sea estable si el alumno recarga la página.
    Cada opción conserva su letra original (a-d); esa letra es la que se guarda como respuesta.
    """
    with get_db().cursor() as cur:
        cur.execute(
            "SELECT pregunta_id, nivel_id, texto_pregunta, imagen_url FROM preguntas WHERE pregunta_id = %s",
            (pregunta_id,),
        )
        pregunta = cur.fetchone()
        cur.execute(
            "SELECT letra, texto FROM opciones WHERE pregunta_id = %s ORDER BY letra",
            (pregunta_id,),
        )
        opciones = cur.fetchall()
    random.Random(semilla).shuffle(opciones)
    pregunta["opciones"] = opciones
    return pregunta
