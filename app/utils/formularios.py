from datetime import date, datetime


def parsear_fecha(valor: str | None) -> date | None:
    """Convierte un input type=date (YYYY-MM-DD) a date; retorna None si viene vacío."""
    if not valor:
        return None
    return datetime.strptime(valor, "%Y-%m-%d").date()
