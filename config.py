import os

from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/pos_licoreria",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    STOCK_MINIMO_DEFAULT = 10
    VENCIMIENTO_ALERTA_DIAS = 30
    EDAD_MINIMA = 18

    IVA = 0.15
    PUNTOS_POR_DOLAR = 1  # 1 punto por cada $1 de compra
    VALOR_PUNTO_DESCUENTO = 0.05  # cada punto canjeado descuenta $0.05
