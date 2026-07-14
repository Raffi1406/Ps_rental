"""
routes/rentals.py
Manajemen transaksi sewa PS3. Setiap transaksi baru otomatis mendapat
folder khusus di Cloud Vault (S3) untuk menyimpan foto kondisi unit &
bukti pembayaran terkait transaksi tersebut.
"""

from datetime import datetime, date
from flask import Blueprint, render_template, current_app, flash, redirect, url_for, request
from services.s3_service import S3ServiceError

rentals_bp = Blueprint("rentals", __name__)


@rentals_bp.route("/rentals")
def list_rentals():
    db = current_app.db_service
    rentals = db.list_rentals()
    return render_template("rentals.html", rentals=rentals)


@rentals_bp.route("/rentals/new")
def new_rental_form():
    db = current_app.db_service
    units = [u for u in db.list_units() if u["status"] == "Tersedia"]
    customers = db.list_customers()
    return render_template("rental_form.html", units=units, customers=customers)


@rentals_bp.route("/rentals/create", methods=["POST"])
def create_rental():
    db = current_app.db_service
    unit_id = request.form.get("unit_id")
    customer_id = request.form.get("customer_id")
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")
    notes = request.form.get("notes", "").strip()

    if not all([unit_id, customer_id, start_date, end_date]):
        flash("Semua field wajib diisi.", "warning")
        return redirect(url_for("rentals.new_rental_form"))

    unit = db.get_unit(int(unit_id))
    if not unit:
        flash("Unit tidak ditemukan.", "danger")
        return redirect(url_for("rentals.new_rental_form"))

    d1 = datetime.strptime(start_date, "%Y-%m-%d").date()
    d2 = datetime.strptime(end_date, "%Y-%m-%d").date()
    days = max((d2 - d1).days, 1)
    total_price = days * unit["price_per_day"]

    root_prefix = current_app.config["VAULT_ROOT_PREFIX"]
    rental_id, vault_prefix = db.create_rental(
        int(unit_id), int(customer_id), start_date, end_date, total_price, notes, root_prefix
    )

    # Buat folder vault otomatis untuk transaksi ini
    s3 = current_app.s3_service
    try:
        s3.create_folder("", vault_prefix.rstrip("/"))
    except S3ServiceError as e:
        flash(f"Transaksi dibuat, tapi folder vault gagal dibuat otomatis: {e}", "warning")

    flash(f"Transaksi sewa #{rental_id} berhasil dibuat. Total: Rp {total_price:,}".replace(",", "."), "success")
    return redirect(url_for("rentals.detail", rental_id=rental_id))


@rentals_bp.route("/rentals/<int:rental_id>")
def detail(rental_id):
    db = current_app.db_service
    rental = db.get_rental(rental_id)
    if not rental:
        flash("Transaksi tidak ditemukan.", "danger")
        return redirect(url_for("rentals.list_rentals"))
    return render_template("rental_detail.html", rental=rental)


@rentals_bp.route("/rentals/<int:rental_id>/return", methods=["POST"])
def mark_returned(rental_id):
    db = current_app.db_service
    db.mark_returned(rental_id)
    flash("Unit ditandai sudah dikembalikan.", "success")
    return redirect(url_for("rentals.detail", rental_id=rental_id))
