"""M: intentos del simulador de práctica (intentos_practica / detalle_intentos_practica)."""
import pymysql
from flask import current_app

from app.db import get_db


# ---------------------------------------------------------------- consultas
def contar_intentos(usuario_id):
    with get_db().cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM intentos_practica WHERE usuario_id = %s", (usuario_id,))
        return cur.fetchone()["n"]


def obtener_en_curso(usuario_id):
    with get_db().cursor() as cur:
        cur.execute(
            "SELECT * FROM intentos_practica WHERE usuario_id = %s AND fecha_fin IS NULL "
            "ORDER BY numero_intento DESC LIMIT 1",
            (usuario_id,),
        )
        return cur.fetchone()


def obtener_intento(intento_id):
    with get_db().cursor() as cur:
        cur.execute("SELECT * FROM intentos_practica WHERE intento_practica_id = %s", (intento_id,))
        return cur.fetchone()


# ---------------------------------------------------------------- creación
def crear_intento(usuario_id, ids_preguntas):
    """Crea el intento y sus N filas de detalle (respuesta vacía). None si ya agotó los intentos."""
    db = get_db()
    maximo = current_app.config["PRACTICA_MAX_INTENTOS"]
    numero = contar_intentos(usuario_id) + 1
    if numero > maximo:
        return None
    try:
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO intentos_practica (usuario_id, numero_intento) VALUES (%s, %s)",
                (usuario_id, numero),
            )
            intento_id = cur.lastrowid
            cur.executemany(
                "INSERT INTO detalle_intentos_practica (intento_practica_id, pregunta_id, orden) "
                "VALUES (%s, %s, %s)",
                [(intento_id, pid, orden) for orden, pid in enumerate(ids_preguntas, start=1)],
            )
        db.commit()
        return intento_id
    except pymysql.err.IntegrityError:      # doble clic / petición simultánea
        db.rollback()
        return None


# ---------------------------------------------------------------- pregunta actual
def siguiente_pendiente(intento_id):
    """Primera pregunta sin resolver (es_correcta NULL), con los segundos transcurridos desde que se mostró."""
    with get_db().cursor() as cur:
        cur.execute(
            "SELECT detalle_practica_id AS detalle_id, pregunta_id, orden, fecha_presentada, "
            "TIMESTAMPDIFF(MICROSECOND, fecha_presentada, NOW(3)) AS micros "
            "FROM detalle_intentos_practica "
            "WHERE intento_practica_id = %s AND es_correcta IS NULL "
            "ORDER BY orden LIMIT 1",
            (intento_id,),
        )
        fila = cur.fetchone()
    if fila is None:
        return None
    fila["transcurrido"] = None if fila["micros"] is None else fila["micros"] / 1_000_000
    return fila


def _marcar_presentada(detalle_id):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "UPDATE detalle_intentos_practica SET fecha_presentada = NOW(3) "
            "WHERE detalle_practica_id = %s AND fecha_presentada IS NULL",
            (detalle_id,),
        )
    db.commit()


def expirar(detalle_id):
    """Tiempo agotado: respuesta vacía, incorrecta y 60 s. Solo afecta a preguntas aún sin resolver."""
    db = get_db()
    limite = current_app.config["SEGUNDOS_POR_PREGUNTA"]
    with db.cursor() as cur:
        cur.execute(
            "UPDATE detalle_intentos_practica SET respuesta_dada = NULL, es_correcta = 0, "
            "tiempo_respuesta = %s WHERE detalle_practica_id = %s AND es_correcta IS NULL",
            (limite, detalle_id),
        )
        afectadas = cur.rowcount
    db.commit()
    return afectadas == 1


def obtener_pregunta_actual(intento_id):
    """Devuelve la pregunta que debe responder el alumno ahora, o None si ya terminó.

    - Si la pregunta aún no se había mostrado, inicia su minuto.
    - Si el alumno dejó vencer el minuto (cerró la pestaña, se fue), la marca como errónea
      y avanza a la siguiente, repitiendo hasta encontrar una vigente.
    """
    cfg = current_app.config
    limite_total = cfg["SEGUNDOS_POR_PREGUNTA"] + cfg["SEGUNDOS_GRACIA"]
    while True:
        fila = siguiente_pendiente(intento_id)
        if fila is None:
            return None
        if fila["transcurrido"] is None:
            _marcar_presentada(fila["detalle_id"])
            fila["transcurrido"] = 0.0
            return fila
        if fila["transcurrido"] > limite_total:
            expirar(fila["detalle_id"])
            continue
        return fila


