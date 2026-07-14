"""
routes/dashboard.py
Halaman utama: ringkasan bisnis rental (unit, penyewaan aktif, pelanggan)
sekaligus ringkasan penggunaan Cloud Vault (S3).
"""

from flask import Blueprint, render_template, current_app, flash
from services.s3_service import S3ServiceError
from utils.helper import format_bytes, format_rupiah

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    db = current_app.db_service
    s3 = current_app.s3_service

    stats = db.dashboard_stats()
    stats["total_revenue_human"] = format_rupiah(stats["total_revenue"])

    vault_info = None
    try:
        vault_info = s3.get_bucket_info()
        vault_info["total_size_human"] = format_bytes(vault_info["total_size"])
    except S3ServiceError as e:
        flash(f"Cloud Vault belum terhubung: {e}", "warning")

    recent_rentals = db.list_rentals()[:5]

    return render_template(
        "dashboard.html", stats=stats, vault_info=vault_info, recent_rentals=recent_rentals
    )
