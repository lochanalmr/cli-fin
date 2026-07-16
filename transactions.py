import csv
from datetime import datetime

from assets import add_asset
from loans import apply_loan_payment_to_loan

from shared import (
    EXPENSE_CATEGORIES,
    STORAGE_DB,
    db_cursor,
    format_currency,
    format_table,
    get_choice,
    get_confirmation,
    get_int_input,
    get_optional_choice,
    get_optional_positive_float,
    get_positive_float,
    print_table,
    safe_input,
)


def _normalize_transaction_amount(amount, transaction_type):
    """Normalize amount based on transaction type."""
    normalized_type = (transaction_type or '').lower()
    if normalized_type == 'income':
        return abs(amount)
    if normalized_type == 'expense':
        return -abs(amount)
    return amount


def _get_transaction_categories(transaction_type):
    """Get categories for a given transaction type."""
    if transaction_type == 'income':
        return {
            '1': 'Salary',
            '2': 'Gift',
            '3': 'Interest/Dividends',
            '4': 'Reverse Transaction',
            '5': 'Other'
        }
    return EXPENSE_CATEGORIES


def _display_monthly_summary(year, month):
    """Display quick summary of monthly expenses."""
    month_name = datetime(year, month, 1).strftime("%B")
    month_filter = f"{year:04d}-{month:02d}-%"
    
    with db_cursor(STORAGE_DB) as c:
        c.execute(
            "SELECT amount, category, type FROM storage WHERE created_at LIKE ?",
            (month_filter,)
        )
        rows = c.fetchall()

    expense_totals = {}
    total_expenses = 0.0
    for amount, category, transaction_type in rows:
        if transaction_type.lower() == 'expense':
            display_amount = abs(amount)
            expense_totals[category] = expense_totals.get(category, 0.0) + display_amount
            total_expenses += display_amount

    print("Quick Summary")
    print(f"You have spent {format_currency(total_expenses)} in {month_name}.")
    if expense_totals:
        top_category, top_amount = max(expense_totals.items(), key=lambda item: item[1])
        print(f"Top expense category: {top_category} ({format_currency(top_amount)})")
    else:
        print("Top expense category: None")


def _handle_loan_payment(amount):
    """Handle loan payment transaction linking."""
    from loans import _fetch_loans
    
    rows = _fetch_loans()
    active_loans = [row for row in rows if row[10] == 'active']
    
    if not active_loans:
        print('No active loans found to link this payment to.')
        return

    print('\nSelect the loan this payment is for:')
    headers = ['ID', 'Name', 'Remaining']
    loan_rows = [
        [loan[0], loan[1], format_currency(loan[6])]
        for loan in active_loans
    ]
    print_table(headers, loan_rows)
    
    loan_choice = get_choice(
        'Enter loan ID: ',
        [str(loan[0]) for loan in active_loans],
        'Invalid loan selection. Please enter one of the listed IDs.'
    )
    selected_loan_id = int(loan_choice)
    
    advance_due_date = get_confirmation(
        'Should the next due date be pushed to the next period with the remaining balance? (y/n): ',
        input_fn=safe_input
    )
    apply_loan_payment_to_loan(selected_loan_id, amount, advance_due_date=advance_due_date)
    print('Loan balance updated successfully.')


def _handle_credit_card_payment(amount):
    """Handle credit card payment transaction linking."""
    from credit_cards import (
        _fetch_credit_cards,
        record_credit_card_payment_from_spendable,
        pay_from_another_credit_card
    )
    
    cards = _fetch_credit_cards()
    active_cards = [card for card in cards if card[12] == 'active']
    
    if not active_cards:
        print('No active credit cards found. Recording as a plain expense.')
        data_write(amount, 'Credit Card Payments', 'expense')
        return True  # Skip normal data_write

    print('\nSelect the credit card this payment is for:')
    headers = ['ID', 'Name', 'Current Balance']
    card_rows = [
        [card[0], card[1], format_currency(card[8])]
        for card in active_cards
    ]
    print_table(headers, card_rows)

    card_choice = get_int_input(
        'Enter credit card ID: ',
        'Invalid ID.',
        lambda cid: any(card[0] == cid for card in active_cards),
        'No credit card found with that ID.',
        input_fn=safe_input
    )
    selected_card = next(card for card in active_cards if card[0] == card_choice)

    print('\nPay from:')
    print('1. Spendable balance')
    print('2. Another credit card')
    pay_from_choice = get_choice(
        'Choose payment source (1 or 2): ',
        ['1', '2'],
        'Invalid choice. Please enter 1 or 2.',
        input_fn=safe_input
    )
    
    if pay_from_choice == '1':
        record_credit_card_payment_from_spendable(selected_card, amount)
        print(f'Credit card balance updated and payment of {format_currency(amount)} recorded from spendable balance.')
    else:
        pay_from_another_credit_card(selected_card, amount)
    
    return True  # Skip normal data_write


