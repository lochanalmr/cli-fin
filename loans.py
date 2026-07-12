from datetime import date, datetime, timedelta

from shared import (
    EXPENSE_CATEGORIES,
    LOANS_DB,
    STORAGE_DB,
    calculate_next_due_date,
    db_cursor,
    format_currency,
    format_table,
    get_choice,
    get_confirmation,
    get_int_input,
    get_optional_choice,
    get_optional_date,
    get_optional_positive_float,
    get_positive_float,
    parse_date_ddmmyyyy,
    print_table,
    safe_input,
)


LOAN_FREQUENCIES = {
    '1': 'yearly',
    '2': 'monthly',
    '3': 'weekly',
}


def _insert_loan_record(name, payment_amount, frequency, term_count, total_loan_value, first_due_date, status='active'):
    """Insert a new loan record into the database."""
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with db_cursor(LOANS_DB, commit=True) as c:
        c.execute(
            """
            INSERT INTO loans (name, payment_amount, frequency, term_count, total_loan_value, remaining_balance, first_due_date, next_due_date, last_payment_at, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, payment_amount, frequency, term_count, total_loan_value, total_loan_value, first_due_date, first_due_date, None, status, created_at)
        )


def add_loan():
    """Add a new loan. Total loan value is calculated from payment amount and term."""
    print('\n' + '=' * 60)
    print('Add Loan')
    print('=' * 60)
    
    # Get loan name
    while True:
        name = safe_input('Enter loan name/description: ').strip()
        if name:
            break
        print('Loan name cannot be empty.')

    # Get payment frequency
    print('\nPayment Frequency:')
    print('1. Yearly')
    print('2. Monthly')
    print('3. Weekly')
    frequency_choice = get_choice(
        'Enter frequency code (1, 2, or 3): ',
        ['1', '2', '3'],
        'Invalid choice. Please enter 1, 2, or 3.',
        input_fn=safe_input
    )
    frequency = LOAN_FREQUENCIES[frequency_choice]

    # Get payment amount per frequency
    payment_amount = get_positive_float(f'Enter payment amount per {frequency}: ')

    # Get credited loan amount (the actual loan amount received)
    print('\nNote: The credited loan amount will be recorded as income in your transactions.')
    credited_amount = get_positive_float('Enter the credited loan amount (actual amount received): ')

    # Get loan term (number of payments)
    term_count = get_int_input(
        f'Enter loan term (number of {frequency} payments): ',
        'Invalid term. Please enter a valid positive number.',
        lambda t: t > 0,
        'Term must be greater than 0.',
        input_fn=safe_input
    )

    # Calculate total loan value
    total_loan_value = payment_amount * term_count
    print(f'\nCalculated total loan value: {format_currency(total_loan_value)}')
    print(f'({term_count} payments x {format_currency(payment_amount)} per {frequency})')
    
    if abs(total_loan_value - credited_amount) > 0.01:
        print(f'Note: Total repayment ({format_currency(total_loan_value)}) differs from credited amount ({format_currency(credited_amount)})')
        if total_loan_value > credited_amount:
            print(f'This implies interest/fees of {format_currency(total_loan_value - credited_amount)}')
        else:
            print(f'Warning: Credited amount exceeds total repayment - please verify the figures')

    # Get first payment due date
    while True:
        first_due_date_input = safe_input('Enter first payment due date (DD-MM-YYYY): ').strip()
        parsed_date = parse_date_ddmmyyyy(first_due_date_input)
        if parsed_date is not None:
            first_due_date = parsed_date.strftime('%d-%m-%Y')
            break
        print('Invalid date. Please use DD-MM-YYYY with a valid day, month, and year.')

    _insert_loan_record(name, payment_amount, frequency, term_count, total_loan_value, first_due_date)
    print('\nLoan added successfully.')
    
    # Record the credited loan amount as income in transactions
    created_at_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with db_cursor(STORAGE_DB, commit=True) as c:
        c.execute(
            "INSERT INTO storage (amount, category, type, created_at) VALUES (?, ?, ?, ?)",
            (abs(credited_amount), 'Loan Income', 'income', created_at_time)
        )
    print(f'{format_currency(credited_amount)} recorded as income in transactions.')


def _fetch_loans():
    """Fetch all loans from the database."""
    with db_cursor(LOANS_DB) as c:
        c.execute(
            "SELECT id, name, payment_amount, frequency, term_count, total_loan_value, remaining_balance, first_due_date, next_due_date, last_payment_at, status, created_at FROM loans ORDER BY id"
        )
        return c.fetchall()


def _display_loans(rows):
    """Display loans in a formatted table."""
    if not rows:
        print('No loans found.')
        return False

    headers = ['ID', 'Name', 'Payment', 'Freq', 'Term', 'Total', 'Remaining', 'Next Due', 'Status']
    table_rows = []
    for record in rows:
        record_id, name, payment_amount, frequency, term_count, total_loan_value, remaining_balance, first_due_date, next_due_date, last_payment_at, status, created_at = record
        table_rows.append([
            record_id,
            name,
            format_currency(payment_amount),
            frequency,
            term_count,
            format_currency(total_loan_value),
            format_currency(remaining_balance),
            next_due_date,
            status
        ])
    
    print('\nAvailable Loans')
    print_table(headers, table_rows)
    return True


def update_loan():
    """Update loan details (payment amount, term, etc.). Recalculates total loan value."""
    print('\n' + '=' * 60)
    print('Update Loan')
    print('=' * 60)
    
    rows = _fetch_loans()
    if not _display_loans(rows):
        return

    loan_id = get_int_input(
        'Enter loan ID to update: ',
        'Invalid ID. Please enter a valid number.',
        lambda lid: any(row[0] == lid for row in rows),
        'No loan found with that ID.',
        input_fn=safe_input
    )
    selected_loan = next(row for row in rows if row[0] == loan_id)

    (record_id, existing_name, existing_payment_amount, existing_frequency, 
     existing_term_count, existing_total_loan_value, existing_remaining_balance,
     existing_first_due_date, existing_next_due_date, existing_last_payment_at,
     existing_status, existing_created_at) = selected_loan

    while True:
        print('\nLeave a field blank to keep the current value.')

        # Edit name
        name_input = safe_input(f'Edit name [{existing_name}]: ').strip()
        new_name = name_input if name_input else existing_name

        # Edit payment amount
        new_payment_amount = get_optional_positive_float(
            f'Edit payment amount per {existing_frequency} [{format_currency(existing_payment_amount)}]: ',
            existing_payment_amount,
            input_fn=safe_input
        )

        # Edit frequency
        new_frequency = get_optional_choice(
            f'Edit frequency [{existing_frequency}]: ',
            {
                '1': 'yearly', 'yearly': 'yearly',
                '2': 'monthly', 'monthly': 'monthly',
                '3': 'weekly', 'weekly': 'weekly'
            },
            existing_frequency,
            'Invalid frequency. Please enter yearly, monthly, weekly, or the corresponding number.',
            input_fn=safe_input
        )

        # Edit term count
        term_input = safe_input(f'Edit loan term (number of {new_frequency} payments) [{existing_term_count}]: ').strip()
        if term_input:
            try:
                new_term_count = int(term_input)
                if new_term_count <= 0:
                    print('Term must be greater than 0.')
                    continue
            except ValueError:
                print('Invalid term. Please enter a valid positive number.')
                continue
        else:
            new_term_count = existing_term_count

        # Edit first due date
        new_first_due_date = get_optional_date(
            f'Edit first payment due date [{existing_first_due_date}] (DD-MM-YYYY): ',
            existing_first_due_date,
            parse_date_ddmmyyyy,
            '%d-%m-%Y',
            'Invalid date. Please use DD-MM-YYYY with a valid day, month, and year.',
            input_fn=safe_input
        )

        # Calculate new total loan value
        new_total_loan_value = new_payment_amount * new_term_count
        
        print(f'\nUpdated loan summary:')
        print(f'  Payment amount: {format_currency(new_payment_amount)} per {new_frequency}')
        print(f'  Term: {new_term_count} payments')
        print(f'  Calculated total loan value: {format_currency(new_total_loan_value)}')

        if get_confirmation('Confirm this edit? (y/n): ', input_fn=safe_input):
            # Update next_due_date to match first_due_date if it changed
            with db_cursor(LOANS_DB, commit=True) as c:
                c.execute(
                    """UPDATE loans SET name=?, payment_amount=?, frequency=?, term_count=?, 
                       total_loan_value=?, remaining_balance=?, first_due_date=?, next_due_date=? 
                       WHERE id=?""",
                    (new_name, new_payment_amount, new_frequency, new_term_count,
                     new_total_loan_value, new_total_loan_value, new_first_due_date, new_first_due_date, record_id)
                )
            print('Loan updated successfully.')
            return
        else:
            print('Edit cancelled. You can modify the loan again.')
            continue


def collect_pending_loan_due_dates(current_due_date, today, frequency):
    """Return loan due dates from current_due_date through today."""
    if not isinstance(current_due_date, date) or not isinstance(today, date):
        return []

    if current_due_date > today:
        return []

    pending = []
    cursor = current_due_date
    while cursor <= today:
        pending.append(cursor)
        cursor = calculate_next_due_date(cursor, frequency)
        if cursor is None:
            break
    return pending


def mark_loan_payments_as_already_paid(loan_id, payment_count):
    """Advance overdue loan payments without creating current-month expenses."""
    rows = _fetch_loans()
    selected_loan = next((row for row in rows if row[0] == loan_id), None)
    if not selected_loan:
        raise ValueError(f'Loan with id {loan_id} was not found.')

    (record_id, name, payment_amount_regular, frequency, term_count,
     total_loan_value, remaining_balance, first_due_date, next_due_date,
     last_payment_at, status, created_at) = selected_loan

    normalized_count = int(payment_count)
    if normalized_count <= 0:
        raise ValueError('Payment count must be greater than 0.')

    total_paid = min(payment_amount_regular * normalized_count, remaining_balance)
    new_remaining_balance = max(remaining_balance - total_paid, 0.0)

    new_next_due_date = next_due_date
    try:
        current_due = datetime.strptime(next_due_date, '%d-%m-%Y').date()
        for _ in range(normalized_count):
            next_due = calculate_next_due_date(current_due, frequency)
            if next_due is None:
                break
            current_due = next_due
        new_next_due_date = current_due.strftime('%d-%m-%Y')
    except (ValueError, TypeError):
        pass

    processed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with db_cursor(LOANS_DB, commit=True) as c:
        c.execute(
            """UPDATE loans SET remaining_balance=?, next_due_date=?, last_payment_at=?,
               status=?, payment_amount=? WHERE id=?""",
            (new_remaining_balance, new_next_due_date, processed_at,
             'paid' if new_remaining_balance <= 0 else 'active', payment_amount_regular, record_id)
        )

    return {
        'loan_id': record_id,
        'payment_count': normalized_count,
        'total_paid': total_paid,
        'remaining_balance': new_remaining_balance,
        'next_due_date': new_next_due_date,
        'status': 'paid' if new_remaining_balance <= 0 else 'active',
    }

def apply_loan_payment_to_loan(loan_id, payment_amount, advance_due_date=False):
    """Apply a payment to a specific loan and update its remaining balance and due date."""
    rows = _fetch_loans()
    selected_loan = next((row for row in rows if row[0] == loan_id), None)
    if not selected_loan:
        raise ValueError(f'Loan with id {loan_id} was not found.')

    (record_id, name, payment_amount_regular, frequency, term_count,
     total_loan_value, remaining_balance, first_due_date, next_due_date,
     last_payment_at, status, created_at) = selected_loan

    if remaining_balance <= 0:
        return {
            'loan_id': record_id,
            'remaining_balance': 0.0,
            'next_due_date': next_due_date,
            'status': 'paid',
        }

    normalized_payment = float(payment_amount)
    if normalized_payment <= 0:
        raise ValueError('Payment amount must be greater than 0.')

    new_remaining_balance = max(remaining_balance - normalized_payment, 0.0)
    new_next_due_date = next_due_date
    if advance_due_date:
        try:
            current_due = datetime.strptime(next_due_date, '%d-%m-%Y').date()
            new_due = calculate_next_due_date(current_due, frequency)
            if new_due:
                new_next_due_date = new_due.strftime('%d-%m-%Y')
        except (ValueError, TypeError):
            pass

    created_at_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with db_cursor(LOANS_DB, commit=True) as c:
        c.execute(
            """UPDATE loans SET remaining_balance=?, next_due_date=?, last_payment_at=?, 
               status=?, payment_amount=? WHERE id=?""",
            (new_remaining_balance, new_next_due_date, created_at_time,
             'paid' if new_remaining_balance <= 0 else 'active', payment_amount_regular, record_id)
        )

    return {
        'loan_id': record_id,
        'remaining_balance': new_remaining_balance,
        'next_due_date': new_next_due_date,
        'status': 'paid' if new_remaining_balance <= 0 else 'active',
    }


def make_loan_payment(loan_id=None, payment_amount=None, is_partial=None, carry_over_balance=None):
    """Make a loan payment. Records as transaction and updates loan balance."""
    print('\n' + '=' * 60)
    print('Make Loan Payment')
    print('=' * 60)
    
    rows = _fetch_loans()
    active_loans = [row for row in rows if row[10] == 'active']  # status is at index 10
    
    if not active_loans:
        print('No active loans found.')
        return

    if loan_id is None:
        if not _display_loans(active_loans):
            return

        loan_id = get_int_input(
            'Enter loan ID to make payment: ',
            'Invalid ID. Please enter a valid number.',
            lambda lid: any(row[0] == lid for row in active_loans),
            'No loan found with that ID.',
            input_fn=safe_input
        )
    
    selected_loan = next((row for row in active_loans if row[0] == loan_id), None)
    if not selected_loan:
        print('Loan not found.')
        return

    (record_id, name, payment_amount_regular, frequency, term_count, 
     total_loan_value, remaining_balance, first_due_date, next_due_date, 
     last_payment_at, status, created_at) = selected_loan

    if remaining_balance <= 0:
        print('This loan is already fully paid.')
        return

    # Determine payment amount
    if payment_amount is None:
        print(f'\nRegular payment amount: {format_currency(payment_amount_regular)} per {frequency}')
        print(f'Remaining balance: {format_currency(remaining_balance)}')
        payment_input = safe_input(f'Enter payment amount (or press Enter for full payment of {format_currency(payment_amount_regular)}): ').strip()
        if not payment_input:
            payment_amount = min(payment_amount_regular, remaining_balance)
        else:
            try:
                payment_amount = float(payment_input)
                if payment_amount <= 0:
                    print('Payment amount must be greater than 0.')
                    return
            except ValueError:
                print('Invalid payment amount.')
                return

    # Check if this is a partial payment
    if is_partial is None:
        is_partial = payment_amount < payment_amount_regular

    # Determine if we should advance the due date
    advance_due_date = True
    if is_partial:
        print('\nThis is a partial payment (less than the regular payment amount).')
        advance_due = get_confirmation('Would you like to apply this payment toward the next due date (advance due date)? (y/n): ', input_fn=safe_input)
        advance_due_date = advance_due

    # Record the payment as a transaction
    created_at_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with db_cursor(STORAGE_DB, commit=True) as c:
        c.execute(
            "INSERT INTO storage (amount, category, type, created_at) VALUES (?, ?, ?, ?)",
            (-abs(payment_amount), 'Loan Payments', 'expense', created_at_time)
        )

    # Update loan balance
    new_remaining_balance = remaining_balance - payment_amount
    if new_remaining_balance < 0:
        new_remaining_balance = 0

    # Handle carry-over balance for partial payments when advancing due date
    new_payment_amount_regular = payment_amount_regular
    if advance_due_date and is_partial:
        unpaid_portion = payment_amount_regular - payment_amount
        if carry_over_balance is None or carry_over_balance is False:
            # Ask user if they want to add unpaid portion to next payment
            print(f'\nUnpaid portion of this payment: {format_currency(unpaid_portion)}')
            add_to_next = get_confirmation('Would you like to add this unpaid amount to the next payment due? (y/n): ', input_fn=safe_input)
            if add_to_next:
                new_payment_amount_regular = payment_amount_regular + unpaid_portion
                print(f'Next payment amount updated to: {format_currency(new_payment_amount_regular)}')
        elif carry_over_balance > 0:
            # Carry over balance from previous partial payment
            new_payment_amount_regular = payment_amount_regular + carry_over_balance

    # Update next due date if advancing
    new_next_due_date = next_due_date
    if advance_due_date:
        try:
            current_due = datetime.strptime(next_due_date, '%d-%m-%Y').date()
            new_due = calculate_next_due_date(current_due, frequency)
            if new_due:
                new_next_due_date = new_due.strftime('%d-%m-%Y')
        except (ValueError, TypeError):
            pass

    # Update loan record
    with db_cursor(LOANS_DB, commit=True) as c:
        c.execute(
            """UPDATE loans SET remaining_balance=?, next_due_date=?, last_payment_at=?, 
               status=?, payment_amount=? WHERE id=?""",
            (new_remaining_balance, new_next_due_date, created_at_time,
             'paid' if new_remaining_balance <= 0 else 'active', new_payment_amount_regular, record_id)
        )

    print(f'\nPayment of {format_currency(payment_amount)} recorded successfully.')
    print(f'Remaining balance: {format_currency(new_remaining_balance)}')
    if advance_due_date:
        print(f'Next due date updated to: {new_next_due_date}')
    else:
        print(f'Next due date remains: {new_next_due_date}')
    
    if new_remaining_balance <= 0:
        print('Congratulations! This loan is now fully paid.')


def delete_loan():
    """Delete a loan record."""
    print('\n' + '=' * 60)
    print('Delete Loan')
    print('=' * 60)
    
    rows = _fetch_loans()
    if not _display_loans(rows):
        return

    loan_id = get_int_input(
        'Enter loan ID to delete: ',
        'Invalid ID. Please enter a valid number.',
        lambda lid: any(row[0] == lid for row in rows),
        'No loan found with that ID.',
        input_fn=safe_input
    )

    confirmation = safe_input('Type y to confirm deletion (this cannot be undone): ').strip().lower()
    if confirmation in {'y', 'yes'}:
        with db_cursor(LOANS_DB, commit=True) as c:
            c.execute("DELETE FROM loans WHERE id=?", (loan_id,))
        print('Loan deleted successfully.')
    else:
        print('Deletion cancelled.')


def manage_loans():
    """Main loan management menu."""
    while True:
        print('\n' + '=' * 60)
        print('Loan Management')
        print('=' * 60)
        print('1. Add New Loan')
        print('2. Update Loan Details')
        print('3. Make Loan Payment')
        print('4. Delete Loan')
        print('5. View All Loans')
        print('6. View Next Payment Amounts')
        print('7. Back to Main Menu')
        
        choice = safe_input('Choose an option (1, 2, 3, 4, 5, 6, or 7): ').strip()
        
        if choice == '1':
            add_loan()
        elif choice == '2':
            update_loan()
        elif choice == '3':
            make_loan_payment()
        elif choice == '4':
            delete_loan()
        elif choice == '5':
            rows = _fetch_loans()
            _display_loans(rows)
        elif choice == '6':
            view_next_loan_payments()
        elif choice == '7':
            return
        else:
            print('Invalid choice. Please enter 1, 2, 3, 4, 5, 6, or 7.')



def view_next_loan_payments():
    """View upcoming loan payment amounts for all active loans."""
    print('\n' + '=' * 60)
    print('Next Loan Payment Amounts')
    print('=' * 60)
    
    rows = _fetch_loans()
    active_loans = [row for row in rows if row[10] == 'active']  # status is at index 10
    
    if not active_loans:
        print('No active loans found.')
        return

    today = date.today()
    
    headers = ['ID', 'Loan Name', 'Next Payment', 'Due Date', 'Frequency', 'Remaining Balance', 'Payments Left']
    table_rows = []
    
    for record in active_loans:
        (record_id, name, payment_amount, frequency, term_count,
         total_loan_value, remaining_balance, first_due_date, next_due_date,
         last_payment_at, status, created_at) = record
        
        # Calculate payments left
        if payment_amount > 0:
            payments_left = max(1, int(remaining_balance / payment_amount))
            if remaining_balance % payment_amount > 0:
                payments_left += 1
        else:
            payments_left = 0
        
        # Parse next due date to check if it's overdue
        try:
            due_date = datetime.strptime(next_due_date, '%d-%m-%Y').date()
            due_date_status = next_due_date
            if due_date < today:
                due_date_status = f"{next_due_date} (OVERDUE)"
        except (ValueError, TypeError):
            due_date_status = next_due_date
        
        table_rows.append([
            record_id,
            name,
            format_currency(payment_amount),
            due_date_status,
            frequency,
            format_currency(remaining_balance),
            payments_left
        ])
    
    print_table(headers, table_rows)
    
    # Calculate and display summary
    total_next_payments = sum(row[2] for row in active_loans)
    total_remaining = sum(row[6] for row in active_loans)
    
    print(f'\nSummary:')
    print(f'  Total next payments due: {format_currency(total_next_payments)}')
    print(f'  Total remaining balance across all loans: {format_currency(total_remaining)}')


def process_due_loan_payments():
    """Process due loan payments similar to subscriptions."""
    rows = _fetch_loans()
    active_loans = [row for row in rows if row[10] == 'active']
    
    if not active_loans:
        return

    today = date.today()
    
    for record in active_loans:
        (record_id, name, payment_amount, frequency, term_count,
         total_loan_value, remaining_balance, first_due_date, next_due_date,
         last_payment_at, status, created_at) = record

        try:
            due_date = datetime.strptime(next_due_date, '%d-%m-%Y').date()
        except (ValueError, TypeError):
            continue

        pending_due_dates = collect_pending_loan_due_dates(due_date, today, frequency)
        if not pending_due_dates or remaining_balance <= 0:
            continue

        due_count = len(pending_due_dates)
        total_due = min(payment_amount * due_count, remaining_balance)
        print(f"\nLoan payment of {format_currency(payment_amount)} is due for '{name}' (Due: {next_due_date})")

        if due_count > 1:
            first_due = pending_due_dates[0].strftime('%d-%m-%Y')
            last_due = pending_due_dates[-1].strftime('%d-%m-%Y')
            print(f"This loan has {due_count} pending payment(s) from {first_due} through {last_due}.")
            print(f"Choose whether to record a payment now or mark previous payments as already paid.")
        else:
            print("Choose whether to record this payment now or mark it as already paid.")

        print("1. Make one payment now and record it as this month's expense")
        print(f"2. Mark all {due_count} pending payment(s) as already paid without adding expense records ({format_currency(total_due)})")
        print("3. Skip for now")
        choice = get_choice(
            'Choose an option (1, 2, or 3): ',
            ['1', '2', '3'],
            'Invalid choice. Please enter 1, 2, or 3.',
            input_fn=safe_input
        )

        if choice == '1':
            make_loan_payment(loan_id=record_id, payment_amount=min(payment_amount, remaining_balance), is_partial=False)
        elif choice == '2':
            result = mark_loan_payments_as_already_paid(record_id, due_count)
            print(f"Marked {result['payment_count']} payment(s) as already paid without adding expense records.")
            print(f"Remaining balance: {format_currency(result['remaining_balance'])}")
            if result['status'] == 'paid':
                print('This loan is now fully paid.')
            else:
                print(f"Next due date updated to: {result['next_due_date']}")
        else:
            print('Loan payment skipped. No expense was added.')
