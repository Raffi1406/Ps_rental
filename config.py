"""
config.py
Konfigurasi aplikasi PS Rental Cloud Vault.
Kredensial AWS & pengaturan lain diambil dari environment variable (.env).
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "ps-rental-cloud-vault-secret")

    # Kredensial AWS
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
    AWS_SESSION_TOKEN = os.environ.get("AWS_SESSION_TOKEN", "")
    AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-1")

    # Endpoint custom untuk emulator S3 lokal (LocalStack).
    # Kosongkan nilai ini jika ingin memakai AWS S3 asli.
    # Contoh untuk LocalStack: http://localhost:4566 (jalan lokal) atau
    # http://localstack:4566 (jalan lewat docker-compose, pakai nama service).
    AWS_ENDPOINT_URL = os.environ.get("AWS_ENDPOINT_URL", "")

    # Dipakai HANYA jika AWS_ENDPOINT_URL memakai hostname internal Docker
    # (mis. "http://localstack:4566") sehingga presigned URL yang dikirim ke
    # browser perlu ditukar ke host yang bisa diakses dari luar container
    # (mis. "http://localhost:4566"). Kosongkan jika menjalankan tanpa Docker.
    AWS_ENDPOINT_URL_PUBLIC = os.environ.get("AWS_ENDPOINT_URL_PUBLIC", "")

    # Bucket S3 khusus untuk "Cloud Vault" (foto kondisi unit PS3 & bukti pembayaran)
    VAULT_BUCKET = os.environ.get("VAULT_BUCKET", "")

    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_UPLOAD_MB", 100)) * 1024 * 1024
    PRESIGNED_URL_EXPIRE = int(os.environ.get("PRESIGNED_URL_EXPIRE", 3600))
    IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp", "svg"}

    # Lokasi database SQLite
    DATABASE_PATH = os.environ.get("DATABASE_PATH") or os.path.join(os.path.dirname(__file__), "rental.db")

    # Prefix folder S3 tempat semua data transaksi rental disimpan
    VAULT_ROOT_PREFIX = "rentals/"


def get_config():
    return Config