def _handle_credit_card_expense(amount, transaction_type, category):
    """Handle charging an expense to a credit card."""
    from credit_cards import prompt_for_credit_card_expense
    
    use_credit_card, card_id = prompt_for_credit_card_expense(amount, transaction_type, category)
    if use_credit_card:
        print(f'Expense of {format_currency(amount)} charged to credit card. It will be recorded as an expense when the card is paid.')
        return True  # Charged to card, skip normal write
    return False


def data_write(amount, category, transaction_type):
    """Write a transaction to the database."""
    normalized_type = transaction_type.lower()
    signed_amount = _normalize_transaction_amount(amount, normalized_type)
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with db_cursor(STORAGE_DB, commit=True) as c:
        c.execute(
            "INSERT INTO storage (amount, category, type, created_at) VALUES (?, ?, ?, ?)",
            (signed_amount, category, normalized_type, created_at)
        )
    print("Transaction added successfully.")


def data_entry():
    """Main transaction entry function."""
    while True:
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        _display_monthly_summary(current_year, current_month)

        print("\nTransaction Type")
        print("1. Income")
        print("2. Expense")

        type_choice = get_choice(
            "Enter transaction type code (1 or 2): ",
            ['1', '2'],
            "Invalid choice. Please enter 1 for income or 2 for expense."
        )
        transaction_type = 'income' if type_choice == '1' else 'expense'

        categories = _get_transaction_categories(transaction_type)

        print("\nSelect a category:")
        for code, name in categories.items():
            print(f"{code}. {name}")

        category_choice = get_choice(
            "Enter category code: ",
            list(categories.keys()),
            "Invalid category code. Please enter one of the listed options."
        )
        category = categories[category_choice]

        amount = get_positive_float("Enter amount: ")

        # Handle special expense categories
        skip_normal_write = False
        if transaction_type == 'expense':
            if category == 'Loan Payments':
                _handle_loan_payment(amount)
            elif category == 'Credit Card Payments':
                skip_normal_write = _handle_credit_card_payment(amount)
            else:
                skip_normal_write = _handle_credit_card_expense(amount, transaction_type, category)

        # Write transaction if not handled specially
        if not skip_normal_write:
            data_write(amount, category, transaction_type)
            if category == 'Asset Purchase':
                add_asset(amount=amount)

        if not get_confirmation("Do you want to add another entry? (y/n): "):
            return


def _display_transaction_rows(rows):
    if not rows:
        print("No transactions found.")
        return False

    headers = ['ID', 'Value', 'Type', 'Category']
    table_rows = []
    for record_id, amount, category, transaction_type, _ in rows:
        table_rows.append([
            record_id,
            format_currency(amount),
            transaction_type,
            category
        ])
    
    print("\nAvailable transactions")
    print_table(headers, table_rows)
    return True


def _show_selected_transaction(transaction):
    record_id, amount, category, transaction_type, _ = transaction
      
    print("Selected transaction details")
      
    print(f"Transaction ID:        {record_id}")
    print(f"Transaction value:    {format_currency(amount)}")
    print(f"Transaction type:     {transaction_type.lower()}")
    print(f"Transaction category: {category}")


def _fetch_transactions(filter_type=None, filter_value=None):
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
    with db_cursor(STORAGE_DB) as c:
        c.execute(query, tuple(params))
        return c.fetchall()


