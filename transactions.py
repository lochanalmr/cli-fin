import csv
from datetime import datetime

from shared import EXPENSE_CATEGORIES, init_db, safe_input


def _normalize_transaction_amount(amount, transaction_type):
    normalized_type = (transaction_type or '').lower()
    if normalized_type == 'income':
        return abs(amount)
    if normalized_type == 'expense':
        return -abs(amount)
    return amount


def _get_transaction_categories(transaction_type):
    if transaction_type == 'income':
        return {
            '1': 'Salary',
            '2': 'Gift',
            '3': 'Interest',
            '4': 'Reversal',
            '5': 'Other'
        }
    return EXPENSE_CATEGORIES


def data_write(amount, category, transaction_type):
    conn = init_db()
    c = conn.cursor()

    normalized_type = transaction_type.lower()
    signed_amount = _normalize_transaction_amount(amount, normalized_type)
    stored_category = category

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute(
        "INSERT INTO storage (amount, category, type, created_at) VALUES (?, ?, ?, ?)",
        (signed_amount, stored_category, normalized_type, created_at)
    )

    conn.commit()
    conn.close()
    print("Transaction added successfully.")


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
            type_choice = safe_input("Enter transaction type code (1 or 2): ").strip()
            if type_choice == '1':
                transaction_type = 'income'
                break
            if type_choice == '2':
                transaction_type = 'expense'
                break
            print("Invalid choice. Please enter 1 for income or 2 for expense.")

        categories = _get_transaction_categories(transaction_type)

        print("\nSelect a category:")
        for code, name in categories.items():
            print(f"{code}. {name}")

        while True:
            category_choice = safe_input("Enter category code: ").strip()
            if category_choice in categories:
                category = categories[category_choice]
                break
            print("Invalid category code. Please enter one of the listed options.")

        while True:
            amount_input = safe_input("Enter amount: ").strip()
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
            stop_choice = safe_input("Do you want to add another entry? (y/n): ").strip().lower()
            if stop_choice in {'y', 'yes'}:
                break
            if stop_choice in {'n', 'no'}:
                return
            print("Invalid choice. Please enter y or n.")


def _display_transaction_rows(rows):
    if not rows:
        print("No transactions found.")
        return False

    print("\nAvailable transactions")
    print(f"{'ID':<3} | {'Value':>10} | {'Type':<7} | {'Category':<12}")
    print("-" * 44)
    for record_id, amount, category, transaction_type, _ in rows:
        print(f"{record_id:<3} | {abs(amount):>10.2f} | {transaction_type:<7} | {category:<12}")
    return True


def _show_selected_transaction(transaction):
    record_id, amount, category, transaction_type, _ = transaction
    print("\nSelected transaction details")
    print(f"Selected transaction id: {record_id}")
    print(f"Transaction value: {abs(amount):.2f}")
    print(f"Transaction type: {transaction_type.lower()}")
    print(f"Transaction category: {category}")


def _fetch_transactions(filter_type=None, filter_value=None):
    conn = init_db()
    c = conn.cursor()
    query = "SELECT id, amount, category, type, created_at FROM storage"
    params = []

    if filter_type == 'year':
        query += " WHERE created_at LIKE ?"
        params.append(f"{filter_value:04d}-%")
    elif filter_type == 'month':
        year, month = filter_value
        query += " WHERE created_at LIKE ?"
        params.append(f"{year:04d}-{month:02d}-%")
    elif filter_type == 'day':
        year, month, day = filter_value
        query += " WHERE created_at LIKE ?"
        params.append(f"{year:04d}-{month:02d}-{day:02d}%")

    query += " ORDER BY created_at"
    c.execute(query, tuple(params))
    rows = c.fetchall()
    conn.close()
    return rows


