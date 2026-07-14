"""
routes/units.py
Manajemen data unit PS3 (CRUD dasar).
"""

from flask import Blueprint, render_template, current_app, flash, redirect, url_for, request

units_bp = Blueprint("units", __name__)


@units_bp.route("/units")
def list_units():
    db = current_app.db_service
    units = db.list_units()
    return render_template("units.html", units=units)


@units_bp.route("/units/create", methods=["POST"])
def create_unit():
    db = current_app.db_service
    code = request.form.get("code", "").strip().upper()
    name = request.form.get("name", "").strip()
    condition = request.form.get("condition", "Baik").strip()
    price = request.form.get("price_per_day", "0").strip()

    if not code or not name:
        flash("Kode unit dan nama unit wajib diisi.", "warning")
        return redirect(url_for("units.list_units"))

    try:
        db.create_unit(code, name, condition, int(price))
        flash(f"Unit '{code}' berhasil ditambahkan.", "success")
    except Exception as e:
        flash(f"Gagal menambahkan unit: {e}", "danger")

    return redirect(url_for("units.list_units"))


@units_bp.route("/units/<int:unit_id>/status", methods=["POST"])
def update_status(unit_id):
    db = current_app.db_service
    status = request.form.get("status")
    db.update_unit_status(unit_id, status)
    flash("Status unit berhasil diperbarui.", "success")
    return redirect(url_for("units.list_units"))


@units_bp.route("/units/<int:unit_id>/delete", methods=["POST"])
def delete_unit(unit_id):
    db = current_app.db_service
    db.delete_unit(unit_id)
    flash("Unit berhasil dihapus.", "success")
    return redirect(url_for("units.list_units"))
