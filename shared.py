import json
import os
import sqlite3 as sql

STORAGE_DB = 'storage.db'
ASSETS_DB = 'assets.db'
SUBSCRIPTIONS_DB = 'subscriptions.db'
CONFIG_FILE = 'user_config.json'

VERSION = '1.4'

EXPENSE_CATEGORIES = {
    '1': 'Entertainment',
    '2': 'Food',
    '3': 'Asset Purchase',
    '4': 'Travel',
    '5': 'Other',
}

_DATABASE_SCHEMAS = {
    STORAGE_DB: """
        CREATE TABLE IF NOT EXISTS storage (
            id INTEGER PRIMARY KEY,
            amount REAL,
            category TEXT,
            type TEXT,
            created_at TEXT
        )
    """,
    ASSETS_DB: """
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY,
            name TEXT,
            asset_type TEXT,
            amount REAL,
            created_at TEXT
        )
    """,
    SUBSCRIPTIONS_DB: """
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY,
            name TEXT,
            amount REAL,
            frequency TEXT,
            start_date TEXT,
            next_due_date TEXT,
            last_processed_at TEXT,
            category TEXT,
            status TEXT,
            created_at TEXT
        )
    """,
}


def safe_input(prompt):
    try:
        return input(prompt)
    except KeyboardInterrupt:
        raise SystemExit(0)


def _initialize_database(db_name, schema):
    conn = sql.connect(db_name)
    conn.execute(schema)
    conn.commit()
    return conn


def init_db(db_name=STORAGE_DB):
    return _initialize_database(db_name, _DATABASE_SCHEMAS[STORAGE_DB])


def init_assets_db(db_name=ASSETS_DB):
    return _initialize_database(db_name, _DATABASE_SCHEMAS[ASSETS_DB])


def init_subscriptions_db(db_name=SUBSCRIPTIONS_DB):
    return _initialize_database(db_name, _DATABASE_SCHEMAS[SUBSCRIPTIONS_DB])


def load_user_name(config_file=CONFIG_FILE):
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            name = data.get('name')
            if name and isinstance(name, str):
                return name
        except Exception:
            return None
    return None


def save_user_name(name, config_file=CONFIG_FILE):
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump({'name': name}, f)
        return True
    except Exception:
        return False
