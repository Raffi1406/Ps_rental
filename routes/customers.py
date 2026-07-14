"""
routes/customers.py
Manajemen data pelanggan.
"""

from flask import Blueprint, render_template, current_app, flash, redirect, url_for, request

customers_bp = Blueprint("customers", __name__)


@customers_bp.route("/customers")
def list_customers():
    db = current_app.db_service
    customers = db.list_customers()
    return render_template("customers.html", customers=customers)


@customers_bp.route("/customers/create", methods=["POST"])
def create_customer():
    db = current_app.db_service
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    address = request.form.get("address", "").strip()

    if not name or not phone:
        flash("Nama dan nomor telepon pelanggan wajib diisi.", "warning")
        return redirect(url_for("customers.list_customers"))

    db.create_customer(name, phone, email, address)
    flash(f"Pelanggan '{name}' berhasil ditambahkan.", "success")
    return redirect(url_for("customers.list_customers"))


@customers_bp.route("/customers/<int:customer_id>/delete", methods=["POST"])
def delete_customer(customer_id):
    db = current_app.db_service
    db.delete_customer(customer_id)
    flash("Pelanggan berhasil dihapus.", "success")
    return redirect(url_for("customers.list_customers"))
