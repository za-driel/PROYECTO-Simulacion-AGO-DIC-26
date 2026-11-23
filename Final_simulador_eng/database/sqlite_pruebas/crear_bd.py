"""Crea simulador_ingles.db: aplica schema.sql y carga niveles + 80 preguntas."""
import os
import sqlite3

from datos_preguntas import NIVELES, PREGUNTAS

AQUI = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(AQUI, "simulador_ingles.db")


def crear_bd(db_path=DB_PATH):
    if os.path.exists(db_path):
        os.remove(db_path)
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys = ON")
    with open(os.path.join(AQUI, "schema.sql"), encoding="utf-8") as f:
        con.executescript(f.read())

    con.executemany("INSERT INTO niveles (nivel_id, nombre_nivel, orden) VALUES (?,?,?)", NIVELES)

    for q in PREGUNTAS:
        cur = con.execute(
            "INSERT INTO preguntas (nivel_id, texto_pregunta, imagen_url) VALUES (?,?,?)",
            (q["nivel_id"], q["texto"], q.get("imagen_url")),
        )
        pid = cur.lastrowid
        for letra, texto in zip("abcd", q["opciones"]):
            con.execute(
                "INSERT INTO opciones (pregunta_id, letra, texto, es_correcta) VALUES (?,?,?,?)",
                (pid, letra, texto, 1 if letra == q["correcta"] else 0),
            )
    con.commit()
    return con


if __name__ == "__main__":
    con = crear_bd()
    print("BD creada en:", DB_PATH)
    for nombre, n in con.execute(
        "SELECT n.nombre_nivel, COUNT(*) FROM preguntas p JOIN niveles n USING(nivel_id) "
        "GROUP BY n.nivel_id ORDER BY n.orden"
    ):
        print(f"  {nombre}: {n} preguntas")
    print("  Total:", con.execute("SELECT COUNT(*) FROM preguntas").fetchone()[0])
    con.close()