def manage_transaction():
      
    print("Manage transaction")
      

    view_choice = get_choice(
        "Would you like to (1) view all transactions or (2) filter transactions? ",
        ['1', '2'],
        "Invalid choice. Please enter 1 or 2."
    )

    if view_choice == '1':
        rows = _fetch_transactions()
    else:
        filter_choice = get_choice(
            "Filter by (1) year, (2) month, or (3) day? ",
            ['1', '2', '3'],
            "Invalid choice. Please enter 1, 2, or 3."
        )
        if filter_choice == '1':
            year = get_int_input(
                "Enter year: ",
                "Invalid year. Please enter a valid number.",
                lambda y: y > 0,
                "Invalid year. Please enter a valid number."
            )
            rows = _fetch_transactions('year', year)
        elif filter_choice == '2':
            year = get_int_input(
                "Enter year: ",
                "Invalid year. Please enter a valid number.",
                lambda y: y > 0,
                "Invalid year. Please enter a valid number."
            )
            month = get_int_input(
                "Enter month number (1-12): ",
                "Invalid month. Please enter a number from 1 to 12.",
                lambda m: 1 <= m <= 12,
                "Invalid month. Please enter a number from 1 to 12."
            )
            rows = _fetch_transactions('month', (year, month))
        else:
            year = get_int_input(
                "Enter year: ",
                "Invalid year. Please enter a valid number.",
                lambda y: y > 0,
                "Invalid year. Please enter a valid number."
            )
            month = get_int_input(
                "Enter month number (1-12): ",
                "Invalid month. Please enter a number from 1 to 12.",
                lambda m: 1 <= m <= 12,
                "Invalid month. Please enter a number from 1 to 12."
            )
            day = get_int_input(
                "Enter day number (1-31): ",
                "Invalid day. Please enter a number from 1 to 31.",
                lambda d: 1 <= d <= 31,
                "Invalid day. Please enter a number from 1 to 31."
            )
            rows = _fetch_transactions('day', (year, month, day))

    if not _display_transaction_rows(rows):
        return

    transaction_id = get_int_input(
        "Enter transaction ID to select: ",
        "Invalid ID. Please enter a valid number.",
        lambda tid: any(row[0] == tid for row in rows),
        "No transaction found with that ID."
    )
    selected_transaction = next(row for row in rows if row[0] == transaction_id)
    _show_selected_transaction(selected_transaction)

    action_choice = get_choice(
        "Would you like to delete or edit this transaction? (d/e): ",
        ['d', 'delete', 'e', 'edit'],
        "Invalid choice. Please enter d for delete or e for edit."
    )

    if action_choice in {'d', 'delete'}:
        confirmation = safe_input("Type y to confirm deletion: ").strip().lower()
        if confirmation in {'y', 'yes'}:
            with db_cursor(STORAGE_DB, commit=True) as c:
                c.execute("DELETE FROM storage WHERE id = ?", (transaction_id,))
            print("Transaction deleted successfully.")
        else:
            print("Deletion cancelled.")
        return

    existing_id, existing_amount, existing_category, existing_type, existing_created_at = selected_transaction
    while True:
        print("\nLeave a field blank to keep the current value.")

        amount_value = get_optional_positive_float(
            f"Edit amount [{format_currency(abs(existing_amount))}]: ",
            abs(existing_amount)
        )

        new_type = get_optional_choice(
            f"Edit type [{existing_type}]: ",
            {'1': 'income', 'income': 'income', '2': 'expense', 'expense': 'expense'},
            existing_type,
            "Invalid type. Please enter income, expense, 1, or 2."
        )

        categories = _get_transaction_categories(new_type)
        print("Select a category:")
        for code, name in categories.items():
            print(f"{code}. {name}")

        new_category = get_optional_choice(
            f"Edit category [{existing_category}]: ",
            categories,
            existing_category,
            "Invalid category code. Please enter one of the listed options."
        )

        new_amount = _normalize_transaction_amount(amount_value, new_type)
        updated_transaction = (existing_id, new_amount, new_category, new_type, existing_created_at)
        _show_selected_transaction(updated_transaction)

        if get_confirmation("Confirm this edit? (y/n): "):
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with db_cursor(STORAGE_DB, commit=True) as c:
                c.execute(
                    "UPDATE storage SET amount=?, category=?, type=?, created_at=? WHERE id=?",
                    (new_amount, new_category, new_type, current_time, existing_id)
                )
            print("Transaction updated successfully.")
            return
        else:
            print("Edit cancelled. You can modify the transaction again.")
            continue


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
      
    print("View Historical Data")
      

    year = get_int_input(
        "Enter year: ",
        "Invalid year. Please enter a valid number.",
        lambda y: y > 0,
        "Invalid year. Please enter a valid number."
    )

    month = get_int_input(
        "Enter month number (1-12): ",
        "Invalid month. Please enter a number from 1 to 12.",
        lambda m: 1 <= m <= 12,
        "Invalid month. Please enter a number from 1 to 12."
    )

    print("\nChoose report type:")
    print("1. Summary")
    print("2. Raw data")
    print("3. Both")
    report_choice = get_choice(
        "Enter choice (1, 2, or 3): ",
        ['1', '2', '3'],
        "Invalid choice. Please enter 1, 2, or 3."
    )

    month_name = datetime(year, month, 1).strftime("%B")
    month_filter = f"{year:04d}-{month:02d}-%"

    with db_cursor(STORAGE_DB) as c:
        c.execute(
            "SELECT id, amount, category, type, created_at FROM storage WHERE created_at LIKE ? ORDER BY created_at",
            (month_filter,)
        )
        rows = c.fetchall()

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

        print(f"\n{'=' * 60}")
        print(f"Summary for {month_name} {year}")
          
        
        print("\nIncome:")
        if income_totals:
            headers = ['Category', 'Amount']
            income_rows = [[cat, format_currency(amt)] for cat, amt in sorted(income_totals.items())]
            print_table(headers, income_rows)
        else:
            print("- None")
        print(f"Total income: {format_currency(total_income)}")

        print("\nExpenses:")
        if expense_totals:
            headers = ['Category', 'Amount']
            expense_rows = [[cat, format_currency(amt)] for cat, amt in sorted(expense_totals.items())]
            print_table(headers, expense_rows)
        else:
            print("- None")
        print(f"Total expenses: {format_currency(total_expenses)}")
        print(f"Net: {format_currency(total_income - total_expenses)}")

    if report_choice in {'2', '3'}:
        print(f"\n{'=' * 60}")
        print(f"Raw data for {month_name} {year}")
          
        headers = ['ID', 'Date', 'Type', 'Category', 'Amount']
        table_rows = []
        for record_id, amount, category, transaction_type, created_at in rows:
            table_rows.append([
                record_id,
                created_at,
                transaction_type,
                category,
                format_currency(amount)
            ])
        print_table(headers, table_rows)

        if get_confirmation("\nWould you like to export this data as CSV? (y/n): "):
            export_to_csv(rows, year, month)
