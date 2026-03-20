"""
create_db.py — Initialize local DuckDB database and table schemas.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import duckdb
from config import DUCKDB_PATH

def main() -> None:
    print(f"🦆 Creando DuckDB en {DUCKDB_PATH}...\n")

    DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(DUCKDB_PATH))

    con.execute("""
        CREATE TABLE IF NOT EXISTS ranking_raw (
            posicion         VARCHAR,
            nick_cs          VARCHAR,
            puntos           VARCHAR,
            partidas_ganadas VARCHAR,
            frags            VARCHAR,
            asistencias      VARCHAR,
            muertes          VARCHAR,
            hs               VARCHAR,
            hits             VARCHAR,
            disparos         VARCHAR,
            precision_pct    VARCHAR,
            dano             VARCHAR,
            tiempo_jugado    VARCHAR,
            fecha_carga      VARCHAR
        )
    """)
    print("  ✅ ranking_raw creada")

    con.execute("""
        CREATE TABLE IF NOT EXISTS ranking_silver (
            posicion         INTEGER,
            nick_cs          VARCHAR,
            puntos           BIGINT,
            partidas_ganadas BIGINT,
            frags            BIGINT,
            asistencias      BIGINT,
            muertes          BIGINT,
            hs               BIGINT,
            hits             BIGINT,
            disparos         BIGINT,
            precision_pct    DOUBLE,
            dano             BIGINT,
            dias_jugados     INTEGER,
            horas_jugadas    INTEGER,
            minutos_jugados  INTEGER,
            fecha_carga      VARCHAR
        )
    """)
    print("  ✅ ranking_silver creada")

    con.close()
    print(f"\n✅ DuckDB inicializado en {DUCKDB_PATH}")


if __name__ == "__main__":
    main()