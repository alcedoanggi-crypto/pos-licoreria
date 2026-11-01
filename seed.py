"""Carga de datos de ejemplo para desarrollo local.

Uso: python seed.py
"""
from datetime import date, timedelta

from app import create_app
from app.extensions import db
from app.models import Categoria, ClienteFrecuente, Empleado, Producto, Proveedor
from app.models.empleado import RolEmpleado

app = create_app()

with app.app_context():
    db.create_all()

    if Empleado.query.filter_by(email="admin@poslicoreria.com").first():
        print("Los datos de ejemplo ya existen. No se realizaron cambios.")
    else:
        admin = Empleado(nombre_completo="Marta Administradora", email="admin@poslicoreria.com", pin="1111", rol=RolEmpleado.ADMINISTRADOR)
        admin.set_password("admin123")

        supervisor = Empleado(nombre_completo="Sergio Supervisor", email="supervisor@poslicoreria.com", pin="2222", rol=RolEmpleado.SUPERVISOR)
        supervisor.set_password("supervisor123")

        cajero = Empleado(nombre_completo="Carla Cajera", email="cajero@poslicoreria.com", pin="3333", rol=RolEmpleado.CAJERO)
        cajero.set_password("cajero123")

        db.session.add_all([admin, supervisor, cajero])

        categorias = {
            "whisky": Categoria(nombre="Whisky", descripcion="Whiskies escoceses, irlandeses y bourbon"),
            "ron": Categoria(nombre="Ron", descripcion="Rones añejos y blancos"),
            "vino": Categoria(nombre="Vinos", descripcion="Vinos tintos, blancos y espumosos"),
            "cerveza": Categoria(nombre="Cerveza", descripcion="Cervezas nacionales e importadas"),
            "licor": Categoria(nombre="Licores y aperitivos", descripcion="Licores, vermuts y aperitivos"),
        }
        db.session.add_all(categorias.values())

        proveedor = Proveedor(razon_social="Distribuidora Central de Licores", contacto_nombre="Roberto Salas", telefono="555-0100", email="ventas@distcentral.com")
        db.session.add(proveedor)
        db.session.flush()

        hoy = date.today()

        productos = [
            Producto(codigo_barras="7501234560014", sku="WHK-100", nombre="Whisky Escocés 12 años", presentacion="Botella 750ml",
                     categoria_id=categorias["whisky"].id, proveedor_id=proveedor.id, precio_venta=32.50, costo=20.00,
                     stock_actual=45, stock_minimo=15),
            Producto(codigo_barras="7501234560021", sku="RON-100", nombre="Ron Añejo 7 años", presentacion="Botella 750ml",
                     categoria_id=categorias["ron"].id, proveedor_id=proveedor.id, precio_venta=18.00, costo=11.00,
                     stock_actual=8, stock_minimo=15),
            Producto(codigo_barras="7501234560038", sku="VIN-100", nombre="Vino Tinto Reserva", presentacion="Botella 750ml",
                     categoria_id=categorias["vino"].id, proveedor_id=proveedor.id, precio_venta=15.00, costo=9.00,
                     stock_actual=30, stock_minimo=10, fecha_vencimiento=hoy + timedelta(days=20)),
            Producto(codigo_barras="7501234560045", sku="CRV-100", nombre="Cerveza Lager Importada", presentacion="Botella 355ml",
                     categoria_id=categorias["cerveza"].id, proveedor_id=proveedor.id, precio_venta=3.50, costo=1.80,
                     stock_actual=150, stock_minimo=40),
            Producto(codigo_barras="7501234560052", sku="LIC-100", nombre="Aperitivo Amaro Tradicional", presentacion="Botella 700ml",
                     categoria_id=categorias["licor"].id, proveedor_id=proveedor.id, precio_venta=22.00, costo=13.50,
                     stock_actual=5, stock_minimo=10),
            Producto(codigo_barras="7501234560069", sku="VDK-100", nombre="Vodka Premium", presentacion="Botella 750ml",
                     categoria_id=categorias["whisky"].id, proveedor_id=proveedor.id, precio_venta=20.00, costo=12.00,
                     stock_actual=25, stock_minimo=10),
        ]
        db.session.add_all(productos)

        clientes = [
            ClienteFrecuente(nombre_completo="Juan Pérez", telefono="5551112222", email="juan@example.com", puntos=45),
            ClienteFrecuente(nombre_completo="María López", telefono="5553334444", email="maria@example.com", puntos=120),
        ]
        db.session.add_all(clientes)

        db.session.commit()
        print("Datos de ejemplo creados correctamente.")
        print("Usuarios de prueba (contraseña / PIN rápido):")
        print("  admin@poslicoreria.com / admin123 (administrador, PIN 1111)")
        print("  supervisor@poslicoreria.com / supervisor123 (supervisor, PIN 2222)")
        print("  cajero@poslicoreria.com / cajero123 (cajero, PIN 3333)")
        print("Clientes frecuentes de prueba: tel. 5551112222 (45 pts), 5553334444 (120 pts)")
