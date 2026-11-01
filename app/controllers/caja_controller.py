from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Caja
from app.models.caja import EstadoCaja
from app.utils.decorators import roles_requeridos

caja_bp = Blueprint("caja", __name__)


@caja_bp.route("/abrir", methods=["GET", "POST"])
@login_required
def abrir():
    caja_activa = Caja.query.filter_by(empleado_id=current_user.id, estado=EstadoCaja.ABIERTA).first()
    if caja_activa:
        flash("Ya tienes una caja abierta.", "info")
        return redirect(url_for("pos.pantalla"))

    if request.method == "POST":
        caja = Caja(
            nombre=request.form.get("nombre", "Caja 1").strip() or "Caja 1",
            empleado_id=current_user.id,
            monto_apertura=request.form.get("monto_apertura", type=float) or 0,
        )
        db.session.add(caja)
        db.session.commit()
        flash(f"Caja abierta con ${caja.monto_apertura:.2f} en efectivo.", "success")
        return redirect(url_for("pos.pantalla"))

    return render_template("caja/abrir.html")


@caja_bp.route("/cerrar", methods=["GET", "POST"])
@login_required
def cerrar():
    caja = Caja.query.filter_by(empleado_id=current_user.id, estado=EstadoCaja.ABIERTA).first()
    if not caja:
        flash("No tienes ninguna caja abierta.", "warning")
        return redirect(url_for("dashboard.index"))

    monto_sistema = float(caja.monto_apertura) + caja.total_ventas_efectivo

    if request.method == "POST":
        monto_contado = request.form.get("monto_contado", type=float) or 0
        caja.monto_sistema = monto_sistema
        caja.monto_contado = monto_contado
        caja.diferencia = monto_contado - monto_sistema
        caja.observaciones = request.form.get("observaciones", "").strip()
        caja.estado = EstadoCaja.CERRADA
        caja.fecha_cierre = datetime.utcnow()
        db.session.commit()

        if caja.diferencia == 0:
            flash("Caja cerrada correctamente. El arqueo cuadra exacto.", "success")
        else:
            flash(f"Caja cerrada con una diferencia de ${caja.diferencia:.2f}.", "warning")
        return redirect(url_for("caja.detalle", caja_id=caja.id))

    return render_template("caja/cerrar.html", caja=caja, monto_sistema=monto_sistema)


@caja_bp.route("/historial")
@login_required
@roles_requeridos("supervisor", "administrador")
def historial():
    cajas = Caja.query.order_by(Caja.fecha_apertura.desc()).all()
    return render_template("caja/historial.html", cajas=cajas)


@caja_bp.route("/<int:caja_id>")
@login_required
def detalle(caja_id):
    caja = Caja.query.get_or_404(caja_id)
    if caja.empleado_id != current_user.id and not current_user.tiene_rol("supervisor", "administrador"):
        from flask import abort

        abort(403)
    return render_template("caja/detalle.html", caja=caja)
