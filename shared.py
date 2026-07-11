import json
import os
import sqlite3 as sql
from contextlib import contextmanager

STORAGE_DB = 'storage.db'
ASSETS_DB = 'assets.db'
SUBSCRIPTIONS_DB = 'subscriptions.db'
CONFIG_FILE = 'user_config.json'

VERSION = '1.6'

EXPENSE_CATEGORIES = {
    '1': 'Entertainment',
    '2': 'Food',
    '3': 'Asset Purchase',
    '4': 'Travel',
    '5': 'Bank Charge',
    '6': 'Utilities',
    '7': 'Health and Fitness',
    '8': 'Housing',
    '9': 'Loan Payments',
    '10': 'Other',
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


@contextmanager
def db_cursor(db_name, commit=False):
    if db_name == STORAGE_DB:
        conn = init_db(db_name)
    elif db_name == ASSETS_DB:
        conn = init_assets_db(db_name)
    elif db_name == SUBSCRIPTIONS_DB:
        conn = init_subscriptions_db(db_name)
    else:
        conn = sql.connect(db_name)

    cursor = conn.cursor()
    try:
        yield cursor
        if commit:
            conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_choice(prompt, valid_choices, error_msg=None, input_fn=safe_input):
    while True:
        choice = input_fn(prompt).strip()
        if choice in valid_choices:
            return choice
        if error_msg:
            print(error_msg)
        else:
            choices_str = ", ".join(valid_choices[:-1]) + ", or " + valid_choices[-1] if len(valid_choices) > 1 else valid_choices[0]
            print(f"Invalid choice. Please enter {choices_str}.")


def get_optional_choice(prompt, choices_map, default, err_msg=None, input_fn=safe_input):
    while True:
        choice = input_fn(prompt).strip()
        if not choice:
            return default
        choice_lower = choice.lower()
        if choice in choices_map:
            return choices_map[choice]
        if choice_lower in choices_map:
            return choices_map[choice_lower]
        if err_msg:
            print(err_msg)
        else:
            print("Invalid choice. Please try again.")


def get_confirmation(prompt, input_fn=safe_input):
    while True:
        choice = input_fn(prompt).strip().lower()
        if choice in {'y', 'yes'}:
            return True
        if choice in {'n', 'no'}:
            return False
        print("Invalid choice. Please enter y or n.")


def get_positive_float(prompt, err_invalid="Invalid amount. Please enter a valid number.", err_range="Amount must be greater than 0.", input_fn=safe_input):
    while True:
        val_input = input_fn(prompt).strip()
        try:
            val = float(val_input)
        except ValueError:
            print(err_invalid)
            continue
        if val <= 0:
            print(err_range)
            continue
        return val


def get_optional_positive_float(prompt, default, err_invalid="Invalid amount. Please enter a valid number.", err_range="Amount must be greater than 0.", input_fn=safe_input):
    while True:
        val_input = input_fn(prompt).strip()
        if not val_input:
            return default
        try:
            val = float(val_input)
        except ValueError:
            print(err_invalid)
            continue
        if val <= 0:
            print(err_range)
            continue
        return val


def get_int_input(prompt, err_invalid="Invalid ID. Please enter a valid number.", validator=None, err_validator=None, input_fn=safe_input):
    while True:
        val_input = input_fn(prompt).strip()
        try:
            val = int(val_input)
        except ValueError:
            print(err_invalid)
            continue
        if validator and not validator(val):
            if err_validator:
                print(err_validator)
            continue
        return val


def get_optional_date(prompt, default, parser, format_str='%d-%m-%Y', err_msg="Invalid date. Please use DD-MM-YYYY with a valid day, month, and year.", input_fn=safe_input):
    while True:
        val_input = input_fn(prompt).strip()
        if not val_input:
            return default
        parsed = parser(val_input)
        if parsed is not None:
            return parsed.strftime(format_str)
        print(err_msg)