# ---------------------------------------------------------------- respuesta
def registrar_respuesta(detalle_id, letra, transcurrido):
    """Guarda la respuesta y calcula es_correcta contra la tabla opciones. False si ya estaba resuelta."""
    db = get_db()
    limite = current_app.config["SEGUNDOS_POR_PREGUNTA"]
    tiempo = max(0, min(limite, int(round(transcurrido))))
    with db.cursor() as cur:
        cur.execute(
            "UPDATE detalle_intentos_practica SET respuesta_dada = %s, tiempo_respuesta = %s, "
            "es_correcta = COALESCE((SELECT o.es_correcta FROM opciones o "
            "WHERE o.pregunta_id = detalle_intentos_practica.pregunta_id AND o.letra = %s), 0) "
            "WHERE detalle_practica_id = %s AND es_correcta IS NULL",
            (letra, tiempo, letra, detalle_id),
        )
        afectadas = cur.rowcount
    db.commit()
    return afectadas == 1


# ---------------------------------------------------------------- cierre y resultado
def _desglose_por_nivel(intento_id):
    with get_db().cursor() as cur:
        cur.execute(
            "SELECT n.nivel_id, n.nombre_nivel, COUNT(*) AS total, "
            "SUM(CASE WHEN d.es_correcta = 1 THEN 1 ELSE 0 END) AS correctas "
            "FROM detalle_intentos_practica d "
            "JOIN preguntas p ON p.pregunta_id = d.pregunta_id "
            "JOIN niveles n ON n.nivel_id = p.nivel_id "
            "WHERE d.intento_practica_id = %s "
            "GROUP BY n.nivel_id, n.nombre_nivel, n.orden ORDER BY n.orden",
            (intento_id,),
        )
        filas = cur.fetchall()
    for f in filas:
        f["correctas"] = int(f["correctas"])
        f["porcentaje"] = round(f["correctas"] * 100 / f["total"], 1)
    return filas


def finalizar(intento_id):
    """Calcula calificación, aprobado y nivel alcanzado, y cierra el intento.

    Calificación: cada reactivo vale PRACTICA_PUNTOS_POR_PREGUNTA (20 x 5 = 100).
    Nivel alcanzado: el más alto en el que el alumno logra >= 70 % de los reactivos de ese nivel,
    exigiendo también haberlo logrado en todos los niveles inferiores (Básico -> Intermedio -> Avanzado).
    """
    cfg = current_app.config
    minimo = cfg["PORCENTAJE_APROBATORIO"]
    desglose = _desglose_por_nivel(intento_id)
    puntos = sum(f["correctas"] for f in desglose) * cfg["PRACTICA_PUNTOS_POR_PREGUNTA"]
    maximo = sum(f["total"] for f in desglose) * cfg["PRACTICA_PUNTOS_POR_PREGUNTA"]
    calificacion = round(puntos * 100 / maximo, 2)
    aprobado = 1 if calificacion >= minimo else 0

    nivel_resultado = None
    for f in desglose:                       # ya viene ordenado Básico -> Avanzado
        if f["porcentaje"] >= minimo:
            nivel_resultado = f["nivel_id"]
        else:
            break

    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "UPDATE intentos_practica SET fecha_fin = NOW(), calificacion = %s, aprobado = %s, "
            "nivel_resultado_id = %s WHERE intento_practica_id = %s AND fecha_fin IS NULL",
            (calificacion, aprobado, nivel_resultado, intento_id),
        )
    db.commit()


def obtener_resultado(intento_id):
    with get_db().cursor() as cur:
        cur.execute(
            "SELECT i.*, n.nombre_nivel AS nivel_resultado "
            "FROM intentos_practica i LEFT JOIN niveles n ON n.nivel_id = i.nivel_resultado_id "
            "WHERE i.intento_practica_id = %s",
            (intento_id,),
        )
        intento = cur.fetchone()
        cur.execute(
            "SELECT SUM(CASE WHEN es_correcta = 1 THEN 1 ELSE 0 END) AS correctas, "
            "SUM(CASE WHEN es_correcta = 0 AND respuesta_dada IS NOT NULL THEN 1 ELSE 0 END) AS incorrectas, "
            "SUM(CASE WHEN respuesta_dada IS NULL THEN 1 ELSE 0 END) AS sin_responder "
            "FROM detalle_intentos_practica WHERE intento_practica_id = %s",
            (intento_id,),
        )
        conteo = cur.fetchone()
    intento["correctas"] = int(conteo["correctas"])
    intento["incorrectas"] = int(conteo["incorrectas"])
    intento["sin_responder"] = int(conteo["sin_responder"])
    intento["por_nivel"] = _desglose_por_nivel(intento_id)
    return intento
