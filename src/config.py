import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

FECHA_CARGA = os.getenv("FECHA_CARGA", datetime.now().strftime("%Y%m%d"))
REPO_ROOT   = Path(__file__).parent.parent
DUCKDB_PATH = REPO_ROOT / "db" / "cs16.duckdb"