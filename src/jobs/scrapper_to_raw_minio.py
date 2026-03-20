"""
scrapper_to_raw_minio.py — Scrape xa-cs.com.ar ranking and upload raw data to MinIO.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import csv
import io
import json
import re

from bs4 import BeautifulSoup
from seleniumbase import SB

from config import FECHA_CARGA
from iout import storage

# ── Configuración ─────────────────────────────────────────────────────────────

BASE_URL   = "https://xa-cs.com.ar/servidores/ranking-1-gungame-teamplay/general/0/"
PAGED_URL  = "https://xa-cs.com.ar/servidores/ranking-1-gungame-teamplay/general/0/page/{}/"
DELAY      = 2.0
CF_PHRASES = ("moment", "verificar", "un momento")

# ── Helpers puros ─────────────────────────────────────────────────────────────

def page_url(page: int) -> str:
    """Return the URL for a given page number (1-indexed)."""
    return BASE_URL if page == 1 else PAGED_URL.format(page)


def is_cloudflare(title: str) -> bool:
    """Return True if the page title indicates a Cloudflare challenge."""
    return any(phrase in title.lower() for phrase in CF_PHRASES)


def detect_total_pages(html: str, fallback: int = 47) -> int:
    """Parse total page count from HTML, return fallback if not found."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()

    if match := re.search(r'[Pp]ágina\s+\d+\s+de\s+(\d+)', text):
        return int(match.group(1))

    for tag in soup.find_all(string=re.compile(r'de\s+\d+')):
        if match := re.search(r'de\s+(\d+)', tag):
            return int(match.group(1))

    print(f"⚠️  Total de páginas no detectado, usando fallback={fallback}")
    return fallback


def parse_table(html: str) -> list[list[str]]:
    """Extract all rows from the first table in the HTML."""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")

    if not table:
        return []

    return [
        [cell.get_text(strip=True) for cell in row.find_all(["td", "th"])]
        for row in table.find_all("tr")
        if row.find(["td", "th"])
    ]


def serialize(
    data: list[list[str]],
    headers: list[str] | None,
) -> tuple[bytes, bytes]:
    """Serialize data to CSV and JSON bytes in memory."""
    records = [dict(zip(headers, row)) for row in data] if headers else data

    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    if headers:
        writer.writerow(headers)
    writer.writerows(data)
    csv_bytes  = csv_buffer.getvalue().encode("utf-8")
    json_bytes = json.dumps(records, ensure_ascii=False, indent=2).encode("utf-8")

    return csv_bytes, json_bytes

# ── Browser helpers ───────────────────────────────────────────────────────────

def wait_for_cloudflare(sb: SB, timeout: int = 60) -> bool:
    """Block until Cloudflare challenge resolves. Return False on timeout."""
    for _ in range(timeout):
        sb.sleep(1)
        if not is_cloudflare(sb.get_title()):
            return True
    return False


def scrape_page(sb: SB, page: int, total: int) -> list[list[str]]:
    """Navigate to a page and return its table rows, or [] on failure."""
    sb.open(page_url(page))
    sb.sleep(DELAY)

    if is_cloudflare(sb.get_title()):
        print(f"  ⏳ Página {page}: Cloudflare, esperando...")
        if not wait_for_cloudflare(sb, timeout=20):
            print(f"  ❌ Página {page}: timeout")
            return []

    rows = parse_table(sb.get_page_source())

    if not rows:
        print(f"  ⚠️  Página {page}/{total}: sin tabla")
    else:
        print(f"  ✅ Página {page}/{total}: {len(rows) - 1} jugadores")

    return rows

# ── Orquestación ──────────────────────────────────────────────────────────────

def collect_all_pages(sb: SB) -> tuple[list[list[str]], list[str] | None]:
    """Scrape all ranking pages. Returns (data_rows, headers)."""
    total   = detect_total_pages(sb.get_page_source())
    headers = None
    data    = []
    retries = []

    print(f"📄 Total de páginas: {total}\n")

    for page in range(1, total + 1):
        rows = scrape_page(sb, page, total)

        if not rows:
            retries.append(page)
            continue

        if headers is None:
            headers = rows[0]
            data.extend(rows[1:])
        else:
            start = 1 if rows[0] == headers else 0
            data.extend(rows[start:])

    if retries:
        print(f"\n🔁 Reintentando páginas fallidas: {retries}")
        for page in retries:
            rows = scrape_page(sb, page, total)
            if rows:
                start = 1 if rows[0] == headers else 0
                data.extend(rows[start:])
                print(f"  ✅ Página {page}: recuperada")
            else:
                print(f"  ❌ Página {page}: descartada")

    return data, headers


def main() -> None:
    print(f"🚀 Iniciando scraper [fecha_carga={FECHA_CARGA}]...\n")

    with SB(uc=True, headed=True, locale_code="es") as sb:
        sb.open(BASE_URL)
        sb.sleep(3)

        if is_cloudflare(sb.get_title()):
            print("⏳ Esperando Cloudflare...")
            if not wait_for_cloudflare(sb):
                print("❌ No se pudo pasar Cloudflare")
                return

        print("✅ Cloudflare superado!\n")
        data, headers = collect_all_pages(sb)

    csv_bytes, json_bytes = serialize(data, headers)

    print(f"\n📊 Total jugadores recolectados: {len(data)}")
    storage.upload_raw(csv_bytes,  f"ranking_completo_{FECHA_CARGA}.csv",  "text/csv")
    storage.upload_raw(json_bytes, f"ranking_completo_{FECHA_CARGA}.json", "application/json")


if __name__ == "__main__":
    main()