"""
storage.py — Shared MinIO client and helpers for all pipeline scripts.
"""

import io
import os

from dotenv import load_dotenv
from minio import Minio
from minio.error import S3Error

load_dotenv()

# ── Configuración ─────────────────────────────────────────────────────────────

ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
ACCESS   = os.getenv("MINIO_ACCESS",   "admin")
SECRET   = os.getenv("MINIO_SECRET",   "password123")
BUCKET   = os.getenv("MINIO_BUCKET",   "cs16-ranking")
SECURE   = os.getenv("MINIO_SECURE",   "false").lower() == "true"

# ── Capas ─────────────────────────────────────────────────────────────────────

RAW    = "raw"
SILVER = "silver"
GOLD   = "gold"


# ── Client ────────────────────────────────────────────────────────────────────

def get_client() -> Minio:
    """Return a configured MinIO client."""
    return Minio(ENDPOINT, access_key=ACCESS, secret_key=SECRET, secure=SECURE)


def ensure_bucket(client: Minio, bucket: str = BUCKET) -> None:
    """Create bucket if it doesn't exist."""
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        print(f"🪣  Bucket '{bucket}' creado")


# ── Upload ────────────────────────────────────────────────────────────────────

def upload(
    data: bytes,
    object_name: str,
    content_type: str,
    bucket: str = BUCKET,
) -> None:
    """Upload raw bytes to MinIO, creating the bucket if needed."""
    client = get_client()
    ensure_bucket(client, bucket)
    client.put_object(
        bucket,
        object_name,
        data=io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    print(f"☁️  MinIO → {bucket}/{object_name}")


# ── Download ──────────────────────────────────────────────────────────────────

def download(object_name: str, bucket: str = BUCKET) -> bytes:
    """Download an object from MinIO and return its raw bytes."""
    client = get_client()
    response = client.get_object(bucket, object_name)
    return response.read()


# ── Helpers por capa ──────────────────────────────────────────────────────────

def upload_raw(data: bytes, filename: str, content_type: str) -> None:
    upload(data, f"{RAW}/{filename}", content_type)


def upload_silver(data: bytes, filename: str) -> None:
    upload(data, f"{SILVER}/{filename}", "application/octet-stream")


def upload_gold(data: bytes, filename: str) -> None:
    upload(data, f"{GOLD}/{filename}", "application/octet-stream")


def download_raw(filename: str) -> bytes:
    return download(f"{RAW}/{filename}")


def download_silver(filename: str) -> bytes:
    return download(f"{SILVER}/{filename}")


def download_gold(filename: str) -> bytes:
    return download(f"{GOLD}/{filename}")