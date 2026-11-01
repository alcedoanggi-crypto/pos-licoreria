from flask import Flask

from config import Config
from app.extensions import db, login_manager, migrate


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from app.models import Empleado

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Empleado, int(user_id))

    from app.controllers.auth_controller import auth_bp
    from app.controllers.pos_controller import pos_bp
    from app.controllers.caja_controller import caja_bp
    from app.controllers.dashboard_controller import dashboard_bp
    from app.controllers.producto_controller import producto_bp
    from app.controllers.proveedor_controller import proveedor_bp
    from app.controllers.cliente_controller import cliente_bp
    from app.controllers.empleado_controller import empleado_bp
    from app.controllers.reporte_controller import reporte_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(pos_bp, url_prefix="/pos")
    app.register_blueprint(caja_bp, url_prefix="/caja")
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(producto_bp, url_prefix="/productos")
    app.register_blueprint(proveedor_bp, url_prefix="/proveedores")
    app.register_blueprint(cliente_bp, url_prefix="/clientes")
    app.register_blueprint(empleado_bp, url_prefix="/empleados")
    app.register_blueprint(reporte_bp, url_prefix="/reportes")

    from app.controllers.errores import registrar_manejadores_error

    registrar_manejadores_error(app)

    from app.utils.carrito_pos import contar_items as contar_items_pos

    @app.context_processor
    def inyectar_globales():
        from app.models import Caja
        from app.models.caja import EstadoCaja
        from flask_login import current_user

        caja_abierta = None
        if current_user.is_authenticated:
            caja_abierta = Caja.query.filter_by(empleado_id=current_user.id, estado=EstadoCaja.ABIERTA).first()

        return {"pos_items": contar_items_pos(), "caja_abierta": caja_abierta}

    return app
