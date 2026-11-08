"""C: examen de práctica (20 preguntas, 1 minuto por pregunta)."""
from flask import (Blueprint, abort, current_app, flash, redirect, render_template,
                   request, session, url_for)

from app.models import practica_model, pregunta_model
from app.security import login_required

bp = Blueprint("practica", __name__, url_prefix="/practica")


def _intento_del_usuario(intento_id):
    """Carga el intento y verifica que pertenezca al usuario en sesión."""
    intento = practica_model.obtener_intento(intento_id)
    if intento is None or intento["usuario_id"] != session["usuario_id"]:
        abort(404)
    return intento


@bp.route("/iniciar", methods=["POST"])
@login_required
def iniciar():
    if session.get("rol") == "administrador":
        abort(403)
    usuario_id = session["usuario_id"]

    en_curso = practica_model.obtener_en_curso(usuario_id)       # reanuda si ya hay uno abierto
    if en_curso:
        return redirect(url_for("practica.pregunta", intento_id=en_curso["intento_practica_id"]))

    cfg = current_app.config
    if practica_model.contar_intentos(usuario_id) >= cfg["PRACTICA_MAX_INTENTOS"]:
        flash("Ya usaste tus %d intentos de práctica." % cfg["PRACTICA_MAX_INTENTOS"], "error")
        return redirect(url_for("menu.principal"))

    ids = pregunta_model.seleccionar_aleatorias(cfg["PRACTICA_PREGUNTAS_POR_NIVEL"])
    intento_id = practica_model.crear_intento(usuario_id, ids)
    if intento_id is None:
        flash("No se pudo iniciar el examen. Inténtalo de nuevo.", "error")
        return redirect(url_for("menu.principal"))
    return redirect(url_for("practica.pregunta", intento_id=intento_id))


@bp.route("/<int:intento_id>")
@login_required
def pregunta(intento_id):
    intento = _intento_del_usuario(intento_id)
    if intento["fecha_fin"] is not None:
        return redirect(url_for("practica.resultado", intento_id=intento_id))

    actual = practica_model.obtener_pregunta_actual(intento_id)
    if actual is None:                                  # no quedan preguntas: cerrar y calificar
        practica_model.finalizar(intento_id)
        return redirect(url_for("practica.resultado", intento_id=intento_id))

    cfg = current_app.config
    contenido = pregunta_model.obtener_con_opciones(actual["pregunta_id"], semilla=actual["detalle_id"])
    return render_template(
        "pregunta.html",
        intento_id=intento_id,
        detalle_id=actual["detalle_id"],
        numero=actual["orden"],
        total=sum(cfg["PRACTICA_PREGUNTAS_POR_NIVEL"].values()),
        pregunta=contenido,
        titulo="Examen de práctica",
        url_responder=url_for("practica.responder", intento_id=intento_id),
        segundos_total=cfg["SEGUNDOS_POR_PREGUNTA"],
        segundos_restantes=max(0.0, cfg["SEGUNDOS_POR_PREGUNTA"] - actual["transcurrido"]),
    )


@bp.route("/<int:intento_id>/responder", methods=["POST"])
@login_required
def responder(intento_id):
    intento = _intento_del_usuario(intento_id)
    if intento["fecha_fin"] is not None:
        return redirect(url_for("practica.resultado", intento_id=intento_id))

    cfg = current_app.config
    limite = cfg["SEGUNDOS_POR_PREGUNTA"]
    actual = practica_model.siguiente_pendiente(intento_id)

    # Solo se acepta respuesta para la pregunta vigente (evita reenvíos y saltos de pregunta)
    try:
        detalle_id = int(request.form.get("detalle_id", ""))
    except ValueError:
        detalle_id = None
    if actual is None or actual["transcurrido"] is None or actual["detalle_id"] != detalle_id:
        return redirect(url_for("practica.pregunta", intento_id=intento_id))

    transcurrido = actual["transcurrido"]
    letra = request.form.get("opcion", "")
    letra = letra if letra in ("a", "b", "c", "d") else None
    tiempo_agotado = request.form.get("tiempo_agotado") == "1" and transcurrido >= limite - 2

    if transcurrido > limite + cfg["SEGUNDOS_GRACIA"]:
        practica_model.expirar(detalle_id)               # llegó fuera de tiempo: errónea
    elif letra is not None:
        practica_model.registrar_respuesta(detalle_id, letra, transcurrido)
    elif tiempo_agotado:
        practica_model.expirar(detalle_id)               # se acabó el minuto sin elegir nada
    else:
        flash("Elige una opción antes de responder.", "error")   # el reloj sigue corriendo

    if practica_model.siguiente_pendiente(intento_id) is None:    # era la última pregunta
        practica_model.finalizar(intento_id)
        return redirect(url_for("practica.resultado", intento_id=intento_id))
    return redirect(url_for("practica.pregunta", intento_id=intento_id))


@bp.route("/<int:intento_id>/resultado")
@login_required
def resultado(intento_id):
    intento = _intento_del_usuario(intento_id)
    if intento["fecha_fin"] is None:
        return redirect(url_for("practica.pregunta", intento_id=intento_id))
    cfg = current_app.config
    return render_template(
        "resultado.html",
        r=practica_model.obtener_resultado(intento_id),
        titulo="Examen de práctica",
        intentos_max=cfg["PRACTICA_MAX_INTENTOS"],
        minimo=cfg["PORCENTAJE_APROBATORIO"],
    )
