from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.models import Empleado

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        empleado = Empleado.query.filter_by(email=email).first()
        if empleado and empleado.activo and empleado.check_password(password):
            login_user(empleado, remember=bool(request.form.get("recordar")))
            siguiente = request.args.get("next")
            if empleado.tiene_rol("cajero"):
                return redirect(siguiente or url_for("pos.pantalla"))
            return redirect(siguiente or url_for("dashboard.index"))

        flash("Correo o contraseña incorrectos.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("auth.login"))
