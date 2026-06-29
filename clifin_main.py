import sqlite3 as sql
from datetime import datetime
import csv


def init_db():
    conn = sql.connect('storage.db')
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS storage (
        id INTEGER PRIMARY KEY,
        amount REAL,
        category TEXT,
        type TEXT,
        created_at TEXT
    )
    """)
    conn.commit()
    return conn


def data_write(amount, category, transaction_type):
    print("\nConnecting to database...")
    conn = init_db()
    c = conn.cursor()

    print("Database connected...")

    normalized_type = transaction_type.lower()
    if normalized_type == 'income':
        signed_amount = abs(amount)
    elif normalized_type == 'expense':
        signed_amount = -abs(amount)
    else:
        signed_amount = amount

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute(
        "INSERT INTO storage (amount, category, type, created_at) VALUES (?, ?, ?, ?)",
        (signed_amount, category, normalized_type, created_at)
    )

    conn.commit()
    print("Completed writing to database successfully!")
    conn.close()


def data_entry():
    while True:
        current_year = datetime.now().year
        current_month = datetime.now().month
        month_name = datetime(current_year, current_month, 1).strftime("%B")

        conn = init_db()
        c = conn.cursor()
        month_filter = f"{current_year:04d}-{current_month:02d}-%"
        c.execute(
            "SELECT amount, category, type FROM storage WHERE created_at LIKE ?",
            (month_filter,)
        )
        rows = c.fetchall()
        conn.close()

        expense_totals = {}
        total_expenses = 0.0
        for amount, category, transaction_type in rows:
            if transaction_type.lower() == 'expense':
                display_amount = abs(amount)
                expense_totals[category] = expense_totals.get(category, 0.0) + display_amount
                total_expenses += display_amount

        print("\nQuick Summary:")
        print(f"You have spent LKR {total_expenses:.2f} in {month_name}.")
        if expense_totals:
            top_category, top_amount = max(expense_totals.items(), key=lambda item: item[1])
            print(f"Top expense category: {top_category} (Amount: {top_amount:.2f})")
        else:
            print("Top expense category: None")

        print("\nTransaction Type")
        print("1. Income")
        print("2. Expense")

        while True:
            type_choice = input("Enter transaction type code (1 or 2): ").strip()
            if type_choice == '1':
                transaction_type = 'income'
                break
            if type_choice == '2':
                transaction_type = 'expense'
                break
            print("Invalid choice. Please enter 1 for income or 2 for expense.")

        if transaction_type == 'income':
            categories = {
                '1': 'Salary',
                '2': 'Gift',
                '3': 'Bonus',
                '4': 'Freelance',
                '5': 'Other'
            }
        else:
            categories = {
                '1': 'Entertainment',
                '2': 'Food',
                '3': 'Stationary',
                '4': 'Travel',
                '5': 'Other'
            }

        print("\nSelect a category:")
        for code, name in categories.items():
            print(f"{code}. {name}")

        while True:
            category_choice = input("Enter category code: ").strip()
            if category_choice in categories:
                category = categories[category_choice]
                break
            print("Invalid category code. Please enter one of the listed options.")

        while True:
            amount_input = input("Enter amount: ").strip()
            try:
                amount = float(amount_input)
            except ValueError:
                print("Invalid amount. Please enter a valid number.")
                continue

            if amount <= 0:
                print("Amount must be greater than 0.")
                continue

            break

        data_write(amount, category, transaction_type)

        while True:
            stop_choice = input("Do you want to add another entry? (y/n): ").strip().lower()
            if stop_choice in {'y', 'yes'}:
                break
            if stop_choice in {'n', 'no'}:
                return
            print("Invalid choice. Please enter y or n.")


def export_to_csv(rows, year, month):
    """Export transaction data to CSV file"""
    month_name = datetime(year, month, 1).strftime("%B")
    filename = f"transactions_{year}_{month:02d}_{month_name}.csv"
    
    try:
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['ID', 'Date', 'Type', 'Category', 'Amount']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for record_id, amount, category, transaction_type, created_at in rows:
                writer.writerow({
                    'ID': record_id,
                    'Date': created_at,
                    'Type': transaction_type,
                    'Category': category,
                    'Amount': f"{amount:.2f}"
                })
        
        print(f"Data exported successfully to {filename}")
        return True
    except Exception as e:
        print(f"Error exporting to CSV: {e}")
        return False


def data_read():
    print("\nFinancial Records Reader")

    while True:
        year_input = input("Enter year: ").strip()
        try:
            year = int(year_input)
        except ValueError:
            print("Invalid year. Please enter a valid number.")
            continue

        if year > 0:
            break
        print("Invalid year. Please enter a valid number.")

    while True:
        month_input = input("Enter month number (1-12): ").strip()
        try:
            month = int(month_input)
        except ValueError:
            print("Invalid month. Please enter a number from 1 to 12.")
            continue

        if 1 <= month <= 12:
            break
        print("Invalid month. Please enter a number from 1 to 12.")

    while True:
        print("\nChoose report type:")
        print("1. Summary")
        print("2. Raw data")
        print("3. Both")
        report_choice = input("Enter choice (1, 2, or 3): ").strip()
        if report_choice in {'1', '2', '3'}:
            break
        print("Invalid choice. Please enter 1, 2, or 3.")

    month_name = datetime(year, month, 1).strftime("%B")
    month_filter = f"{year:04d}-{month:02d}-%"

    conn = init_db()
    c = conn.cursor()

    c.execute(
        "SELECT id, amount, category, type, created_at FROM storage WHERE created_at LIKE ? ORDER BY created_at",
        (month_filter,)
    )
    rows = c.fetchall()
    conn.close()

    if not rows:
        print(f"No records found for {month_name} {year}.")
        return

    if report_choice in {'1', '3'}:
        income_totals = {}
        expense_totals = {}
        total_income = 0.0
        total_expenses = 0.0

        for _, amount, category, transaction_type, _ in rows:
            normalized_type = transaction_type.lower()
            display_amount = abs(amount)
            if normalized_type == 'income':
                income_totals[category] = income_totals.get(category, 0.0) + display_amount
                total_income += display_amount
            elif normalized_type == 'expense':
                expense_totals[category] = expense_totals.get(category, 0.0) + display_amount
                total_expenses += display_amount

        print(f"\nSummary for {month_name} {year}")
        print("Income:")
        if income_totals:
            for category, total in sorted(income_totals.items()):
                print(f"- {category}: {total:.2f}")
        else:
            print("- None")
        print(f"Total income: {total_income:.2f}")

        print("\nExpenses:")
        if expense_totals:
            for category, total in sorted(expense_totals.items()):
                print(f"- {category}: {total:.2f}")
        else:
            print("- None")
        print(f"Total expenses: {total_expenses:.2f}")
        print(f"Net: {total_income - total_expenses:.2f}")

    if report_choice in {'2', '3'}:
        print(f"\nRaw data for {month_name} {year}")
        print(f"{'ID':<3} | {'Date':<19} | {'Type':<7} | {'Category':<12} | {'Amount':>10}")
        print("-" * 72)
        for record_id, amount, category, transaction_type, created_at in rows:
            print(f"{record_id:<3} | {created_at:<19} | {transaction_type:<7} | {category:<12} | {amount:>10.2f}")
        
        while True:
            export_choice = input("\nWould you like to export this data as CSV? (y/n): ").strip().lower()
            if export_choice in {'y', 'yes'}:
                export_to_csv(rows, year, month)
                break
            elif export_choice in {'n', 'no'}:
                break
            else:
                print("Invalid choice. Please enter y or n.")


if __name__ == '__main__':
    print("CliFin - Command Line Financial Tracker")
    while True:
        print("\nMain Menu")
        print("1. Enter data")
        print("2. View summary")
        print("3. Exit")

        choice = input("Choose an option (1, 2, or 3): ").strip()

        if choice == '1':
            data_entry()
        elif choice == '2':
            data_read()
        elif choice == '3':
            print("Thank you for using CliFin!")
            print("Created by Lochana, with help from Copilot.")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

