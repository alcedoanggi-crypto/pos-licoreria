from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, render_template
from flask_login import login_required
from sqlalchemy import extract, func

from app.extensions import db
from app.models import Caja, DetalleVenta, Producto, Venta
from app.models.caja import EstadoCaja
from app.models.venta import EstadoVenta

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    hoy = date.today()
    inicio_dia = datetime(hoy.year, hoy.month, hoy.day)

    ventas_hoy = Venta.query.filter(Venta.fecha >= inicio_dia, Venta.estado == EstadoVenta.COMPLETADA).all()
    ventas_hoy_total = sum(float(v.total) for v in ventas_hoy)
    ticket_promedio = ventas_hoy_total / len(ventas_hoy) if ventas_hoy else 0

    producto_estrella = (
        db.session.query(Producto.nombre, func.sum(DetalleVenta.cantidad).label("total"))
        .join(DetalleVenta, DetalleVenta.producto_id == Producto.id)
        .join(Venta, DetalleVenta.venta_id == Venta.id)
        .filter(Venta.fecha >= inicio_dia, Venta.estado == EstadoVenta.COMPLETADA)
        .group_by(Producto.id)
        .order_by(func.sum(DetalleVenta.cantidad).desc())
        .first()
    )

    productos = Producto.query.filter_by(activo=True).all()
    stock_bajo = sum(1 for p in productos if p.stock_bajo)
    proximos_a_vencer = [p for p in productos if p.proximo_a_vencer]

    cajas_abiertas = Caja.query.filter_by(estado=EstadoCaja.ABIERTA).count()

    return render_template(
        "dashboard/index.html",
        ventas_hoy_total=ventas_hoy_total,
        ventas_hoy_cantidad=len(ventas_hoy),
        ticket_promedio=ticket_promedio,
        producto_estrella=producto_estrella[0] if producto_estrella else "—",
        stock_bajo=stock_bajo,
        proximos_a_vencer=proximos_a_vencer,
        cajas_abiertas=cajas_abiertas,
    )


@dashboard_bp.route("/api/ventas-periodo")
@login_required
def api_ventas_periodo():
    hace_7_dias = datetime.utcnow() - timedelta(days=6)
    resultados = (
        db.session.query(func.date(Venta.fecha), func.coalesce(func.sum(Venta.total), 0))
        .filter(Venta.fecha >= hace_7_dias, Venta.estado == EstadoVenta.COMPLETADA)
        .group_by(func.date(Venta.fecha))
        .order_by(func.date(Venta.fecha))
        .all()
    )
    labels = [r[0].strftime("%d/%m") if hasattr(r[0], "strftime") else str(r[0]) for r in resultados]
    valores = [float(r[1]) for r in resultados]
    return jsonify({"labels": labels, "valores": valores})


@dashboard_bp.route("/api/productos-mas-vendidos")
@login_required
def api_productos_mas_vendidos():
    resultados = (
        db.session.query(Producto.nombre, func.coalesce(func.sum(DetalleVenta.cantidad), 0))
        .select_from(DetalleVenta)
        .join(Venta, DetalleVenta.venta_id == Venta.id)
        .join(Producto, DetalleVenta.producto_id == Producto.id)
        .filter(Venta.estado == EstadoVenta.COMPLETADA)
        .group_by(Producto.id)
        .order_by(func.sum(DetalleVenta.cantidad).desc())
        .limit(8)
        .all()
    )
    return jsonify({"labels": [r[0] for r in resultados], "valores": [int(r[1]) for r in resultados]})


@dashboard_bp.route("/api/horas-pico")
@login_required
def api_horas_pico():
    resultados = (
        db.session.query(extract("hour", Venta.fecha), func.count(Venta.id))
        .filter(Venta.estado == EstadoVenta.COMPLETADA)
        .group_by(extract("hour", Venta.fecha))
        .order_by(extract("hour", Venta.fecha))
        .all()
    )
    por_hora = {int(hora): cantidad for hora, cantidad in resultados}
    labels = [f"{h:02d}:00" for h in range(24)]
    valores = [por_hora.get(h, 0) for h in range(24)]
    return jsonify({"labels": labels, "valores": valores})
