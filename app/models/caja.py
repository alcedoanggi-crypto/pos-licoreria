import enum
from datetime import datetime

from app.extensions import db


class EstadoCaja(str, enum.Enum):
    ABIERTA = "abierta"
    CERRADA = "cerrada"


class Caja(db.Model):
    """Representa un turno de caja: desde que un cajero la abre hasta que la cierra con arqueo."""

    __tablename__ = "cajas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, default="Caja 1")

    empleado_id = db.Column(db.Integer, db.ForeignKey("empleados.id"), nullable=False)
    empleado = db.relationship("Empleado", back_populates="cajas", foreign_keys=[empleado_id])

    estado = db.Column(db.Enum(EstadoCaja, name="estado_caja"), nullable=False, default=EstadoCaja.ABIERTA)

    fecha_apertura = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    monto_apertura = db.Column(db.Numeric(12, 2), nullable=False, default=0)

    fecha_cierre = db.Column(db.DateTime)
    monto_sistema = db.Column(db.Numeric(12, 2))  # calculado: apertura + ventas en efectivo
    monto_contado = db.Column(db.Numeric(12, 2))  # ingresado por el cajero al arquear
    diferencia = db.Column(db.Numeric(12, 2))  # contado - sistema
    observaciones = db.Column(db.Text)

    ventas = db.relationship("Venta", back_populates="caja")

    @property
    def total_ventas_efectivo(self) -> float:
        return sum(float(v.total) for v in self.ventas if v.metodo_pago == "efectivo" and v.estado.value == "completada")

    @property
    def total_ventas(self) -> float:
        return sum(float(v.total) for v in self.ventas if v.estado.value == "completada")

    def __repr__(self) -> str:
        return f"<Caja {self.id} {self.estado.value}>"
