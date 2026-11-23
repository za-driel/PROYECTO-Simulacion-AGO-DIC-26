"""M: banco de preguntas y selección aleatoria sin repetición."""
import random

from flask import current_app

from app.db import get_db


def seleccionar_aleatorias(distribucion):
    """Elige preguntas al azar por nivel. distribucion = {nivel_id: cantidad}.

    - Estratificado: cada nivel se sortea por separado, así que todos los exámenes cubren los tres niveles.
    - Imágenes: en cada nivel se incluyen entre IMAGENES_POR_NIVEL[0] y IMAGENES_POR_NIVEL[1] preguntas
      con imagen (la cantidad exacta se sortea) y el resto son preguntas de texto.
    - Sin repetición: dentro de un nivel ORDER BY RAND() no duplica filas y los niveles no se solapan.
    - Bloques: la lista sale ordenada por nivel (Básico -> Intermedio -> Avanzado) y al azar dentro de cada nivel.
    """
    minimo, maximo = current_app.config["IMAGENES_POR_NIVEL"]
    ids = []
    with get_db().cursor() as cur:
        for nivel_id, cantidad in sorted(distribucion.items()):
            cur.execute(
                "SELECT COUNT(*) AS n FROM preguntas WHERE nivel_id = %s AND imagen_url IS NOT NULL",
                (nivel_id,),
            )
            tope = min(maximo, cantidad, cur.fetchone()["n"])
            con_imagen = random.randint(min(minimo, tope), tope)
            cur.execute(
                "SELECT pregunta_id FROM preguntas WHERE nivel_id = %s AND imagen_url IS NOT NULL "
                "ORDER BY RAND() LIMIT %s",
                (nivel_id, con_imagen),
            )
            bloque = [f["pregunta_id"] for f in cur.fetchall()]
            cur.execute(
                "SELECT pregunta_id FROM preguntas WHERE nivel_id = %s AND imagen_url IS NULL "
                "ORDER BY RAND() LIMIT %s",
                (nivel_id, cantidad - con_imagen),
            )
            bloque += [f["pregunta_id"] for f in cur.fetchall()]
            if len(bloque) < cantidad:
                raise ValueError(f"El nivel {nivel_id} no tiene {cantidad} preguntas disponibles")
            random.shuffle(bloque)           # mezcla solo dentro del bloque del nivel
            ids.extend(bloque)
    if len(set(ids)) != len(ids):
        raise RuntimeError("Selección con preguntas repetidas")
    return ids


def obtener_con_opciones(pregunta_id, semilla):
    """Pregunta con sus 4 opciones en orden aleatorio.

    La semilla (id del detalle) hace que el orden sea estable si el alumno recarga la página.
    Cada opción conserva su letra original (a-d); esa letra es la que se guarda como respuesta.
    """
    with get_db().cursor() as cur:
        cur.execute(
            "SELECT p.pregunta_id, p.nivel_id, n.nombre_nivel, p.texto_pregunta, p.imagen_url "
            "FROM preguntas p JOIN niveles n ON n.nivel_id = p.nivel_id WHERE p.pregunta_id = %s",
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
