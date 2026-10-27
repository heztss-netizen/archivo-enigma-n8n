"""Control local de reservas de producción. No consulta facturas ni ejecuta compras.

Requiere almacenamiento persistente compartido por todos los productores.
Reservar el máximo posible antes de cada llamada; liquidar con el cargo real.
Los gastos ajenos deben registrarse antes de habilitar producción.
"""
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

def reservar(db, clave, costo_centavos, limite_centavos=150000, ahora=None):
    if not clave or not isinstance(costo_centavos, int) or costo_centavos <= 0:
        raise ValueError("Reserva inválida")
    ahora = ahora or datetime.now(ZoneInfo("America/Mexico_City"))
    mes = ahora.astimezone(ZoneInfo("America/Mexico_City")).strftime("%Y-%m")
    con = sqlite3.connect(db, timeout=30, isolation_level=None)
    try:
        con.execute("CREATE TABLE IF NOT EXISTS gastos (clave TEXT PRIMARY KEY, mes TEXT NOT NULL, centavos INTEGER NOT NULL CHECK(centavos>=0), estado TEXT NOT NULL)")
        con.execute("BEGIN IMMEDIATE")
        if con.execute("SELECT 1 FROM gastos WHERE clave=?", (clave,)).fetchone():
            con.execute("ROLLBACK")
            return False
        total = con.execute("SELECT COALESCE(SUM(centavos),0) FROM gastos WHERE mes=?", (mes,)).fetchone()[0]
        if total + costo_centavos > limite_centavos:
            con.execute("ROLLBACK")
            return False
        con.execute("INSERT INTO gastos VALUES(?,?,?,?)",(clave,mes,costo_centavos,"reservado"))
        con.execute("COMMIT")
        return True
    finally:
        con.close()

def liquidar(db, clave, costo_real_centavos):
    if not isinstance(costo_real_centavos, int) or costo_real_centavos < 0:
        raise ValueError("Costo inválido")
    con = sqlite3.connect(db, timeout=30, isolation_level=None)
    try:
        con.execute("BEGIN IMMEDIATE")
        fila = con.execute("SELECT centavos,estado FROM gastos WHERE clave=?", (clave,)).fetchone()
        if fila is None or fila[1] != "reservado":
            raise ValueError("Reserva inexistente o ya liquidada")
        if costo_real_centavos > fila[0]:
            raise ValueError("Cargo superior a la reserva: revisión requerida")
        con.execute("UPDATE gastos SET centavos=?,estado='liquidado' WHERE clave=?",(costo_real_centavos,clave))
        con.execute("COMMIT")
    except Exception:
        if con.in_transaction: con.execute("ROLLBACK")
        raise
    finally:
        con.close()
