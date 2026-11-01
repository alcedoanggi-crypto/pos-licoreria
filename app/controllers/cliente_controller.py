from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.extensions import db
from app.models import ClienteFrecuente

cliente_bp = Blueprint("clientes", __name__)


@cliente_bp.route("/")
@login_required
def listar():
    busqueda = request.args.get("q", "").strip()
    query = ClienteFrecuente.query
    if busqueda:
        like = f"%{busqueda}%"
        query = query.filter((ClienteFrecuente.nombre_completo.ilike(like)) | (ClienteFrecuente.telefono.ilike(like)))
    clientes = query.order_by(ClienteFrecuente.nombre_completo).all()
    return render_template("clientes/list.html", clientes=clientes, busqueda=busqueda)


@cliente_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    if request.method == "POST":
        cliente = ClienteFrecuente(
            nombre_completo=request.form["nombre_completo"].strip(),
            telefono=request.form["telefono"].strip(),
            email=request.form.get("email", "").strip(),
        )
        db.session.add(cliente)
        db.session.commit()
        flash(f"Cliente {cliente.nombre_completo} registrado.", "success")
        return redirect(url_for("clientes.listar"))

    return render_template("clientes/form.html", cliente=None)


@cliente_bp.route("/<int:cliente_id>")
@login_required
def detalle(cliente_id):
    cliente = ClienteFrecuente.query.get_or_404(cliente_id)
    return render_template("clientes/detalle.html", cliente=cliente)


@cliente_bp.route("/<int:cliente_id>/editar", methods=["GET", "POST"])
@login_required
def editar(cliente_id):
    cliente = ClienteFrecuente.query.get_or_404(cliente_id)

    if request.method == "POST":
        cliente.nombre_completo = request.form["nombre_completo"].strip()
        cliente.telefono = request.form["telefono"].strip()
        cliente.email = request.form.get("email", "").strip()
        cliente.activo = bool(request.form.get("activo"))
        db.session.commit()
        flash(f"Cliente {cliente.nombre_completo} actualizado.", "success")
        return redirect(url_for("clientes.listar"))

    return render_template("clientes/form.html", cliente=cliente)
