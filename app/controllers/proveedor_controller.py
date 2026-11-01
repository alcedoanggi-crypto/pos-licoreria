import random
import string
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import DetalleOrdenCompra, OrdenCompra, Producto, Proveedor
from app.models.orden_compra import EstadoOrdenCompra
from app.utils.decorators import roles_requeridos

proveedor_bp = Blueprint("proveedores", __name__)


def _generar_numero_orden() -> str:
    sufijo = "".join(random.choices(string.digits, k=6))
    return f"OC-{datetime.utcnow():%Y%m}-{sufijo}"


@proveedor_bp.route("/")
@login_required
def listar():
    proveedores = Proveedor.query.order_by(Proveedor.razon_social).all()
    return render_template("proveedores/list.html", proveedores=proveedores)


@proveedor_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@roles_requeridos("administrador")
def nuevo():
    if request.method == "POST":
        proveedor = Proveedor(
            razon_social=request.form["razon_social"].strip(),
            contacto_nombre=request.form.get("contacto_nombre", "").strip(),
            telefono=request.form.get("telefono", "").strip(),
            email=request.form.get("email", "").strip(),
            direccion=request.form.get("direccion", "").strip(),
        )
        db.session.add(proveedor)
        db.session.commit()
        flash(f"Proveedor {proveedor.razon_social} creado.", "success")
        return redirect(url_for("proveedores.listar"))

    return render_template("proveedores/form.html", proveedor=None)


@proveedor_bp.route("/<int:proveedor_id>/editar", methods=["GET", "POST"])
@login_required
@roles_requeridos("administrador")
def editar(proveedor_id):
    proveedor = Proveedor.query.get_or_404(proveedor_id)

    if request.method == "POST":
        proveedor.razon_social = request.form["razon_social"].strip()
        proveedor.contacto_nombre = request.form.get("contacto_nombre", "").strip()
        proveedor.telefono = request.form.get("telefono", "").strip()
        proveedor.email = request.form.get("email", "").strip()
        proveedor.direccion = request.form.get("direccion", "").strip()
        proveedor.activo = bool(request.form.get("activo"))
        db.session.commit()
        flash(f"Proveedor {proveedor.razon_social} actualizado.", "success")
        return redirect(url_for("proveedores.listar"))

    return render_template("proveedores/form.html", proveedor=proveedor)


@proveedor_bp.route("/ordenes-compra")
@login_required
def ordenes_listar():
    ordenes = OrdenCompra.query.order_by(OrdenCompra.fecha_creacion.desc()).all()
    return render_template("proveedores/ordenes_list.html", ordenes=ordenes)


@proveedor_bp.route("/ordenes-compra/nueva", methods=["GET", "POST"])
@login_required
@roles_requeridos("administrador", "supervisor")
def ordenes_nueva():
    proveedores = Proveedor.query.filter_by(activo=True).order_by(Proveedor.razon_social).all()
    productos = Producto.query.filter_by(activo=True).order_by(Producto.nombre).all()

    if request.method == "POST":
        proveedor_id = request.form.get("proveedor_id", type=int)
        productos_ids = request.form.getlist("producto_id[]")
        cantidades = request.form.getlist("cantidad[]")
        costos = request.form.getlist("costo_unitario[]")

        if not proveedor_id or not productos_ids:
            flash("Selecciona un proveedor y al menos un producto.", "danger")
            return render_template("proveedores/orden_form.html", proveedores=proveedores, productos=productos)

        orden = OrdenCompra(numero_orden=_generar_numero_orden(), proveedor_id=proveedor_id, empleado_id=current_user.id)
        db.session.add(orden)
        db.session.flush()

        for producto_id_raw, cantidad_raw, costo_raw in zip(productos_ids, cantidades, costos):
            if not producto_id_raw or not cantidad_raw:
                continue
            db.session.add(
                DetalleOrdenCompra(
                    orden_id=orden.id,
                    producto_id=int(producto_id_raw),
                    cantidad=int(cantidad_raw),
                    costo_unitario=float(costo_raw or 0),
                )
            )

        db.session.commit()
        flash(f"Orden de compra {orden.numero_orden} creada.", "success")
        return redirect(url_for("proveedores.ordenes_detalle", orden_id=orden.id))

    return render_template("proveedores/orden_form.html", proveedores=proveedores, productos=productos)


@proveedor_bp.route("/ordenes-compra/<int:orden_id>")
@login_required
def ordenes_detalle(orden_id):
    orden = OrdenCompra.query.get_or_404(orden_id)
    return render_template("proveedores/orden_detalle.html", orden=orden)


@proveedor_bp.route("/ordenes-compra/<int:orden_id>/recibir", methods=["POST"])
@login_required
@roles_requeridos("administrador", "supervisor")
def ordenes_recibir(orden_id):
    orden = OrdenCompra.query.get_or_404(orden_id)
    if orden.estado != EstadoOrdenCompra.PENDIENTE:
        flash("Esta orden ya fue procesada.", "warning")
        return redirect(url_for("proveedores.ordenes_detalle", orden_id=orden.id))

    for detalle in orden.detalles:
        detalle.producto.stock_actual += detalle.cantidad
        detalle.producto.costo = detalle.costo_unitario

    orden.estado = EstadoOrdenCompra.RECIBIDA
    orden.fecha_recepcion = datetime.utcnow()
    db.session.commit()

    flash(f"Orden {orden.numero_orden} recibida. Inventario actualizado.", "success")
    return redirect(url_for("proveedores.ordenes_detalle", orden_id=orden.id))
