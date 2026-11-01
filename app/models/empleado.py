import enum
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class RolEmpleado(str, enum.Enum):
    CAJERO = "cajero"
    SUPERVISOR = "supervisor"
    ADMINISTRADOR = "administrador"


class Empleado(UserMixin, db.Model):
    __tablename__ = "empleados"

    id = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    pin = db.Column(db.String(10))  # PIN rápido para confirmar apertura/cierre de caja en el mostrador
    rol = db.Column(db.Enum(RolEmpleado, name="rol_empleado"), nullable=False, default=RolEmpleado.CAJERO)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    cajas = db.relationship("Caja", back_populates="empleado", foreign_keys="Caja.empleado_id")
    ventas = db.relationship("Venta", back_populates="empleado")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def tiene_rol(self, *roles: str) -> bool:
        return self.rol.value in roles

    def __repr__(self) -> str:
        return f"<Empleado {self.email} ({self.rol.value})>"
