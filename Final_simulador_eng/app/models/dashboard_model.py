"""M: indicadores generales para el dashboard administrativo."""
from app.db import get_db


def _numero(valor):
    return round(float(valor), 2) if valor is not None else 0


def obtener_resumen():
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS total FROM usuarios")
        usuarios = cur.fetchone()["total"]
        cur.execute("SELECT COUNT(*) AS total FROM usuarios WHERE rol = 'alumno'")
        alumnos = cur.fetchone()["total"]
        cur.execute("SELECT COUNT(*) AS total FROM usuarios WHERE rol = 'administrador'")
        administradores = cur.fetchone()["total"]
        cur.execute("SELECT COUNT(*) AS total FROM intentos_practica WHERE fecha_fin IS NOT NULL")
        practicas = cur.fetchone()["total"]
        cur.execute("SELECT COUNT(*) AS total FROM intentos_finales WHERE fecha_fin IS NOT NULL")
        finales = cur.fetchone()["total"]

        cur.execute("SELECT AVG(calificacion) AS promedio, SUM(aprobado = 1) AS aprobados FROM intentos_practica WHERE fecha_fin IS NOT NULL")
        practica = cur.fetchone()
        cur.execute("SELECT AVG(calificacion) AS promedio, SUM(aprobado = 1) AS aprobados FROM intentos_finales WHERE fecha_fin IS NOT NULL")
        final = cur.fetchone()

        cur.execute("SELECT numero_intento, AVG(calificacion) AS promedio FROM intentos_practica WHERE fecha_fin IS NOT NULL GROUP BY numero_intento ORDER BY numero_intento")
        evolucion_practica = cur.fetchall()
        cur.execute("SELECT numero_intento, AVG(calificacion) AS promedio FROM intentos_finales WHERE fecha_fin IS NOT NULL GROUP BY numero_intento ORDER BY numero_intento")
        evolucion_final = cur.fetchall()

        cur.execute("SELECT COALESCE(n.nombre_nivel, 'Sin nivel') AS nivel, COUNT(*) AS cantidad FROM intentos_practica i LEFT JOIN niveles n ON n.nivel_id = i.nivel_resultado_id WHERE i.fecha_fin IS NOT NULL GROUP BY n.nombre_nivel ORDER BY cantidad DESC")
        niveles_practica = cur.fetchall()
        cur.execute("SELECT COALESCE(n.nombre_nivel, 'Sin nivel') AS nivel, COUNT(*) AS cantidad FROM intentos_finales i LEFT JOIN niveles n ON n.nivel_id = i.nivel_resultado_id WHERE i.fecha_fin IS NOT NULL GROUP BY n.nombre_nivel ORDER BY cantidad DESC")
        niveles_final = cur.fetchall()

        cur.execute("""
            SELECT p.usuario_id,
                   (SELECT MAX(p2.calificacion) FROM intentos_practica p2 WHERE p2.usuario_id = p.usuario_id AND p2.fecha_fin IS NOT NULL) AS mejor_practica,
                   (SELECT MAX(f.calificacion) FROM intentos_finales f WHERE f.usuario_id = p.usuario_id AND f.fecha_fin IS NOT NULL) AS mejor_final
            FROM usuarios p
            WHERE EXISTS (SELECT 1 FROM intentos_practica pp WHERE pp.usuario_id = p.usuario_id AND pp.fecha_fin IS NOT NULL)
              AND EXISTS (SELECT 1 FROM intentos_finales ff WHERE ff.usuario_id = p.usuario_id AND ff.fecha_fin IS NOT NULL)
        """)
        comparacion = cur.fetchall()

    mejoras = [
        _numero(float(fila["mejor_final"] or 0) - float(fila["mejor_practica"] or 0))
        for fila in comparacion
        if fila["mejor_final"] is not None and fila["mejor_practica"] is not None
    ]

    return {
        "usuarios": usuarios,
        "alumnos": alumnos,
        "administradores": administradores,
        "practicas": practicas,
        "finales": finales,
        "promedio_practica": _numero(practica["promedio"]),
        "promedio_final": _numero(final["promedio"]),
        "aprobados_practica": practica["aprobados"] or 0,
        "aprobados_final": final["aprobados"] or 0,
        "evolucion_practica": [[fila["numero_intento"], _numero(fila["promedio"])] for fila in evolucion_practica],
        "evolucion_final": [[fila["numero_intento"], _numero(fila["promedio"])] for fila in evolucion_final],
        "niveles_practica": [[fila["nivel"], fila["cantidad"]] for fila in niveles_practica],
        "niveles_final": [[fila["nivel"], fila["cantidad"]] for fila in niveles_final],
        "mejora_promedio": _numero(sum(mejoras) / len(mejoras)) if mejoras else 0,
        "comparados": len(mejoras),
    }
