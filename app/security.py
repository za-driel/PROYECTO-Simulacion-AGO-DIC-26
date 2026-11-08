"""Sesión, login obligatorio y protección CSRF para los formularios POST."""
import secrets
from functools import wraps

from flask import abort, redirect, request, session, url_for


def login_required(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("auth.login"))
        return vista(*args, **kwargs)
    return envoltura


def admin_required(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("auth.login"))
        if session.get("rol") != "administrador":
            abort(403)
        return vista(*args, **kwargs)
    return envoltura


def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return session["_csrf"]


def _verificar_csrf():
    if request.method == "POST":
        enviado = request.form.get("_csrf", "")
        esperado = session.get("_csrf", "")
        if not esperado or not secrets.compare_digest(enviado, esperado):
            abort(400)


def init_app(app):
    app.before_request(_verificar_csrf)
    app.jinja_env.globals["csrf_token"] = csrf_token
