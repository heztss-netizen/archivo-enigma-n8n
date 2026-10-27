"""Planificador editorial sin generación ni publicación de contenido."""
from datetime import date, timedelta

REFERENCIA = date(2026, 10, 26)  # Semana con tres videos; lunes.
DIAS = {0: (1, 3, 5), 1: (1, 4)}  # Martes/jueves/sábado; martes/viernes.

def fechas_mes(anio, mes, limite=10, ocupados=()):
    """Proponer fechas restantes, descontando las ya publicadas o reservadas."""
    primero = date(anio, mes, 1)
    fin = date(anio + (mes == 12), mes % 12 + 1, 1)
    ocupadas = {d for d in ocupados if primero <= d < fin}
    restantes = max(0, limite - len(ocupadas))
    salida = []
    d = primero
    while d < fin:
        semana = (d - REFERENCIA).days // 7
        if d.weekday() in DIAS[semana % 2] and d not in ocupadas and restantes:
            salida.append(d)
            restantes -= 1
        d += timedelta(days=1)
    return salida

if __name__ == "__main__":
    for d in fechas_mes(2026, 11):
        print(d.isoformat(), "10:40 America/Mexico_City")
