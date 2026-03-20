"""
insert_raw_duckdb.py — Insert raw CSV from MinIO into DuckDB ranking_raw table.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import duckdb

from config import FECHA_CARGA, DUCKDB_PATH
from iout import storage

# ── Configuración ─────────────────────────────────────────────────────────────

RAW_OBJECT  = f"s3://{storage.BUCKET}/{storage.RAW}/ranking_completo_{FECHA_CARGA}.csv"

RAW_SCHEMA = {
    "posicion":         "VARCHAR",
    "nick_cs":          "VARCHAR",
    "puntos":           "VARCHAR",
    "partidas_ganadas": "VARCHAR",
    "frags":            "VARCHAR",
    "asistencias":      "VARCHAR",
    "muertes":          "VARCHAR",
    "hs":               "VARCHAR",
    "hits":             "VARCHAR",
    "disparos":         "VARCHAR",
    "precision_pct":    "VARCHAR",
    "dano":             "VARCHAR",
    "tiempo_jugado":    "VARCHAR",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_db() -> duckdb.DuckDBPyConnection:
    """Return a DuckDB connection configured with MinIO as S3 backend."""
    con = duckdb.connect(str(DUCKDB_PATH))
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(f"""
        SET s3_endpoint          = '{storage.ENDPOINT}';
        SET s3_access_key_id     = '{storage.ACCESS}';
        SET s3_secret_access_key = '{storage.SECRET}';
        SET s3_use_ssl           = false;
        SET s3_url_style         = 'path';
    """)
    return con


def schema_str() -> str:
    """Build DuckDB columns definition string from RAW_SCHEMA."""
    return ", ".join(f"'{k}': '{v}'" for k, v in RAW_SCHEMA.items())


def ensure_table(con: duckdb.DuckDBPyConnection) -> None:
    """Create ranking_raw table if it doesn't exist."""
    con.execute(f"""
        CREATE TABLE IF NOT EXISTS ranking_raw AS
        SELECT *, '{FECHA_CARGA}' AS fecha_carga
        FROM read_csv(
            '{RAW_OBJECT}',
            header       = true,
            auto_detect  = false,
            columns      = {{{schema_str()}}}
        )
        WHERE 1=0
    """)


def already_loaded(con: duckdb.DuckDBPyConnection) -> bool:
    """Return True if FECHA_CARGA is already present in ranking_raw."""
    result = con.execute("""
        SELECT COUNT(*) FROM ranking_raw
        WHERE fecha_carga = ?
    """, [FECHA_CARGA]).fetchone()[0]
    return result > 0


def insert(con: duckdb.DuckDBPyConnection) -> int:
    """Insert raw CSV into ranking_raw and return inserted row count."""
    con.execute(f"""
        INSERT INTO ranking_raw
        SELECT *, '{FECHA_CARGA}' AS fecha_carga
        FROM read_csv(
            '{RAW_OBJECT}',
            header       = true,
            auto_detect  = false,
            columns      = {{{schema_str()}}}
        )
    """)
    return con.execute("""
        SELECT COUNT(*) FROM ranking_raw
        WHERE fecha_carga = ?
    """, [FECHA_CARGA]).fetchone()[0]

# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print(f"🦆 insert_raw_duckdb [fecha_carga={FECHA_CARGA}]\n")

    con = get_db()
    ensure_table(con)

    if already_loaded(con):
        print(f"⚠️  fecha_carga={FECHA_CARGA} ya existe en ranking_raw, saltando.")
        con.close()
        return

    count = insert(con)
    con.close()

    print(f"✅ {count} filas insertadas en ranking_raw")


if __name__ == "__main__":
    main()