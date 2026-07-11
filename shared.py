import json
import os
import re
import sqlite3 as sql
from contextlib import contextmanager
from datetime import date, datetime, timedelta

STORAGE_DB = 'storage.db'
ASSETS_DB = 'assets.db'
SUBSCRIPTIONS_DB = 'subscriptions.db'
LOANS_DB = 'loans.db'
CONFIG_FILE = 'user_config.json'

VERSION = '1.8'

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
    LOANS_DB: """
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY,
            name TEXT,
            payment_amount REAL,
            frequency TEXT,
            term_count INTEGER,
            total_loan_value REAL,
            remaining_balance REAL,
            first_due_date TEXT,
            next_due_date TEXT,
            last_payment_at TEXT,
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


def init_db(db_name=None):
    if db_name is None:
        db_name = STORAGE_DB
    return _initialize_database(db_name, _DATABASE_SCHEMAS[STORAGE_DB])


def init_assets_db(db_name=None):
    if db_name is None:
        db_name = ASSETS_DB
    return _initialize_database(db_name, _DATABASE_SCHEMAS[ASSETS_DB])


def init_subscriptions_db(db_name=None):
    if db_name is None:
        db_name = SUBSCRIPTIONS_DB
    return _initialize_database(db_name, _DATABASE_SCHEMAS[SUBSCRIPTIONS_DB])


def init_loans_db(db_name=None):
    if db_name is None:
        db_name = LOANS_DB
    return _initialize_database(db_name, _DATABASE_SCHEMAS[LOANS_DB])


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
    elif db_name == LOANS_DB:
        conn = init_loans_db(db_name)
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


# ============================================================================
# Date Parsing Utilities
# ============================================================================

def parse_date(value, date_format='%d-%m-%Y'):
    """Parse a date string in DD-MM-YYYY format (or custom format)."""
    try:
        if not isinstance(value, str):
            return None
        return datetime.strptime(value, date_format).date()
    except (ValueError, TypeError):
        return None


def parse_date_ddmmyyyy(value):
    """Parse a date string in DD-MM-YYYY format."""
    try:
        if not isinstance(value, str):
            return None
        if not re.fullmatch(r"\d{2}-\d{2}-\d{4}", value):
            return None
        day_str, month_str, year_str = value.split('-')
        day = int(day_str)
        month = int(month_str)
        year = int(year_str)
        return date(year, month, day)
    except ValueError:
        return None


# ============================================================================
# Date Calculation Utilities
# ============================================================================

def calculate_next_due_date(current_due_date, frequency):
    """Calculate the next due date based on frequency.
    
    Args:
        current_due_date: A date object
        frequency: One of 'yearly', 'monthly', 'weekly', 'daily'
    
    Returns:
        A date object representing the next due date, or None if frequency is invalid
    """
    if not isinstance(current_due_date, date):
        return None

    freq = (frequency or '').strip().lower()
    
    if freq == 'yearly':
        year = current_due_date.year + 1
        try:
            return date(year, current_due_date.month, current_due_date.day)
        except ValueError:
            return date(year, 3, 1)

    if freq == 'monthly':
        month = current_due_date.month + 1
        year = current_due_date.year
        while month > 12:
            month -= 12
            year += 1
        try:
            return date(year, month, current_due_date.day)
        except ValueError:
            # Handle end-of-month cases
            if month > 12:
                return date(year + 1, 1, 1)
            return date(year, month + 1, 1)

    if freq == 'weekly':
        return current_due_date + timedelta(days=7)

    if freq == 'daily':
        return current_due_date + timedelta(days=1)

    return None


# ============================================================================
# Table Formatting Utilities
# ============================================================================

def format_table(headers, rows, border_char='-', padding=1):
    """Format data as a nicely aligned table.
    
    Args:
        headers: List of header strings
        rows: List of tuples/lists containing row data
        border_char: Character to use for borders (default: '-')
        padding: Number of spaces to pad each cell (default: 1)
    
    Returns:
        A formatted string representation of the table
    """
    if not rows:
        return "No data available."
    
    # Calculate column widths
    col_widths = []
    for i, header in enumerate(headers):
        max_width = len(header)
        for row in rows:
            if i < len(row):
                cell_value = str(row[i]) if row[i] is not None else ''
                max_width = max(max_width, len(cell_value))
        col_widths.append(max_width + padding * 2)
    
    # Build format string
    format_str = ' | '.join([f"{{:<{w}}}" for w in col_widths])
    
    # Build separator line
    separator = border_char * (sum(col_widths) + len(col_widths) - 1)
    
    # Format header
    header_row = format_str.format(*headers)
    
    # Format rows
    formatted_rows = []
    for row in rows:
        formatted_row = format_str.format(*[str(cell) if cell is not None else '' for cell in row])
        formatted_rows.append(formatted_row)
    
    # Combine all parts
    result = [header_row, separator] + formatted_rows
    return '\n'.join(result)


def print_table(headers, rows, border_char='-', padding=1):
    """Print data as a nicely formatted table.
    
    Args:
        headers: List of header strings
        rows: List of tuples/lists containing row data
        border_char: Character to use for borders (default: '-')
        padding: Number of spaces to pad each cell (default: 1)
    """
    print(format_table(headers, rows, border_char, padding))


def format_currency(amount, currency_symbol='LKR '):
    """Format a numeric amount as currency.
    
    Args:
        amount: Numeric value to format
        currency_symbol: Symbol to prepend (default: 'LKR ')
    
    Returns:
        Formatted currency string
    """
    if amount is None:
        return ''
    return f"{currency_symbol}{abs(float(amount)):.2f}"


def format_transaction_type(transaction_type):
    """Format transaction type for display."""
    if transaction_type is None:
        return ''
    return transaction_type.lower()
