"""
services/db_service.py
Lapisan service untuk operasi CRUD terhadap database rental (units, customers, rentals).
Dipisah dari routes supaya query terpusat & mudah diuji.
"""

from datetime import datetime, date
from database.models import get_connection


class DBService:
    def __init__(self, db_path):
        self.db_path = db_path

    def _conn(self):
        return get_connection(self.db_path)

    # ------------------------------------------------------------------
    # UNITS
    # ------------------------------------------------------------------
    def list_units(self):
        conn = self._conn()
        rows = conn.execute("SELECT * FROM units ORDER BY code").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_unit(self, unit_id):
        conn = self._conn()
        row = conn.execute("SELECT * FROM units WHERE id = ?", (unit_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def create_unit(self, code, name, condition, price_per_day):
        conn = self._conn()
        conn.execute(
            "INSERT INTO units (code, name, condition, price_per_day, status, created_at) "
            "VALUES (?, ?, ?, ?, 'Tersedia', ?)",
            (code, name, condition, price_per_day, datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()

    def update_unit_status(self, unit_id, status):
        conn = self._conn()
        conn.execute("UPDATE units SET status = ? WHERE id = ?", (status, unit_id))
        conn.commit()
        conn.close()

    def delete_unit(self, unit_id):
        conn = self._conn()
        conn.execute("DELETE FROM units WHERE id = ?", (unit_id,))
        conn.commit()
        conn.close()

    # ------------------------------------------------------------------
    # CUSTOMERS
    # ------------------------------------------------------------------
    def list_customers(self):
        conn = self._conn()
        rows = conn.execute("SELECT * FROM customers ORDER BY name").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_customer(self, customer_id):
        conn = self._conn()
        row = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def create_customer(self, name, phone, email, address):
        conn = self._conn()
        cur = conn.execute(
            "INSERT INTO customers (name, phone, email, address, created_at) VALUES (?, ?, ?, ?, ?)",
            (name, phone, email, address, datetime.now().isoformat()),
        )
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return new_id

    def delete_customer(self, customer_id):
        conn = self._conn()
        conn.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
        conn.commit()
        conn.close()

    # ------------------------------------------------------------------
    # RENTALS
    # ------------------------------------------------------------------
    def list_rentals(self):
        conn = self._conn()
        rows = conn.execute("""
            SELECT r.*, u.code AS unit_code, u.name AS unit_name, c.name AS customer_name
            FROM rentals r
            JOIN units u ON u.id = r.unit_id
            JOIN customers c ON c.id = r.customer_id
            ORDER BY r.created_at DESC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_rental(self, rental_id):
        conn = self._conn()
        row = conn.execute("""
            SELECT r.*, u.code AS unit_code, u.name AS unit_name, u.price_per_day,
                   c.name AS customer_name, c.phone AS customer_phone
            FROM rentals r
            JOIN units u ON u.id = r.unit_id
            JOIN customers c ON c.id = r.customer_id
            WHERE r.id = ?
        """, (rental_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def create_rental(self, unit_id, customer_id, start_date, end_date, total_price, notes, vault_root_prefix):
        conn = self._conn()
        cur = conn.execute(
            "INSERT INTO rentals (unit_id, customer_id, start_date, end_date, status, "
            "total_price, vault_prefix, notes, created_at) VALUES (?, ?, ?, ?, 'Aktif', ?, ?, ?, ?)",
            (unit_id, customer_id, start_date, end_date, total_price, "PLACEHOLDER", notes, datetime.now().isoformat()),
        )
        rental_id = cur.lastrowid
        # Folder vault dibuat unik per transaksi: rentals/{id}-{kode_unit}/
        unit = conn.execute("SELECT code FROM units WHERE id = ?", (unit_id,)).fetchone()
        vault_prefix = f"{vault_root_prefix}{rental_id}-{unit['code']}/"
        conn.execute("UPDATE rentals SET vault_prefix = ? WHERE id = ?", (vault_prefix, rental_id))
        conn.execute("UPDATE units SET status = 'Disewa' WHERE id = ?", (unit_id,))
        conn.commit()
        conn.close()
        return rental_id, vault_prefix

    def mark_returned(self, rental_id):
        conn = self._conn()
        rental = conn.execute("SELECT unit_id FROM rentals WHERE id = ?", (rental_id,)).fetchone()
        conn.execute(
            "UPDATE rentals SET status = 'Selesai', actual_return_date = ? WHERE id = ?",
            (date.today().isoformat(), rental_id),
        )
        if rental:
            conn.execute("UPDATE units SET status = 'Tersedia' WHERE id = ?", (rental["unit_id"],))
        conn.commit()
        conn.close()

    def dashboard_stats(self):
        conn = self._conn()
        total_units = conn.execute("SELECT COUNT(*) c FROM units").fetchone()["c"]
        available_units = conn.execute("SELECT COUNT(*) c FROM units WHERE status = 'Tersedia'").fetchone()["c"]
        rented_units = conn.execute("SELECT COUNT(*) c FROM units WHERE status = 'Disewa'").fetchone()["c"]
        active_rentals = conn.execute("SELECT COUNT(*) c FROM rentals WHERE status = 'Aktif'").fetchone()["c"]
        total_customers = conn.execute("SELECT COUNT(*) c FROM customers").fetchone()["c"]
        total_revenue = conn.execute(
            "SELECT COALESCE(SUM(total_price), 0) s FROM rentals WHERE status = 'Selesai'"
        ).fetchone()["s"]
        conn.close()
        return {
            "total_units": total_units,
            "available_units": available_units,
            "rented_units": rented_units,
            "active_rentals": active_rentals,
            "total_customers": total_customers,
            "total_revenue": total_revenue,
        }
