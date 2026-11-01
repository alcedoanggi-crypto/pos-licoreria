import random
import string
from datetime import datetime

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Caja, ClienteFrecuente, DetalleVenta, Producto, Venta
from app.models.caja import EstadoCaja
from app.models.venta import EstadoVenta, MetodoPago
from app.utils import carrito_pos

pos_bp = Blueprint("pos", __name__)


def _caja_actual():
    return Caja.query.filter_by(empleado_id=current_user.id, estado=EstadoCaja.ABIERTA).first()


def _generar_numero_venta() -> str:
    sufijo = "".join(random.choices(string.digits, k=6))
    return f"VTA-{datetime.utcnow():%Y%m%d}-{sufijo}"


@pos_bp.route("/")
@login_required
def pantalla():
    if not _caja_actual():
        flash("Debes abrir tu caja antes de vender.", "warning")
        return redirect(url_for("caja.abrir"))

    items = carrito_pos.obtener_items_detallados()
    subtotal = sum(item["subtotal"] for item in items)
    return render_template("pos/pantalla.html", items=items, subtotal=subtotal)


@pos_bp.route("/buscar")
@login_required
def buscar():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])

    # Prioriza coincidencia exacta de código de barras (lectura de escáner)
    producto = Producto.query.filter_by(codigo_barras=q, activo=True).first()
    if producto:
        resultados = [producto]
    else:
        like = f"%{q}%"
        resultados = (
            Producto.query.filter(Producto.activo.is_(True))
            .filter((Producto.nombre.ilike(like)) | (Producto.sku.ilike(like)) | (Producto.codigo_barras.ilike(like)))
            .limit(12)
            .all()
        )

    return jsonify(
        [
            {
                "id": p.id,
                "nombre": p.nombre,
                "presentacion": p.presentacion,
                "precio": float(p.precio_venta),
                "stock": p.stock_actual,
                "codigo_barras": p.codigo_barras,
            }
            for p in resultados
        ]
    )


@pos_bp.route("/carrito/agregar", methods=["POST"])
@login_required
def carrito_agregar():
    producto_id = request.form.get("producto_id", type=int)
    cantidad = request.form.get("cantidad", type=int) or 1
    producto = Producto.query.get_or_404(producto_id)

    if producto.stock_actual < cantidad:
        return jsonify({"ok": False, "mensaje": f"Solo hay {producto.stock_actual} unidades disponibles."}), 400

    carrito_pos.agregar_producto(producto_id, cantidad)
    return jsonify({"ok": True, "items": len(carrito_pos.obtener_items_detallados()), "subtotal": carrito_pos.calcular_subtotal()})


@pos_bp.route("/carrito/actualizar", methods=["POST"])
@login_required
def carrito_actualizar():
    producto_id = request.form.get("producto_id", type=int)
    cantidad = request.form.get("cantidad", type=int) or 0
    carrito_pos.actualizar_cantidad(producto_id, cantidad)
    return jsonify({"ok": True, "subtotal": carrito_pos.calcular_subtotal()})


@pos_bp.route("/carrito/eliminar", methods=["POST"])
@login_required
def carrito_eliminar():
    producto_id = request.form.get("producto_id", type=int)
    carrito_pos.eliminar_producto(producto_id)
    return jsonify({"ok": True, "subtotal": carrito_pos.calcular_subtotal()})


@pos_bp.route("/carrito/vaciar", methods=["POST"])
@login_required
def carrito_vaciar():
    carrito_pos.vaciar_carrito()
    return jsonify({"ok": True})


@pos_bp.route("/cliente-buscar")
@login_required
def cliente_buscar():
    telefono = request.args.get("telefono", "").strip()
    if not telefono:
        return jsonify(None)
    cliente = ClienteFrecuente.query.filter_by(telefono=telefono, activo=True).first()
    if not cliente:
        return jsonify(None)
    return jsonify({"id": cliente.id, "nombre": cliente.nombre_completo, "puntos": cliente.puntos})


@pos_bp.route("/venta/completar", methods=["POST"])
@login_required
def completar_venta():
    caja = _caja_actual()
    if not caja:
        flash("Debes abrir tu caja antes de vender.", "warning")
        return redirect(url_for("caja.abrir"))

    items = carrito_pos.obtener_items_detallados()
    if not items:
        flash("El carrito está vacío.", "warning")
        return redirect(url_for("pos.pantalla"))

    if not request.form.get("edad_confirmada"):
        flash("Debes confirmar que el cliente es mayor de edad antes de completar la venta.", "danger")
        return redirect(url_for("pos.pantalla"))

    for item in items:
        if item["producto"].stock_actual < item["cantidad"]:
            flash(f"Stock insuficiente para {item['producto'].nombre}.", "danger")
            return redirect(url_for("pos.pantalla"))

    subtotal = sum(item["subtotal"] for item in items)

    cliente = None
    cliente_id = request.form.get("cliente_id", type=int)
    puntos_canjear = request.form.get("puntos_canjear", type=int) or 0
    descuento_puntos = 0.0
    if cliente_id:
        cliente = ClienteFrecuente.query.get(cliente_id)
        if cliente and puntos_canjear > 0:
            puntos_canjear = min(puntos_canjear, cliente.puntos)
            descuento_puntos = puntos_canjear * current_app.config["VALOR_PUNTO_DESCUENTO"]

    subtotal_neto = max(0, subtotal - descuento_puntos)
    impuesto = round(subtotal_neto * current_app.config["IVA"], 2)
    total = round(subtotal_neto + impuesto, 2)

    metodo_pago = MetodoPago(request.form.get("metodo_pago", "efectivo"))
    monto_recibido = request.form.get("monto_recibido", type=float) or total
    cambio = round(monto_recibido - total, 2) if metodo_pago in (MetodoPago.EFECTIVO, MetodoPago.MIXTO) else 0

    if cambio < 0:
        flash("El monto recibido es menor al total de la venta.", "danger")
        return redirect(url_for("pos.pantalla"))

    puntos_otorgados = int(total * current_app.config["PUNTOS_POR_DOLAR"]) if cliente else 0

    venta = Venta(
        numero_venta=_generar_numero_venta(),
        caja_id=caja.id,
        empleado_id=current_user.id,
        cliente_id=cliente.id if cliente else None,
        subtotal=subtotal,
        impuesto=impuesto,
        descuento_puntos=descuento_puntos,
        total=total,
        metodo_pago=metodo_pago,
        monto_recibido=monto_recibido,
        cambio=cambio,
        puntos_otorgados=puntos_otorgados,
        puntos_canjeados=puntos_canjear,
        edad_confirmada=True,
        estado=EstadoVenta.COMPLETADA,
    )
    db.session.add(venta)
    db.session.flush()

    for item in items:
        db.session.add(
            DetalleVenta(
                venta_id=venta.id,
                producto_id=item["producto"].id,
                cantidad=item["cantidad"],
                precio_unitario=item["producto"].precio_venta,
            )
        )
        item["producto"].stock_actual -= item["cantidad"]

    if cliente:
        cliente.puntos = cliente.puntos - puntos_canjear + puntos_otorgados

    db.session.commit()
    carrito_pos.vaciar_carrito()

    flash(f"Venta {venta.numero_venta} completada.", "success")
    return redirect(url_for("pos.recibo", venta_id=venta.id))


@pos_bp.route("/venta/<int:venta_id>/recibo")
@login_required
def recibo(venta_id):
    venta = Venta.query.get_or_404(venta_id)
    return render_template("pos/recibo.html", venta=venta)