def manage_transaction():
    print("\nManage transaction")

    while True:
        view_choice = safe_input("Would you like to (1) view all transactions or (2) filter transactions? ").strip()
        if view_choice == '1':
            rows = _fetch_transactions()
            break
        if view_choice == '2':
            while True:
                filter_choice = safe_input("Filter by (1) year, (2) month, or (3) day? ").strip()
                if filter_choice == '1':
                    while True:
                        year_input = safe_input("Enter year: ").strip()
                        try:
                            year = int(year_input)
                        except ValueError:
                            print("Invalid year. Please enter a valid number.")
                            continue
                        if year > 0:
                            rows = _fetch_transactions('year', year)
                            break
                    break
                if filter_choice == '2':
                    while True:
                        year_input = safe_input("Enter year: ").strip()
                        try:
                            year = int(year_input)
                        except ValueError:
                            print("Invalid year. Please enter a valid number.")
                            continue
                        if year <= 0:
                            print("Invalid year. Please enter a valid number.")
                            continue
                        break

                    while True:
                        month_input = safe_input("Enter month number (1-12): ").strip()
                        try:
                            month = int(month_input)
                        except ValueError:
                            print("Invalid month. Please enter a number from 1 to 12.")
                            continue
                        if 1 <= month <= 12:
                            rows = _fetch_transactions('month', (year, month))
                            break
                        print("Invalid month. Please enter a number from 1 to 12.")
                    break
                if filter_choice == '3':
                    while True:
                        year_input = safe_input("Enter year: ").strip()
                        try:
                            year = int(year_input)
                        except ValueError:
                            print("Invalid year. Please enter a valid number.")
                            continue
                        if year <= 0:
                            print("Invalid year. Please enter a valid number.")
                            continue
                        break

                    while True:
                        month_input = safe_input("Enter month number (1-12): ").strip()
                        try:
                            month = int(month_input)
                        except ValueError:
                            print("Invalid month. Please enter a number from 1 to 12.")
                            continue
                        if 1 <= month <= 12:
                            break
                        print("Invalid month. Please enter a number from 1 to 12.")

                    while True:
                        day_input = safe_input("Enter day number (1-31): ").strip()
                        try:
                            day = int(day_input)
                        except ValueError:
                            print("Invalid day. Please enter a number from 1 to 31.")
                            continue
                        if 1 <= day <= 31:
                            rows = _fetch_transactions('day', (year, month, day))
                            break
                        print("Invalid day. Please enter a number from 1 to 31.")
                    break
                print("Invalid choice. Please enter 1, 2, or 3.")
            break
        print("Invalid choice. Please enter 1 or 2.")

    if not _display_transaction_rows(rows):
        return

    while True:
        transaction_id_input = safe_input("Enter transaction ID to select: ").strip()
        try:
            transaction_id = int(transaction_id_input)
        except ValueError:
            print("Invalid ID. Please enter a valid number.")
            continue

        selected_transaction = next((row for row in rows if row[0] == transaction_id), None)
        if selected_transaction is None:
            print("No transaction found with that ID.")
            continue
        break

    _show_selected_transaction(selected_transaction)

    while True:
        action_choice = safe_input("Would you like to delete or edit this transaction? (d/e): ").strip().lower()
        if action_choice in {'d', 'delete'}:
            confirmation = safe_input("Type y to confirm deletion: ").strip().lower()
            if confirmation in {'y', 'yes'}:
                conn = init_db()
                c = conn.cursor()
                c.execute("DELETE FROM storage WHERE id = ?", (transaction_id,))
                conn.commit()
                conn.close()
                print("Transaction deleted successfully.")
            else:
                print("Deletion cancelled.")
            return
        if action_choice in {'e', 'edit'}:
            break
        print("Invalid choice. Please enter d for delete or e for edit.")

    existing_id, existing_amount, existing_category, existing_type, existing_created_at = selected_transaction
    while True:
        print("\nLeave a field blank to keep the current value.")

        amount_input = safe_input(f"Edit amount [{abs(existing_amount):.2f}]: ").strip()
        if amount_input:
            try:
                amount_value = float(amount_input)
            except ValueError:
                print("Invalid amount. Please enter a valid number.")
                continue
            if amount_value <= 0:
                print("Amount must be greater than 0.")
                continue
        else:
            amount_value = existing_amount

        while True:
            type_input = safe_input(f"Edit type [{existing_type}]: ").strip().lower()
            if not type_input:
                new_type = existing_type
                break
            if type_input in {'1', 'income'}:
                new_type = 'income'
                break
            if type_input in {'2', 'expense'}:
                new_type = 'expense'
                break
            print("Invalid type. Please enter income, expense, 1, or 2.")

        categories = _get_transaction_categories(new_type)
        print("Select a category:")
        for code, name in categories.items():
            print(f"{code}. {name}")

        category_input = safe_input(f"Edit category [{existing_category}]: ").strip()
        if category_input:
            if category_input in categories:
                new_category = categories[category_input]
            else:
                print("Invalid category code. Please enter one of the listed options.")
                continue
        else:
            new_category = existing_category

        new_amount = _normalize_transaction_amount(amount_value, new_type)
        updated_transaction = (existing_id, new_amount, new_category, new_type, existing_created_at)
        _show_selected_transaction(updated_transaction)

        confirmation = safe_input("Confirm this edit? (y/n): ").strip().lower()
        if confirmation in {'y', 'yes'}:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = init_db()
            c = conn.cursor()
            c.execute(
                "UPDATE storage SET amount=?, category=?, type=?, created_at=? WHERE id=?",
                (new_amount, new_category, new_type, current_time, existing_id)
            )
            conn.commit()
            conn.close()
            print("Transaction updated successfully.")
            return
        if confirmation in {'n', 'no'}:
            print("Edit cancelled. You can modify the transaction again.")
            continue
        print("Invalid choice. Please enter y or n.")


def export_to_csv(rows, year, month):
    print("Export process started...")
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
    print("\nView Historical Data")

    while True:
        year_input = safe_input("Enter year: ").strip()
        try:
            year = int(year_input)
        except ValueError:
            print("Invalid year. Please enter a valid number.")
            continue

        if year > 0:
            break
        print("Invalid year. Please enter a valid number.")

    while True:
        month_input = safe_input("Enter month number (1-12): ").strip()
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
        report_choice = safe_input("Enter choice (1, 2, or 3): ").strip()
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
            export_choice = safe_input("\nWould you like to export this data as CSV? (y/n): ").strip().lower()
            if export_choice in {'y', 'yes'}:
                export_to_csv(rows, year, month)
                break
            elif export_choice in {'n', 'no'}:
                break
            else:
                print("Invalid choice. Please enter y or n.")
