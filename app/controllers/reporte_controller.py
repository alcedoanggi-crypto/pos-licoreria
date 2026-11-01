from datetime import date, datetime, timedelta

from flask import Blueprint, current_app, render_template, request, send_file
from flask_login import login_required

from app.models import Caja, Venta
from app.models.venta import EstadoVenta
from app.utils.decorators import roles_requeridos
from app.utils.formularios import parsear_fecha
from app.utils.reportes import generar_excel_cierre_diario, generar_pdf_cierre_diario

reporte_bp = Blueprint("reportes", __name__)


def _rango_del_dia(fecha: date):
    inicio = datetime(fecha.year, fecha.month, fecha.day)
    fin = inicio + timedelta(days=1)
    return inicio, fin


def _ventas_y_cajas_del_dia(fecha: date):
    inicio, fin = _rango_del_dia(fecha)
    ventas = (
        Venta.query.filter(Venta.fecha >= inicio, Venta.fecha < fin, Venta.estado == EstadoVenta.COMPLETADA)
        .order_by(Venta.fecha)
        .all()
    )
    cajas = Caja.query.filter(Caja.fecha_apertura >= inicio, Caja.fecha_apertura < fin).all()
    return ventas, cajas


@reporte_bp.route("/cierre-diario")
@login_required
@roles_requeridos("supervisor", "administrador")
def cierre_diario():
    fecha = parsear_fecha(request.args.get("fecha")) or date.today()
    ventas, cajas = _ventas_y_cajas_del_dia(fecha)
    total_dia = sum(float(v.total) for v in ventas)
    ticket_promedio = total_dia / len(ventas) if ventas else 0

    return render_template(
        "reportes/cierre_diario.html", fecha=fecha, ventas=ventas, cajas=cajas, total_dia=total_dia, ticket_promedio=ticket_promedio
    )


@reporte_bp.route("/cierre-diario/pdf")
@login_required
@roles_requeridos("supervisor", "administrador")
def cierre_diario_pdf():
    fecha = parsear_fecha(request.args.get("fecha")) or date.today()
    ventas, cajas = _ventas_y_cajas_del_dia(fecha)

    output_dir = f"{current_app.instance_path}/reportes"
    ruta_pdf = generar_pdf_cierre_diario(fecha, ventas, cajas, output_dir)
    return send_file(ruta_pdf, as_attachment=True, download_name=f"cierre-{fecha.isoformat()}.pdf")


@reporte_bp.route("/cierre-diario/excel")
@login_required
@roles_requeridos("supervisor", "administrador")
def cierre_diario_excel():
    fecha = parsear_fecha(request.args.get("fecha")) or date.today()
    ventas, _ = _ventas_y_cajas_del_dia(fecha)

    output_dir = f"{current_app.instance_path}/reportes"
    ruta_excel = generar_excel_cierre_diario(fecha, ventas, output_dir)
    return send_file(
        ruta_excel,
        as_attachment=True,
        download_name=f"cierre-{fecha.isoformat()}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
