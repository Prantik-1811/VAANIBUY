import os
import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DATABASE_PATH = Path(
    os.getenv("VAANIBUY_DATABASE_PATH", ROOT_DIR / "data" / "vaanibuy.db")
)


def connect():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize():
    with connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS proposals (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                items_json TEXT NOT NULL,
                budget INTEGER,
                address TEXT NOT NULL,
                subtotal INTEGER NOT NULL,
                delivery_fee INTEGER NOT NULL,
                total INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS approvals (
                id TEXT PRIMARY KEY,
                proposal_id TEXT NOT NULL UNIQUE REFERENCES proposals(id),
                idempotency_key TEXT NOT NULL UNIQUE,
                approved INTEGER NOT NULL CHECK (approved = 1),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                proposal_id TEXT NOT NULL UNIQUE REFERENCES proposals(id),
                status TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS payments (
                id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL UNIQUE REFERENCES orders(id),
                amount INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
