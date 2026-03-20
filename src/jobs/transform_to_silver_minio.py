"""
transform_to_silver_minio.py — Clean raw ranking CSV and write partitioned Parquet to silver layer.
"""

import os
import io
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import ftfy
import polars as pl

from config import FECHA_CARGA
from iout import storage

# ── Configuración ─────────────────────────────────────────────────────────────

RAW_OBJECT    = f"ranking_completo_{FECHA_CARGA}.csv"
SILVER_OBJECT = f"ranking_completo_{FECHA_CARGA}.parquet"

# ── Parsing helpers ───────────────────────────────────────────────────────────

def parse_tiempo(tiempo: str | None) -> tuple[int, int, int]:
    """
    Parse 'X días, Y horas y Z minutos' into (dias, horas, minutos).
    Any missing component defaults to 0.
    """
    if not tiempo:
        return 0, 0, 0

    dias    = int(m.group(1)) if (m := re.search(r'(\d+)\s+día', tiempo))    else 0
    horas   = int(m.group(1)) if (m := re.search(r'(\d+)\s+hora', tiempo))   else 0
    minutos = int(m.group(1)) if (m := re.search(r'(\d+)\s+minuto', tiempo)) else 0

    return dias, horas, minutos


def fix_encoding(value: str | None) -> str | None:
    """Fix mojibake and broken unicode using ftfy."""
    if value is None:
        return None
    return ftfy.fix_text(value.strip())

# ── Transformaciones ──────────────────────────────────────────────────────────

def infer_position(df: pl.DataFrame) -> pl.DataFrame:
    """
    Top 3 players have no position — infer it from row order.
    Also removes thousands separator from position numbers.
    """
    return df.with_columns(
        pl.col("#")
          .str.strip_chars()
          .str.replace_all(r"\.", "")
          .replace("", None)
          .fill_null(
              pl.Series([(i + 1) for i in range(len(df))]).cast(pl.Utf8)
          )
          .cast(pl.Int32)
          .alias("posicion")
    ).drop("#")


def clean_integer(col: str) -> pl.Expr:
    """Remove thousands separator (.) and cast to Int64."""
    return (
        pl.col(col)
          .str.replace_all(r"\.", "")
          .str.strip_chars()
          .cast(pl.Int64)
    )


def clean_precision(col: str = "PRECISIÓN") -> pl.Expr:
    """'29,17%' → 0.2917 as Float64."""
    return (
        pl.col(col)
          .str.replace("%", "")
          .str.replace(",", ".")
          .cast(pl.Float64)
          .truediv(100)
          .alias("precision_pct")
    )


def expand_tiempo(df: pl.DataFrame) -> pl.DataFrame:
    """Parse TIEMPO JUGADO into dias, horas, minutos columns."""
    parsed = [parse_tiempo(v) for v in df["TIEMPO JUGADO"].to_list()]
    dias, horas, minutos = zip(*parsed) if parsed else ([], [], [])

    return df.with_columns([
        pl.Series("dias_jugados",    list(dias)).cast(pl.Int32),
        pl.Series("horas_jugadas",   list(horas)).cast(pl.Int32),
        pl.Series("minutos_jugados", list(minutos)).cast(pl.Int32),
    ]).drop("TIEMPO JUGADO")


def fix_nick_encoding(df: pl.DataFrame) -> pl.DataFrame:
    """Apply ftfy encoding fix to NICK CS column."""
    fixed = [fix_encoding(v) for v in df["NICK CS"].to_list()]
    return df.with_columns(
        pl.Series("nick_cs", fixed)
    ).drop("NICK CS")


def rename_columns(df: pl.DataFrame) -> pl.DataFrame:
    """Normalize all column names to snake_case."""
    mapping = {
        "PUNTOS":           "puntos",
        "PARTIDAS GANADAS": "partidas_ganadas",
        "FRAGS":            "frags",
        "ASISTENCIAS":      "asistencias",
        "MUERTES":          "muertes",
        "HS":               "hs",
        "HITS":             "hits",
        "DISPAROS":         "disparos",
        "DAÑO":             "dano",
    }
    return df.rename({k: v for k, v in mapping.items() if k in df.columns})


def add_metadata(df: pl.DataFrame) -> pl.DataFrame:
    """Add fecha_carga as partition column."""
    return df.with_columns(
        pl.lit(str(FECHA_CARGA)).cast(pl.Utf8).alias("fecha_carga")
    )

# ── Pipeline ──────────────────────────────────────────────────────────────────

def transform(df: pl.DataFrame) -> pl.DataFrame:
    """Full transformation pipeline: raw → silver."""
    int_cols = [
        "PUNTOS", "PARTIDAS GANADAS", "FRAGS", "ASISTENCIAS",
        "MUERTES", "HS", "HITS", "DISPAROS", "DAÑO",
    ]

    return (
        df
        .pipe(infer_position)
        .pipe(fix_nick_encoding)
        .with_columns([clean_integer(c) for c in int_cols])
        .with_columns(clean_precision())
        .drop("PRECISIÓN")
        .pipe(expand_tiempo)
        .pipe(rename_columns)
        .pipe(add_metadata)
        .select([
            "posicion",
            "nick_cs",
            "puntos",
            "partidas_ganadas",
            "frags",
            "asistencias",
            "muertes",
            "hs",
            "hits",
            "disparos",
            "precision_pct",
            "dano",
            "dias_jugados",
            "horas_jugadas",
            "minutos_jugados",
            "fecha_carga",
        ])
    )

# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print(f"🔧 transform_to_silver_minio [fecha_carga={FECHA_CARGA}]\n")

    print(f"📥 Leyendo raw/{RAW_OBJECT} desde MinIO...")
    raw_bytes = storage.download_raw(RAW_OBJECT)
    df_raw    = pl.read_csv(io.BytesIO(raw_bytes), infer_schema_length=0)
    print(f"   {df_raw.shape[0]} filas, {df_raw.shape[1]} columnas")

    print("🔧 Transformando...")
    df_silver = transform(df_raw)
    print(df_silver.head(5))
    print(f"   Schema: {df_silver.schema}")

    print(f"\n📤 Escribiendo silver particionado en MinIO...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        df_silver.write_parquet(
            tmp_dir,
            use_pyarrow=True,
            pyarrow_options={"partition_cols": ["fecha_carga"]},
        )

        for root, _, files in os.walk(tmp_dir):
            for file in files:
                local_path  = os.path.join(root, file)
                relative    = os.path.relpath(local_path, tmp_dir)
                object_name = f"{storage.SILVER}/{relative}"

                with open(local_path, "rb") as f:
                    storage.upload(
                        data=f.read(),
                        object_name=object_name,
                        content_type="application/octet-stream",
                    )

    print("✅ Listo!")


if __name__ == "__main__":
    main()