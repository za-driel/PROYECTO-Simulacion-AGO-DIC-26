"""C: registro, inicio y cierre de sesión."""
import re

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.models import usuario_model

bp = Blueprint("auth", __name__)

_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@bp.route("/")
def inicio():
    return redirect(url_for("menu.principal" if "usuario_id" in session else "auth.login"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()
        password = request.form.get("password", "")
        usuario = usuario_model.autenticar(correo, password)
        if usuario:
            session.clear()
            session["usuario_id"] = usuario["usuario_id"]
            session["nombre"] = usuario["nombre"]
            session["rol"] = usuario.get("rol", "alumno")
            if usuario.get("rol", "alumno") == "administrador":
                return redirect(url_for("admin.dashboard"))
            return redirect(url_for("menu.principal"))
        flash("Correo o contraseña incorrectos.", "error")
        return render_template("login.html", correo=correo)
    return render_template("login.html", correo="")


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
