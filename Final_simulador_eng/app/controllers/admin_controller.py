"""C: administración de cuentas y roles."""
import re

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.models import dashboard_model, usuario_model
from app.security import admin_required

bp = Blueprint("admin", __name__, url_prefix="/administracion")
_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@bp.route("/dashboard")
@admin_required
def dashboard():
    return render_template("dashboard.html", resumen=dashboard_model.obtener_resumen())


@bp.route("", methods=["GET", "POST"])
@admin_required
def panel():
    errores = []
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        correo = request.form.get("correo", "").strip().lower()
        password = request.form.get("password", "")
        rol = request.form.get("rol", "alumno")

        if not 2 <= len(nombre) <= 100:
            errores.append("El nombre debe tener entre 2 y 100 caracteres.")
        if not _CORREO.match(correo) or len(correo) > 150:
            errores.append("Escribe un correo válido.")
        if len(password) < 8:
            errores.append("La contraseña debe tener al menos 8 caracteres.")
        if rol not in ("alumno", "administrador"):
            errores.append("Selecciona un rol válido.")

        if not errores:
            usuario_id = usuario_model.crear(nombre, correo, password, rol)
            if usuario_id is None:
                errores.append("Ese correo ya tiene una cuenta.")
            else:
                flash(f"Cuenta creada para {correo} con rol {rol}.", "exito")
                return redirect(url_for("admin.panel"))

    for error in errores:
        flash(error, "error")
    return render_template("admin.html", usuarios=usuario_model.listar())
