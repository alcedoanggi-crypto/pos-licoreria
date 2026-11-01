from datetime import datetime

from app.extensions import db


class ClienteFrecuente(db.Model):
    __tablename__ = "clientes_frecuentes"

    id = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(30), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120))
    puntos = db.Column(db.Integer, nullable=False, default=0)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    ventas = db.relationship("Venta", back_populates="cliente")

    def __repr__(self) -> str:
        return f"<ClienteFrecuente {self.nombre_completo} ({self.puntos} pts)>"
