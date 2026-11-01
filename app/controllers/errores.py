from flask import Flask, render_template


def registrar_manejadores_error(app: Flask) -> None:
    @app.errorhandler(401)
    def no_autorizado(error):
        return render_template("errors/401.html"), 401

    @app.errorhandler(403)
    def prohibido(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def no_encontrado(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def error_servidor(error):
        return render_template("errors/500.html"), 500
