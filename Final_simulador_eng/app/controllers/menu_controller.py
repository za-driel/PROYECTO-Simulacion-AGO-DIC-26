"""C: menú principal."""
from flask import Blueprint, current_app, redirect, render_template, session, url_for

from app.models import final_model, practica_model
from app.security import login_required

bp = Blueprint("menu", __name__)


@bp.route("/menu")
@login_required
def principal():
    if session.get("rol") == "administrador":
        return redirect(url_for("admin.dashboard"))
    usuario_id = session["usuario_id"]
    cfg = current_app.config
    practica = {
        "titulo": "Examen de práctica",
        "descripcion": "Entrena con preguntas de inglés básico, intermedio y avanzado. Sirve para estudiar y no define tu nivel oficial.",
        "total": sum(cfg["PRACTICA_PREGUNTAS_POR_NIVEL"].values()),
        "usados": practica_model.contar_intentos(usuario_id),
        "maximo": cfg["PRACTICA_MAX_INTENTOS"],
        "en_curso": practica_model.obtener_en_curso(usuario_id),
        "iniciar": "practica.iniciar",
        "boton": "Presentar examen de práctica",
    }
    final = {
        "titulo": "Examen final",
        "descripcion": "Es el examen que te ubica en tu nivel de inglés. Tienes pocos intentos, así que úsalos cuando ya te sientas listo.",
        "total": sum(cfg["FINAL_PREGUNTAS_POR_NIVEL"].values()),
        "usados": final_model.contar_intentos(usuario_id),
        "maximo": cfg["FINAL_MAX_INTENTOS"],
        "en_curso": final_model.obtener_en_curso(usuario_id),
        "iniciar": "final.iniciar",
        "boton": "Presentar examen final",
    }
    return render_template(
        "menu.html",
        examenes=[practica, final],
        segundos=cfg["SEGUNDOS_POR_PREGUNTA"],
        minimo=cfg["PORCENTAJE_APROBATORIO"],
    )
