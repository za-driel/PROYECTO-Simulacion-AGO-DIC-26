"""Lógica compartida por el examen de práctica y el examen final.

Las preguntas se presentan en bloques por nivel (Básico -> Intermedio -> Avanzado). Al entrar a un
bloque nuevo se muestra primero una pantalla de aviso; el minuto de la primera pregunta del bloque
empieza hasta que el alumno presiona "Continuar".
"""
from flask import current_app, redirect, render_template, session, url_for

from app.models import pregunta_model


def _clave(tipo, intento_id, nivel_id):
    return f"{tipo}:{intento_id}:{nivel_id}"


def aviso_visto(tipo, intento_id, nivel_id):
    return _clave(tipo, intento_id, nivel_id) in session.get("avisos_nivel", [])


def marcar_aviso(tipo, intento_id, nivel_id):
    vistos = list(session.get("avisos_nivel", []))
    clave = _clave(tipo, intento_id, nivel_id)
    if clave not in vistos:
        vistos.append(clave)
        session["avisos_nivel"] = vistos[-30:]        # la sesión vive en una cookie: no la dejamos crecer


def continuar_bloque(modelo, tipo, intento_id):
    """El alumno vio el aviso del nivel que le toca ahora; se registra en su sesión."""
    actual = modelo.siguiente_pendiente(intento_id)
    if actual is not None:
        marcar_aviso(tipo, intento_id, actual["nivel_id"])


def mostrar_pregunta(modelo, tipo, intento_id, titulo, total):
    """Devuelve la pantalla que corresponde: resultado, aviso de nivel o la pregunta vigente."""
    cfg = current_app.config
    actual = modelo.obtener_pregunta_actual(intento_id, iniciar_tiempo=False)
    if actual is None:                                  # no quedan preguntas: cerrar y calificar
        modelo.finalizar(intento_id)
        return redirect(url_for(f"{tipo}.resultado", intento_id=intento_id))

    contenido = pregunta_model.obtener_con_opciones(actual["pregunta_id"], semilla=actual["detalle_id"])
    bloque = modelo.info_bloque(intento_id, actual["nivel_id"])

    if actual["transcurrido"] is None:                  # la pregunta aún no se muestra
        abre_bloque = bloque["primer_orden"] == actual["orden"]
        if abre_bloque and not aviso_visto(tipo, intento_id, actual["nivel_id"]):
            return render_template(
                "aviso_nivel.html",
                titulo=titulo,
                nivel=contenido["nombre_nivel"],
                nivel_id=actual["nivel_id"],
                es_primero=actual["orden"] == 1,
                preguntas_bloque=bloque["total"],
                segundos=cfg["SEGUNDOS_POR_PREGUNTA"],
                url_continuar=url_for(f"{tipo}.continuar", intento_id=intento_id),
            )
        actual = modelo.obtener_pregunta_actual(intento_id)     # ahora sí empieza su minuto

    return render_template(
        "pregunta.html",
        intento_id=intento_id,
        detalle_id=actual["detalle_id"],
        numero=actual["orden"],
        total=total,
        pregunta=contenido,
        nivel=contenido["nombre_nivel"],
        nivel_id=actual["nivel_id"],
        posicion_bloque=actual["orden"] - bloque["primer_orden"] + 1,
        total_bloque=bloque["total"],
        titulo=titulo,
        url_responder=url_for(f"{tipo}.responder", intento_id=intento_id),
        segundos_total=cfg["SEGUNDOS_POR_PREGUNTA"],
        segundos_restantes=max(0.0, cfg["SEGUNDOS_POR_PREGUNTA"] - actual["transcurrido"]),
    )
