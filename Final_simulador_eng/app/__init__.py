"""Fábrica de la aplicación Flask (patrón MVC: models / views / controllers)."""
import os

from dotenv import load_dotenv
from flask import Flask, render_template

from config import Config

load_dotenv()


def create_app(config_object=Config):
    app = Flask(
        __name__,
        template_folder="views/templates",   # V: vistas
        static_folder="static",
    )
    app.config.from_object(config_object)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "cambia-esta-clave-antes-de-entregar")
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    from app import db, security
    db.init_app(app)
    security.init_app(app)

    # C: controladores (blueprints)
    from app.controllers import admin_controller, auth_controller, final_controller, menu_controller, practica_controller
    app.register_blueprint(auth_controller.bp)
    app.register_blueprint(admin_controller.bp)
    app.register_blueprint(menu_controller.bp)
    app.register_blueprint(practica_controller.bp)
    app.register_blueprint(final_controller.bp)

    @app.errorhandler(400)
    @app.errorhandler(404)
    def error_handler(e):
        return render_template("error.html", codigo=e.code), e.code

    return app
