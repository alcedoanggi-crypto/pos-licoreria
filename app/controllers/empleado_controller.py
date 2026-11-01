from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.extensions import db
from app.models import Empleado
from app.models.empleado import RolEmpleado
from app.utils.decorators import roles_requeridos

empleado_bp = Blueprint("empleados", __name__)


@empleado_bp.route("/")
@login_required
@roles_requeridos("administrador")
def listar():
    empleados = Empleado.query.order_by(Empleado.nombre_completo).all()
    return render_template("empleados/list.html", empleados=empleados)


@empleado_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@roles_requeridos("administrador")
def nuevo():
    if request.method == "POST":
        empleado = Empleado(
            nombre_completo=request.form["nombre_completo"].strip(),
            email=request.form["email"].strip().lower(),
            pin=request.form.get("pin", "").strip() or None,
            rol=RolEmpleado(request.form.get("rol", "cajero")),
        )
        empleado.set_password(request.form["password"])
        db.session.add(empleado)
        db.session.commit()
        flash(f"Empleado {empleado.nombre_completo} creado.", "success")
        return redirect(url_for("empleados.listar"))

    return render_template("empleados/form.html", empleado=None, roles=RolEmpleado)


@empleado_bp.route("/<int:empleado_id>/editar", methods=["GET", "POST"])
@login_required
@roles_requeridos("administrador")
def editar(empleado_id):
    empleado = Empleado.query.get_or_404(empleado_id)

    if request.method == "POST":
        empleado.nombre_completo = request.form["nombre_completo"].strip()
        empleado.email = request.form["email"].strip().lower()
        empleado.pin = request.form.get("pin", "").strip() or None
        empleado.rol = RolEmpleado(request.form.get("rol", "cajero"))
        empleado.activo = bool(request.form.get("activo"))
        nueva_password = request.form.get("password", "").strip()
        if nueva_password:
            empleado.set_password(nueva_password)
        db.session.commit()
        flash(f"Empleado {empleado.nombre_completo} actualizado.", "success")
        return redirect(url_for("empleados.listar"))

    return render_template("empleados/form.html", empleado=empleado, roles=RolEmpleado)
