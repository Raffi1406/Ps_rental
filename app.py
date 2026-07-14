"""
app.py
Entry point aplikasi PS Rental Cloud Vault.

Menjalankan:
    python app.py
lalu buka http://localhost:5000
"""

from flask import Flask
from config import get_config
from database.models import init_db
from services.db_service import DBService
from services.s3_service import S3Service

from routes.dashboard import dashboard_bp
from routes.units import units_bp
from routes.customers import customers_bp
from routes.rentals import rentals_bp
from routes.vault import vault_bp


def create_app():
    app = Flask(__name__)
    cfg = get_config()
    app.config.from_object(cfg)

    # Inisialisasi database SQLite (otomatis membuat tabel + seed data contoh)
    init_db(cfg.DATABASE_PATH)
    app.db_service = DBService(cfg.DATABASE_PATH)

    # Inisialisasi S3Service ("Cloud Vault")
    app.s3_service = S3Service(cfg)

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(units_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(rentals_bp)
    app.register_blueprint(vault_bp)

    from utils.helper import format_bytes, format_rupiah
    app.jinja_env.filters["filesize"] = format_bytes
    app.jinja_env.filters["rupiah"] = format_rupiah

    # Pastikan bucket vault ada (dibuat otomatis jika belum ada).
    # Dibungkus try/except supaya aplikasi tetap bisa start meski kredensial
    # AWS belum diisi (misalnya saat build image Docker).
    try:
        app.s3_service.ensure_bucket_exists()
    except Exception:
        pass

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
