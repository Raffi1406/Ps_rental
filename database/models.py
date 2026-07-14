"""
database/models.py
Layer database sederhana memakai sqlite3 murni (tanpa ORM berat) supaya
mudah dipahami dan tidak butuh dependency tambahan.

Tabel:
- units      : data unit PS3 yang disewakan
- customers  : data pelanggan
- rentals    : data transaksi sewa (menghubungkan unit + customer)
"""

import os
import sqlite3
from datetime import datetime


def get_connection(db_path):
    folder = os.path.dirname(db_path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path):
    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            condition TEXT NOT NULL DEFAULT 'Baik',
            price_per_day INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Tersedia',
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            address TEXT,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS rentals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            actual_return_date TEXT,
            status TEXT NOT NULL DEFAULT 'Aktif',
            total_price INTEGER NOT NULL DEFAULT 0,
            vault_prefix TEXT NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (unit_id) REFERENCES units (id),
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    """)

    conn.commit()

    # Seed data contoh supaya aplikasi tidak kosong saat pertama dijalankan
    cur.execute("SELECT COUNT(*) AS c FROM units")
    if cur.fetchone()["c"] == 0:
        now = datetime.now().isoformat()
        sample_units = [
            ("PS3-001", "PlayStation 3 Slim 500GB", "Baik", 35000, "Tersedia", now),
            ("PS3-002", "PlayStation 3 Super Slim 250GB", "Baik", 30000, "Tersedia", now),
            ("PS3-003", "PlayStation 3 Fat 320GB", "Perlu Servis Stik", 25000, "Maintenance", now),
        ]
        cur.executemany(
            "INSERT INTO units (code, name, condition, price_per_day, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            sample_units,
        )
        conn.commit()

    conn.close()
