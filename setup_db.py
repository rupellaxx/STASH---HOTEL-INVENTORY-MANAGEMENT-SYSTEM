#!/usr/bin/env python3
"""
setup_db.py
───────────
Run this ONCE before launching main.py.
Creates the `hotel_db` database, all tables, and default user accounts.

Requirements: XAMPP / MySQL running on localhost, user root, blank password.

Usage:
    python setup_db.py
"""

import sys
import mysql.connector
import hashlib


# ── Config ─────────────────────────────────────────────────────────────────
DB_HOST     = "localhost"
DB_USER     = "root"
DB_PASSWORD = ""
DB_NAME     = "hotel_db"


# ── Password helper (mirrors models/database.py) ───────────────────────────
def hash_password(plain: str) -> str:
    """SHA-256 via Python's built-in hashlib."""
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()


# ── DDL ────────────────────────────────────────────────────────────────────
TABLES = [
    # users ─────────────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS users (
        id          INT(11)      NOT NULL AUTO_INCREMENT,
        email       VARCHAR(255) NOT NULL,
        password    VARCHAR(255) NOT NULL COMMENT 'SHA-256 hash via hashlib',
        full_name   VARCHAR(255) NOT NULL,
        role        VARCHAR(50)  NOT NULL COMMENT 'admin | owner | department',
        department  VARCHAR(100) DEFAULT NULL,
        created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
        updated_at  DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        UNIQUE KEY uq_email (email),
        KEY idx_role (role)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # suppliers ─────────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS suppliers (
        id           INT(11)      NOT NULL AUTO_INCREMENT,
        name         VARCHAR(255) NOT NULL,
        contact_name VARCHAR(255) DEFAULT NULL,
        email        VARCHAR(255) DEFAULT NULL,
        phone        VARCHAR(64)  DEFAULT NULL,
        address      TEXT         DEFAULT NULL,
        created_at   DATETIME     DEFAULT CURRENT_TIMESTAMP,
        updated_at   DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        KEY idx_name (name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # items ─────────────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS items (
        id         INT(11)       NOT NULL AUTO_INCREMENT,
        name       VARCHAR(255)  NOT NULL,
        sku        VARCHAR(100)  DEFAULT NULL,
        unit       VARCHAR(50)   DEFAULT NULL,
        unit_cost  DECIMAL(12,2) DEFAULT 0.00,
        stock_qty  INT(11)       DEFAULT 0,
        min_stock  INT(11)       DEFAULT 10,
        category   VARCHAR(100)  DEFAULT 'General',
        created_at DATETIME      DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        KEY idx_name     (name),
        KEY idx_category (category),
        KEY idx_stock    (stock_qty)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # purchases ─────────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS purchases (
        id            INT(11)       NOT NULL AUTO_INCREMENT,
        supplier_id   INT(11)       DEFAULT NULL,
        expected_date DATE          DEFAULT NULL,
        total_amount  DECIMAL(12,2) DEFAULT 0.00,
        status        VARCHAR(32)   DEFAULT 'pending',
        created_by    VARCHAR(255)  DEFAULT NULL,
        created_at    DATETIME      DEFAULT CURRENT_TIMESTAMP,
        updated_at    DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        KEY idx_supplier (supplier_id),
        KEY idx_status   (status),
        KEY idx_created  (created_at),
        FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # purchase_items ────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS purchase_items (
        id                     INT(11)       NOT NULL AUTO_INCREMENT,
        purchase_id            INT(11)       NOT NULL,
        item_name              VARCHAR(255)  DEFAULT NULL,
        item_id                INT(11)       DEFAULT NULL,
        quantity               INT(11)       NOT NULL,
        unit_price             DECIMAL(12,2) NOT NULL,
        total                  DECIMAL(12,2) NOT NULL,
        created_at             DATETIME      DEFAULT CURRENT_TIMESTAMP,
        in_inventory           TINYINT(4)    DEFAULT 0,
        qty_added_to_inventory INT(11)       DEFAULT 0,
        PRIMARY KEY (id),
        KEY idx_purchase (purchase_id),
        KEY idx_item     (item_id),
        FOREIGN KEY (purchase_id) REFERENCES purchases(id)  ON DELETE CASCADE,
        FOREIGN KEY (item_id)     REFERENCES items(id)      ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # requests ──────────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS requests (
        id           INT(11)      NOT NULL AUTO_INCREMENT,
        department   VARCHAR(50)  NOT NULL,
        requested_by VARCHAR(100) NOT NULL,
        item_name    VARCHAR(255) NOT NULL,
        quantity     INT(11)      NOT NULL,
        unit         VARCHAR(50)  DEFAULT NULL,
        reason       TEXT         DEFAULT NULL,
        status       VARCHAR(20)  DEFAULT 'Pending',
        notes        TEXT         DEFAULT NULL,
        created_at   DATETIME     DEFAULT CURRENT_TIMESTAMP,
        updated_at   DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        KEY idx_dept   (department),
        KEY idx_status (status),
        KEY idx_created(created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # messages ──────────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS messages (
        id           INT(11)     NOT NULL AUTO_INCREMENT,
        sender_id    INT(11)     NOT NULL,
        recipient_id INT(11)     NOT NULL,
        category     VARCHAR(64) DEFAULT 'General',
        title        VARCHAR(255)DEFAULT NULL,
        body         TEXT        DEFAULT NULL,
        is_read      TINYINT(1)  DEFAULT 0,
        created_at   DATETIME    DEFAULT CURRENT_TIMESTAMP,
        updated_at   DATETIME    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        KEY idx_sender    (sender_id),
        KEY idx_recipient (recipient_id),
        KEY idx_is_read   (is_read),
        KEY idx_created   (created_at),
        FOREIGN KEY (sender_id)    REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (recipient_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # damages ───────────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS damages (
        id          INT(11)      NOT NULL AUTO_INCREMENT,
        item_id     INT(11)      NOT NULL,
        purchase_id INT(11)      DEFAULT NULL,
        category    VARCHAR(100) DEFAULT NULL,
        quantity    INT(11)      NOT NULL,
        reason      TEXT         DEFAULT NULL,
        status      VARCHAR(50)  DEFAULT 'reported',
        created_by  VARCHAR(255) DEFAULT NULL,
        created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        KEY idx_item    (item_id),
        KEY idx_created (created_at),
        FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # inventory_history ─────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS inventory_history (
        id            INT(11)     NOT NULL AUTO_INCREMENT,
        item_name     VARCHAR(255)NOT NULL,
        movement_type VARCHAR(50) NOT NULL
            COMMENT 'stock_in | distributed | adjustment | damage',
        quantity      INT(11)     NOT NULL,
        user_name     VARCHAR(100)NOT NULL,
        notes         TEXT        DEFAULT NULL,
        department    VARCHAR(100)DEFAULT NULL,
        created_at    DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        KEY idx_item_name     (item_name),
        KEY idx_movement_type (movement_type),
        KEY idx_created       (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
]

# ── Default seed data ──────────────────────────────────────────────────────
DEFAULT_USERS = [
    # (email, plain_password, full_name, role, department)
    ("admin@hotel.com",        "admin123", "Purchase Admin",       "admin",      None),
    ("owner@hotel.com",        "owner123", "Hotel Owner",          "owner",      None),
    ("housekeeping@hotel.com", "dept123",  "Housekeeping Manager", "department", "Housekeeping"),
    ("dining@hotel.com",       "dept123",  "Dining Manager",       "department", "Dining"),
    ("maintenance@hotel.com",  "dept123",  "Maintenance Manager",  "department", "Maintenance"),
]

DEFAULT_SUPPLIERS = [
    ("ABC Suppliers Inc.",  "Juan dela Cruz", "abc@suppliers.com",   "+63 912 000 0001", "Davao City"),
    ("XYZ Supplies Co.",    "Maria Santos",   "xyz@supplies.com",    "+63 912 000 0002", "Makati City"),
    ("Hotel Depot PH",      "Pedro Reyes",    "depot@hoteldph.com",  "+63 912 000 0003", "Cebu City"),
]

DEFAULT_ITEMS = [
    # (name, sku, unit, unit_cost, stock_qty, min_stock, category)
    ("Bath Towels",      "HK-001", "pcs",  250.00, 100, 20, "Housekeeping"),
    ("Bed Sheets",       "HK-002", "sets", 450.00,  80, 15, "Housekeeping"),
    ("Shampoo (50ml)",   "HK-003", "pcs",   35.00, 200, 50, "Housekeeping"),
    ("Soap Bar",         "HK-004", "pcs",   18.00, 300, 60, "Housekeeping"),
    ("Toilet Paper",     "HK-005", "rolls",  12.00, 400, 80, "Housekeeping"),
    ("Rice (50kg sack)", "DI-001", "sacks", 2400.00, 10,  3, "Dining"),
    ("Cooking Oil (5L)", "DI-002", "btls",  420.00, 20,  5, "Dining"),
    ("Table Napkins",    "DI-003", "packs",  60.00, 50, 10, "Dining"),
    ("Dishwashing Liquid","DI-004","btls",   85.00, 30,  8, "Dining"),
    ("Gloves (box)",     "MT-001", "boxes", 150.00, 15,  5, "Maintenance"),
    ("Light Bulbs (LED)","MT-002", "pcs",   120.00, 40, 10, "Maintenance"),
    ("Cleaning Rags",    "MT-003", "pcs",    25.00, 60, 15, "Maintenance"),
]


# ── Main setup function ────────────────────────────────────────────────────
def setup():
    print("\n" + "=" * 58)
    print("  STASH Hotel Inventory Management System")
    print("  Database Setup")
    print("=" * 58)

    try:
        conn = mysql.connector.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASSWORD
        )
        cur = conn.cursor()

        print(f"\n  ✔  Connected to MySQL at {DB_HOST}")

        # Create DB
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
            "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        cur.execute(f"USE `{DB_NAME}`")
        print(f"  ✔  Database '{DB_NAME}' ready")

        # Create tables
        for ddl in TABLES:
            cur.execute(ddl)
        print(f"  ✔  All tables created / verified ({len(TABLES)} tables)")

        # Seed users
        for email, plain_pw, full_name, role, dept in DEFAULT_USERS:
            hashed = hash_password(plain_pw)
            cur.execute(
                "INSERT IGNORE INTO users "
                "(email, password, full_name, role, department) "
                "VALUES (%s, %s, %s, %s, %s)",
                (email, hashed, full_name, role, dept),
            )
        conn.commit()
        print(f"  ✔  Default users seeded ({len(DEFAULT_USERS)} accounts)")

        # Seed suppliers
        for name, contact, email, phone, address in DEFAULT_SUPPLIERS:
            cur.execute(
                "INSERT IGNORE INTO suppliers "
                "(name, contact_name, email, phone, address) "
                "VALUES (%s, %s, %s, %s, %s)",
                (name, contact, email, phone, address),
            )
        conn.commit()
        print(f"  ✔  Default suppliers seeded ({len(DEFAULT_SUPPLIERS)} records)")

        # Seed items
        for name, sku, unit, cost, qty, min_s, cat in DEFAULT_ITEMS:
            cur.execute(
                "INSERT IGNORE INTO items "
                "(name, sku, unit, unit_cost, stock_qty, min_stock, category) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (name, sku, unit, cost, qty, min_s, cat),
            )
        conn.commit()
        print(f"  ✔  Default inventory items seeded ({len(DEFAULT_ITEMS)} items)")

        cur.close(); conn.close()

    except mysql.connector.Error as exc:
        print(f"\n  ✘  MySQL Error: {exc}")
        print("  Make sure XAMPP / MySQL is running and credentials are correct.")
        sys.exit(1)

    # ── Summary ───────────────────────────────────────────────────────────
    print("\n" + "─" * 58)
    print("  Default Login Accounts")
    print("─" * 58)
    print("  Role               Email                      Password")
    print("─" * 58)
    for email, pw, _, role, dept in DEFAULT_USERS:
        role_label = f"{role.title()}" + (f" ({dept})" if dept else "")
        print(f"  {role_label:<18} {email:<26} {pw}")
    print("─" * 58)
    print("\n  ✔  Setup complete!  Run:  python main.py\n")


if __name__ == "__main__":
    setup()