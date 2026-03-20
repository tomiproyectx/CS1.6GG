"""
insert_silver_duckdb.py — Insert silver Parquet from MinIO into DuckDB ranking_silver table.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import duckdb

from config import FECHA_CARGA, DUCKDB_PATH
from iout import storage

# ── Configuración ─────────────────────────────────────────────────────────────

SILVER_OBJECT = f"s3://{storage.BUCKET}/{storage.SILVER}/fecha_carga={FECHA_CARGA}/*.parquet"

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


def already_loaded(con: duckdb.DuckDBPyConnection) -> bool:
    """Return True if FECHA_CARGA is already present in ranking_silver."""
    result = con.execute("""
        SELECT COUNT(*) FROM ranking_silver
        WHERE fecha_carga = ?
    """, [FECHA_CARGA]).fetchone()[0]
    return result > 0


def insert(con: duckdb.DuckDBPyConnection) -> int:
    """Insert silver Parquet into ranking_silver and return inserted row count."""
    con.execute(f"""
        INSERT INTO ranking_silver
        SELECT *
        FROM read_parquet('{SILVER_OBJECT}')
    """)
    return con.execute("""
        SELECT COUNT(*) FROM ranking_silver
        WHERE fecha_carga = ?
    """, [FECHA_CARGA]).fetchone()[0]

# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print(f"🦆 insert_silver_duckdb [fecha_carga={FECHA_CARGA}]\n")

    con = get_db()

    if already_loaded(con):
        print(f"⚠️  fecha_carga={FECHA_CARGA} ya existe en ranking_silver, saltando.")
        con.close()
        return

    print(f"📥 Leyendo {SILVER_OBJECT}...")
    count = insert(con)
    con.close()

    print(f"✅ {count} filas insertadas en ranking_silver")


if __name__ == "__main__":
    main()