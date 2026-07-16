from datetime import date, datetime, timedelta

from shared import (
    CREDIT_CARDS_DB,
    CREDIT_CARD_EXPENSES_DB,
    STORAGE_DB,
    calculate_next_due_date,
    db_cursor,
    format_currency,
    format_table,
    get_choice,
    get_confirmation,
    get_int_input,
    get_optional_choice,
    get_optional_positive_float,
    get_positive_float,
    init_credit_cards_db,
    init_credit_card_expenses_db,
    parse_date_ddmmyyyy,
    print_table,
    safe_input,
)


def calculate_updated_credit_card_balance(current_balance, payment_amount):
    """Calculate the updated balance after a credit card payment."""
    return current_balance - payment_amount


def get_max_payment_amount(current_balance, interest_amount):
    """Return the maximum payment amount allowed before a card becomes overpaid."""
    if current_balance > 0:
        return current_balance + interest_amount
    return None


# Credit Card CRUD Operations

def _insert_credit_card_record(name, credit_limit, interest_rate, billing_date_day, due_date_day, billing_date_month, due_date_month):
    """Insert a new credit card record into the database."""
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    today = date.today()
    
    with db_cursor(CREDIT_CARDS_DB, commit=True) as c:
        c.execute(
            """
            INSERT INTO credit_cards (name, credit_limit, interest_rate, billing_date_day, due_date_day, billing_date_month, due_date_month, current_balance, statement_balance, last_billing_date, last_payment_date, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, credit_limit, interest_rate, billing_date_day, due_date_day, billing_date_month, due_date_month, 0.0, 0.0, today.strftime('%d-%m-%Y'), None, 'active', created_at)
        )


def add_credit_card():
    """Add a new credit card."""
    print('Add Credit Card')

    # Get credit card name
    while True:
        name = safe_input('Enter credit card name/description: ').strip()
        if name:
            break
        print('Credit card name cannot be empty.')

    # Get credit limit
    credit_limit = get_positive_float('Enter credit limit: ')

    # Get interest rate (APR as percentage)
    interest_rate = get_positive_float('Enter annual interest rate (APR) as percentage (e.g., 18 for 18%): ')

    # Get billing date (day of month)
    billing_date_day = get_int_input(
        'Enter billing date (day of month, 1-31): ',
        'Invalid day. Please enter a valid number.',
        lambda d: 1 <= d <= 31,
        'Day must be between 1 and 31.'
    )

    # Get billing date month
    billing_date_month = get_int_input(
        'Enter billing date month (1-12): ',
        'Invalid month. Please enter a valid number.',
        lambda m: 1 <= m <= 12,
        'Month must be between 1 and 12.'
    )

    # Get due date (day of month)
    due_date_day = get_int_input(
        'Enter due date (day of month, 1-31): ',
        'Invalid day. Please enter a valid number.',
        lambda d: 1 <= d <= 31,
        'Day must be between 1 and 31.'
    )

    # Get due date month
    due_date_month = get_int_input(
        'Enter due date month (1-12): ',
        'Invalid month. Please enter a valid number.',
        lambda m: 1 <= m <= 12,
        'Month must be between 1 and 12.'
    )

    _insert_credit_card_record(name, credit_limit, interest_rate, billing_date_day, due_date_day, billing_date_month, due_date_month)
    print('\nCredit card added successfully.')


def _fetch_credit_cards():
    """Fetch all credit cards from the database."""
    with db_cursor(CREDIT_CARDS_DB) as c:
        c.execute(
            "SELECT id, name, credit_limit, interest_rate, billing_date_day, due_date_day, billing_date_month, due_date_month, current_balance, statement_balance, last_billing_date, last_payment_date, status, created_at FROM credit_cards ORDER BY id"
        )
        rows = c.fetchall()
    return rows


def _display_credit_cards(rows):
    """Display credit cards in a formatted table."""
    if not rows:
        print('No credit cards found.')
        return False
    
    headers = ['ID', 'Name', 'Credit Limit', 'APR %', 'Bill Day', 'Bill Month', 'Due Day', 'Due Month', 'Balance', 'Status']
    table_rows = []
    for record in rows:
        (record_id, name, credit_limit, interest_rate, billing_date_day, due_date_day, 
         billing_date_month, due_date_month, current_balance, statement_balance, 
         last_billing_date, last_payment_date, status, created_at) = record
        
        table_rows.append([
            record_id,
            name,
            format_currency(credit_limit),
            f"{interest_rate:.2f}%",
            f"{billing_date_day:02d}",
            f"{billing_date_month:02d}",
            f"{due_date_day:02d}",
            f"{due_date_month:02d}",
            format_currency(current_balance),
            status
        ])
    
    print('\nAvailable Credit Cards')
    print_table(headers, table_rows)
    return True


def update_credit_card():
    """Update credit card details."""
       
    print('Update Credit Card')
    print('=' * 60)
    
    rows = _fetch_credit_cards()
    if not _display_credit_cards(rows):
        return
    
    credit_card_id = get_int_input(
        'Enter credit card ID to update: ',
        'Invalid ID. Please enter a valid number.',
        lambda cid: any(row[0] == cid for row in rows),
        'No credit card found with that ID.',
        input_fn=safe_input
    )
    
    selected_card = next(row for row in rows if row[0] == credit_card_id)
    
    (record_id, existing_name, existing_credit_limit, existing_interest_rate, 
     existing_billing_date_day, existing_due_date_day, existing_billing_date_month, 
     existing_due_date_month, existing_current_balance, existing_statement_balance,
     existing_last_billing_date, existing_last_payment_date, existing_status, 
     existing_created_at) = selected_card
    
    while True:
        print('\nLeave a field blank to keep the current value.')
        
        # Edit name
        name_input = safe_input(f'Edit name [{existing_name}]: ').strip()
        new_name = name_input if name_input else existing_name
        
        # Edit credit limit
        new_credit_limit = get_optional_positive_float(
            f'Edit credit limit [{format_currency(existing_credit_limit)}]: ',
            existing_credit_limit,
            input_fn=safe_input
        )
        
        # Edit interest rate
        new_interest_rate = get_optional_positive_float(
            f'Edit annual interest rate (APR) [{existing_interest_rate:.2f}%]: ',
            existing_interest_rate,
            input_fn=safe_input
        )
        
        # Edit billing date day
        billing_day_input = safe_input(f'Edit billing date day [{existing_billing_date_day:02d}]: ').strip()
        if billing_day_input:
            try:
                new_billing_date_day = int(billing_day_input)
                if not (1 <= new_billing_date_day <= 31):
                    print('Billing day must be between 1 and 31.')
                    continue
            except ValueError:
                print('Invalid billing day. Please enter a valid number.')
                continue
        else:
            new_billing_date_day = existing_billing_date_day
        
        # Edit billing date month
        billing_month_input = safe_input(f'Edit billing date month [{existing_billing_date_month:02d}]: ').strip()
        if billing_month_input:
            try:
                new_billing_date_month = int(billing_month_input)
                if not (1 <= new_billing_date_month <= 12):
                    print('Billing month must be between 1 and 12.')
                    continue
            except ValueError:
                print('Invalid billing month. Please enter a valid number.')
                continue
        else:
            new_billing_date_month = existing_billing_date_month
        
        # Edit due date day
        due_day_input = safe_input(f'Edit due date day [{existing_due_date_day:02d}]: ').strip()
        if due_day_input:
            try:
                new_due_date_day = int(due_day_input)
                if not (1 <= new_due_date_day <= 31):
                    print('Due day must be between 1 and 31.')
                    continue
            except ValueError:
                print('Invalid due day. Please enter a valid number.')
                continue
        else:
            new_due_date_day = existing_due_date_day
        
        # Edit due date month
        due_month_input = safe_input(f'Edit due date month [{existing_due_date_month:02d}]: ').strip()
        if due_month_input:
            try:
                new_due_date_month = int(due_month_input)
                if not (1 <= new_due_date_month <= 12):
                    print('Due month must be between 1 and 12.')
                    continue
            except ValueError:
                print('Invalid due month. Please enter a valid number.')
                continue
        else:
            new_due_date_month = existing_due_date_month
        
        print(f'\nUpdated credit card summary:')
        print(f'  Name: {new_name}')
        print(f'  Credit Limit: {format_currency(new_credit_limit)}')
        print(f'  Interest Rate: {new_interest_rate:.2f}%')
        print(f'  Billing Date: Day {new_billing_date_day:02d}, Month {new_billing_date_month:02d}')
        print(f'  Due Date: Day {new_due_date_day:02d}, Month {new_due_date_month:02d}')
        
        if get_confirmation('Confirm this edit? (y/n): ', input_fn=safe_input):
            
            with db_cursor(CREDIT_CARDS_DB, commit=True) as c:
                c.execute(
                    """UPDATE credit_cards SET name=?, credit_limit=?, interest_rate=?, 
                       billing_date_day=?, due_date_day=?, billing_date_month=?, due_date_month=? 
                       WHERE id=?""",
                    (new_name, new_credit_limit, new_interest_rate, new_billing_date_day, 
                     new_due_date_day, new_billing_date_month, new_due_date_month, record_id)
                )
            print('Credit card updated successfully.')
            return
        else:
            print('Edit cancelled. You can modify the credit card again.')
            continue


def delete_credit_card():
    """Delete a credit card record."""
       
    print('Delete Credit Card')
    print('=' * 60)
    
    rows = _fetch_credit_cards()
    if not _display_credit_cards(rows):
        return
    
    credit_card_id = get_int_input(
        'Enter credit card ID to delete: ',
        'Invalid ID. Please enter a valid number.',
        lambda cid: any(row[0] == cid for row in rows),
        'No credit card found with that ID.',
        input_fn=safe_input
    )
    
    confirmation = safe_input('Type y to confirm deletion (this cannot be undone): ').strip().lower()
    if confirmation in {'y', 'yes'}:
        
        with db_cursor(CREDIT_CARDS_DB, commit=True) as c:
            c.execute("DELETE FROM credit_cards WHERE id=?", (credit_card_id,))
        print('Credit card deleted successfully.')
    else:
        print('Deletion cancelled.')


# Credit Card Expense Operations

def _insert_credit_card_expense(credit_card_id, credit_card_name, amount, expense_type, expense_category):
    """Insert a new credit card expense record."""
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    transaction_date = datetime.now().strftime('%d-%m-%Y')
    
    with db_cursor(CREDIT_CARD_EXPENSES_DB, commit=True) as c:
        c.execute(
            """
            INSERT INTO credit_card_expenses (credit_card_id, credit_card_name, amount, expense_type, expense_category, transaction_date, is_paid, payment_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (credit_card_id, credit_card_name, amount, expense_type, expense_category, transaction_date, 0, None, created_at)
        )


def _fetch_credit_card_expenses(credit_card_id=None):
    """Fetch credit card expenses from the database."""
    
    if credit_card_id:
        with db_cursor(CREDIT_CARD_EXPENSES_DB) as c:
            c.execute(
                "SELECT id, credit_card_id, credit_card_name, amount, expense_type, expense_category, transaction_date, is_paid, payment_date, created_at FROM credit_card_expenses WHERE credit_card_id=? ORDER BY created_at",
                (credit_card_id,)
            )
            rows = c.fetchall()
    else:
        with db_cursor(CREDIT_CARD_EXPENSES_DB) as c:
            c.execute(
                "SELECT id, credit_card_id, credit_card_name, amount, expense_type, expense_category, transaction_date, is_paid, payment_date, created_at FROM credit_card_expenses ORDER BY created_at"
            )
            rows = c.fetchall()
    
    return rows


def _display_credit_card_expenses(rows):
    """Display credit card expenses in a formatted table."""
    if not rows:
        print('No credit card expenses found.')
        return False
    
    headers = ['ID', 'Card Name', 'Amount', 'Type', 'Category', 'Date', 'Paid']
    table_rows = []
    for record in rows:
        (record_id, credit_card_id, credit_card_name, amount, expense_type, 
         expense_category, transaction_date, is_paid, payment_date, created_at) = record
        
        paid_status = 'Yes' if is_paid else 'No'
        table_rows.append([
            record_id,
            credit_card_name,
            format_currency(amount),
            expense_type,
            expense_category,
            transaction_date,
            paid_status
        ])
    
    print('\nCredit Card Expenses')
    print_table(headers, table_rows)
    return True


def mark_credit_card_expense_as_paid(expense_id):
    """Mark a credit card expense as paid."""
    payment_date = datetime.now().strftime('%d-%m-%Y')
    
    with db_cursor(CREDIT_CARD_EXPENSES_DB, commit=True) as c:
        c.execute(
            "UPDATE credit_card_expenses SET is_paid=1, payment_date=? WHERE id=?",
            (payment_date, expense_id)
        )


def view_credit_card_expenses():
    """View credit card expenses with filtering options."""
       
    print('View Credit Card Expenses')
    print('=' * 60)
    
    # Get all credit cards for filtering
    credit_cards = _fetch_credit_cards()
    
    if not credit_cards:
        print('No credit cards available.')
        return
    
    print('\nFilter by credit card:')
    headers = ['ID', 'Name']
    card_rows = [[card[0], card[1]] for card in credit_cards]
    print_table(headers, card_rows)
    
    filter_choice = get_choice(
        '\nFilter by credit card ID (or 0 for all): ',
        ['0'] + [str(card[0]) for card in credit_cards],
        'Invalid choice.',
        input_fn=safe_input
    )
    
    credit_card_id = None if filter_choice == '0' else int(filter_choice)
    rows = _fetch_credit_card_expenses(credit_card_id)
    
    if not _display_credit_card_expenses(rows):
        return
    
    # Option to mark as paid
    if get_confirmation('\nWould you like to mark any expense as paid? (y/n): ', input_fn=safe_input):
        expense_id = get_int_input(
            'Enter expense ID to mark as paid: ',
            'Invalid ID.',
            lambda eid: any(row[0] == eid for row in rows),
            'No expense found with that ID.',
            input_fn=safe_input
        )
        mark_credit_card_expense_as_paid(expense_id)
        print('Expense marked as paid successfully.')


# Credit Card Payment Processing

def calculate_daily_interest_rate(annual_rate):
    """Calculate daily interest rate from annual rate."""
    return annual_rate / 100 / 365


def calculate_interest_accrued(principal, daily_rate, days):
    """Calculate interest accrued using daily compounding."""
    return principal * daily_rate * days


def get_next_billing_date(card):
    """Get the next billing date for a credit card."""
    (record_id, name, credit_limit, interest_rate, billing_date_day, due_date_day, 
     billing_date_month, due_date_month, current_balance, statement_balance,
     last_billing_date, last_payment_date, status, created_at) = card
    
    today = date.today()
    
    # Parse last billing date
    try:
        last_billing = datetime.strptime(last_billing_date, '%d-%m-%Y').date()
    except (ValueError, TypeError):
        # If no last billing date, use today
        last_billing = today
    
    # Calculate next billing date based on billing day and month
    year = today.year
    month = today.month
    
    # Try to use the billing date day and month
    try:
        next_billing = date(year, billing_date_month, billing_date_day)
        if next_billing <= today:
            # Move to next year or next occurrence
            year += 1
            next_billing = date(year, billing_date_month, billing_date_day)
    except ValueError:
        # Handle invalid dates (e.g., Feb 30)
        # Move to next month
        month = billing_date_month + 1
        year = today.year
        while month > 12:
            month -= 12
            year += 1
        next_billing = date(year, month, 1)
    
    return next_billing


def get_next_due_date(card):
    """Get the next due date for a credit card."""
    (record_id, name, credit_limit, interest_rate, billing_date_day, due_date_day, 
     billing_date_month, due_date_month, current_balance, statement_balance,
     last_billing_date, last_payment_date, status, created_at) = card
    
    today = date.today()
    
    # Try to use the due date day and month
    year = today.year
    month = today.month
    
    try:
        next_due = date(year, due_date_month, due_date_day)
        if next_due <= today:
            # Move to next year or next occurrence
            year += 1
            next_due = date(year, due_date_month, due_date_day)
    except ValueError:
        # Handle invalid dates
        month = due_date_month + 1
        year = today.year
        while month > 12:
            month -= 12
            year += 1
        next_due = date(year, month, 1)
    
    return next_due


def process_due_credit_card_payments():
    """Process due credit card payments at program startup."""
    cards = _fetch_credit_cards()
    active_cards = [card for card in cards if card[12] == 'active']  # status is at index 12
    
    if not active_cards:
        return
    
    today = date.today()
    tomorrow = today + timedelta(days=1)
    
    for card in active_cards:
        (record_id, name, credit_limit, interest_rate, billing_date_day, due_date_day, 
         billing_date_month, due_date_month, current_balance, statement_balance,
         last_billing_date, last_payment_date, status, created_at) = card
        
        # Get next due date
        next_due = get_next_due_date(card)
        
        if next_due is None:
            continue
        
        # Check if due date is tomorrow
        if next_due == tomorrow:
            print(f"\n⚠️  NOTIFICATION: Credit card '{name}' payment is due tomorrow ({next_due.strftime('%d-%m-%Y')})!")
            print(f"    Current balance: {format_currency(current_balance)}")
            print(f"    Credit limit: {format_currency(credit_limit)}")
        
        # Check if payment is due today (on or before today)
        if next_due <= today:
            # Calculate days overdue
            days_overdue = (today - next_due).days if next_due < today else 0
            
            # Calculate payment amount (current balance)
            payment_amount = current_balance
            
            # Calculate interest if overdue
            interest_amount = 0.0
            if days_overdue > 0 and interest_rate > 0:
                daily_rate = calculate_daily_interest_rate(interest_rate)
                interest_amount = calculate_interest_accrued(current_balance, daily_rate, days_overdue)
                payment_amount += interest_amount
            
            if days_overdue == 0:
                print(f"\n💳 Credit card '{name}' payment of {format_currency(payment_amount)} is due today ({today.strftime('%d-%m-%Y')})!")
            else:
                print(f"\n💳 Credit card '{name}' payment of {format_currency(payment_amount)} is {days_overdue} day(s) OVERDUE!")
                if interest_amount > 0:
                    print(f"    Interest accrued: {format_currency(interest_amount)}")
                    print(f"    Total due (with interest): {format_currency(payment_amount)}")
            
            # Ask user if they want to pay now
            print(f"\nOptions for credit card '{name}':")
            print(f"1. Pay now from spendable balance ({format_currency(payment_amount)})")
            print(f"2. Pay now from another credit card balance")
            print("3. Skip for now")
            
            choice = get_choice(
                'Choose an option (1, 2, or 3): ',
                ['1', '2', '3'],
                'Invalid choice. Please enter 1, 2, or 3.',
                input_fn=safe_input
            )
            
            if choice == '1':
                # Pay from spendable balance
                record_credit_card_payment_from_spendable(card, payment_amount)
                print(f"Payment of {format_currency(payment_amount)} recorded from spendable balance.")
            elif choice == '2':
                # Pay from another credit card
                pay_from_another_credit_card(card, payment_amount)
            else:
                print('Payment skipped. You can pay later.')


def record_credit_card_payment_from_spendable(card, amount):
    """Record a credit card payment from spendable balance."""
    (record_id, name, credit_limit, interest_rate, billing_date_day, due_date_day, 
     billing_date_month, due_date_month, current_balance, statement_balance,
     last_billing_date, last_payment_date, status, created_at) = card
    
    today = date.today()
    payment_date = today.strftime('%d-%m-%Y')
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Update credit card balance
    
    new_balance = calculate_updated_credit_card_balance(current_balance, amount)
    
    with db_cursor(CREDIT_CARDS_DB, commit=True) as c:
        c.execute(
            """UPDATE credit_cards SET current_balance=?, last_payment_date=?, 
               last_billing_date=? WHERE id=?""",
            (new_balance, payment_date, payment_date, record_id)
        )
    
    # Record as expense in main storage
    with db_cursor(STORAGE_DB, commit=True) as storage_c:
        storage_c.execute(
            "INSERT INTO storage (amount, category, type, created_at) VALUES (?, ?, ?, ?)",
            (-abs(amount), 'Credit Card Payments', 'expense', created_at)
        )
    
    # Mark all expenses for this card as paid
    with db_cursor(CREDIT_CARD_EXPENSES_DB, commit=True) as c_cc:
        c_cc.execute(
            "UPDATE credit_card_expenses SET is_paid=1, payment_date=? WHERE credit_card_id=? AND is_paid=0",
            (payment_date, record_id)
        )


def pay_from_another_credit_card(source_card, amount):
    """Pay a credit card from another credit card."""
    cards = _fetch_credit_cards()
    active_cards = [card for card in cards if card[12] == 'active' and card[0] != source_card[0]]
    
    if not active_cards:
        print('No other active credit cards available.')
        return
    
    print('\nSelect credit card to pay from:')
    headers = ['ID', 'Name', 'Available Balance']
    card_rows = []
    for card in active_cards:
        card_id, name, credit_limit, interest_rate, billing_day, due_day, billing_month, due_month, current_balance, statement_balance, last_billing, last_payment, status, created = card
        available = credit_limit - current_balance
        card_rows.append([card_id, name, format_currency(available)])
    print_table(headers, card_rows)
    
    target_card_id = get_int_input(
        'Enter credit card ID to pay from: ',
        'Invalid ID.',
        lambda cid: any(card[0] == cid for card in active_cards),
        'No credit card found with that ID.',
        input_fn=safe_input
    )
    
    target_card = next(card for card in active_cards if card[0] == target_card_id)
    target_card_id, target_name, target_limit, target_rate, *_ = target_card
    target_current = target_card[8]
    
    available_balance = target_limit - target_current
    
    if amount > available_balance:
        print(f'Error: Insufficient available balance. Available: {format_currency(available_balance)}, Needed: {format_currency(amount)}')
        return
    
    # Process the payment
    today = date.today()
    payment_date = today.strftime('%d-%m-%Y')
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Update source card balance (the one being paid)
    source_record_id = source_card[0]
    source_new_balance = calculate_updated_credit_card_balance(source_card[8], amount)
    
    
    with db_cursor(CREDIT_CARDS_DB, commit=True) as c:
        c.execute(
            "UPDATE credit_cards SET current_balance=?, last_payment_date=? WHERE id=?",
            (source_new_balance, payment_date, source_record_id)
        )
        
        # Update target card balance (the one paying)
        target_new_balance = target_current + amount
        c.execute(
            "UPDATE credit_cards SET current_balance=? WHERE id=?",
            (target_new_balance, target_card_id)
        )
    
    # Record as expense in main storage
    with db_cursor(STORAGE_DB, commit=True) as storage_c:
        storage_c.execute(
            "INSERT INTO storage (amount, category, type, created_at) VALUES (?, ?, ?, ?)",
            (-abs(amount), 'Credit Card Payments', 'expense', created_at)
        )
    
    # Record the credit card expense
    _insert_credit_card_expense(
        target_card_id,
        target_name,
        amount,
        'Credit Card Payment',
        'Credit Card Payments'
    )
    
    # Mark source card expenses as paid
    with db_cursor(CREDIT_CARD_EXPENSES_DB, commit=True) as c_cc:
        c_cc.execute(
            "UPDATE credit_card_expenses SET is_paid=1, payment_date=? WHERE credit_card_id=? AND is_paid=0",
            (payment_date, source_record_id)
        )
    
    print(f'Payment of {format_currency(amount)} recorded from credit card "{target_name}".')


def make_credit_card_payment():
    """Manually make a credit card payment."""
       
    print('Make Credit Card Payment')
    print('=' * 60)
    
    cards = _fetch_credit_cards()
    active_cards = [card for card in cards if card[12] == 'active']
    
    if not active_cards:
        print('No active credit cards found.')
        return
    
    if not _display_credit_cards(active_cards):
        return
    
    card_id = get_int_input(
        'Enter credit card ID to make payment: ',
        'Invalid ID.',
        lambda cid: any(card[0] == cid for card in active_cards),
        'No credit card found with that ID.',
        input_fn=safe_input
    )
    
    selected_card = next(card for card in active_cards if card[0] == card_id)
    
    (record_id, name, credit_limit, interest_rate, billing_date_day, due_date_day, 
     billing_date_month, due_date_month, current_balance, statement_balance,
     last_billing_date, last_payment_date, status, created_at) = selected_card
    
    if current_balance < 0:
        print(f'Credit card "{name}" already has a credit balance of {format_currency(abs(current_balance))}.')
        return
    
    # Calculate any overdue interest
    today = date.today()
    next_due = get_next_due_date(selected_card)
    
    days_overdue = 0
    interest_amount = 0.0
    
    if next_due and next_due < today and interest_rate > 0:
        days_overdue = (today - next_due).days
        daily_rate = calculate_daily_interest_rate(interest_rate)
        interest_amount = calculate_interest_accrued(current_balance, daily_rate, days_overdue)
    
    total_due = current_balance + interest_amount
    max_payment_amount = get_max_payment_amount(current_balance, interest_amount)
    
    print(f'\nCredit Card: {name}')
    print(f'Current balance: {format_currency(current_balance)}')
    if interest_amount > 0:
        print(f'Interest accrued ({days_overdue} days): {format_currency(interest_amount)}')
    if max_payment_amount is not None:
        print(f'Total due: {format_currency(total_due)}')
    else:
        print('No outstanding balance; any positive payment will create a credit balance.')
    
    # Get payment amount
    payment_input = safe_input(f'Enter payment amount (or press Enter for full payment of {format_currency(total_due)}): ').strip()
    if not payment_input:
        payment_amount = total_due
    else:
        try:
            payment_amount = float(payment_input)
            if payment_amount <= 0:
                print('Payment amount must be greater than 0.')
                return
        except ValueError:
            print('Invalid payment amount.')
            return
    
    if max_payment_amount is not None and payment_amount > max_payment_amount:
        print(f'Payment amount cannot exceed total due. Maximum: {format_currency(max_payment_amount)}')
        return
    
    # Ask where to pay from
    print('\nPay from:')
    print('1. Spendable balance')
    print('2. Another credit card')
    
    pay_from_choice = get_choice(
        'Choose payment source (1 or 2): ',
        ['1', '2'],
        'Invalid choice.',
        input_fn=safe_input
    )
    
    if pay_from_choice == '1':
        record_credit_card_payment_from_spendable(selected_card, payment_amount)
    else:
        pay_from_another_credit_card(selected_card, payment_amount)
    
    print('Payment recorded successfully.')


# Credit Card Expense Integration

def prompt_for_credit_card_expense(amount, expense_type, expense_category):
    """Prompt user to use a credit card for an expense."""
    cards = _fetch_credit_cards()
    active_cards = [card for card in cards if card[12] == 'active']
    
    if not active_cards:
        return False, None
    
    use_credit_card = get_confirmation(
        f'\nWould you like to charge this {expense_type} of {format_currency(amount)} to a credit card? (y/n): ',
        input_fn=safe_input
    )
    
    if not use_credit_card:
        return False, None
    
    print('\nSelect credit card:')
    headers = ['ID', 'Name', 'Available Credit']
    card_rows = []
    for card in active_cards:
        card_id, name, credit_limit, interest_rate, *_ = card
        current_balance = card[8]
        available = credit_limit - current_balance
        card_rows.append([card_id, name, format_currency(available)])
    print_table(headers, card_rows)
    
    card_id = get_int_input(
        'Enter credit card ID: ',
        'Invalid ID.',
        lambda cid: any(card[0] == cid for card in active_cards),
        'No credit card found with that ID.',
        input_fn=safe_input
    )
    
    selected_card = next(card for card in active_cards if card[0] == card_id)
    card_id, card_name, credit_limit, interest_rate, *_ = selected_card
    current_balance = selected_card[8]
    available = credit_limit - current_balance
    
    if amount > available:
        print(f'Warning: This expense exceeds available credit! Available: {format_currency(available)}, Amount: {format_currency(amount)}')
        confirm = get_confirmation(
            'Are you sure you want to proceed? This may cause an over-limit situation. (y/n): ',
            input_fn=safe_input
        )
        if not confirm:
            return False, None
    
    # Update credit card balance
    
    new_balance = current_balance + amount
    with db_cursor(CREDIT_CARDS_DB, commit=True) as c:
        c.execute(
            "UPDATE credit_cards SET current_balance=? WHERE id=?",
            (new_balance, card_id)
        )
    
    # Record the credit card expense
    _insert_credit_card_expense(
        card_id,
        card_name,
        amount,
        expense_type,
        expense_category
    )
    
    return True, card_id


# View Next Payment Amounts

def view_next_credit_card_payments():
    """View upcoming credit card payment amounts."""
       
    print('Next Credit Card Payment Amounts')
    
    cards = _fetch_credit_cards()
    active_cards = [card for card in cards if card[12] == 'active']
    
    if not active_cards:
        print('No active credit cards found.')
        return
    
    today = date.today()
    
    headers = ['ID', 'Name', 'Current Balance', 'Next Due Date', 'Days Until Due', 'Interest Rate', 'Min Payment']
    table_rows = []
    
    for card in active_cards:
        (record_id, name, credit_limit, interest_rate, billing_date_day, due_date_day, 
         billing_date_month, due_date_month, current_balance, statement_balance,
         last_billing_date, last_payment_date, status, created_at) = card
        
        next_due = get_next_due_date(card)
        
        if next_due:
            days_until_due = (next_due - today).days
            due_date_str = next_due.strftime('%d-%m-%Y')
            
            # Calculate minimum payment (typically 1-3% of balance)
            min_payment = current_balance * 0.02  # 2% minimum
            
            if days_until_due < 0:
                due_date_str = f"{due_date_str} (OVERDUE)"
                days_until_due = abs(days_until_due)
            
            table_rows.append([
                record_id,
                name,
                format_currency(current_balance),
                due_date_str,
                days_until_due,
                f"{interest_rate:.2f}%",
                format_currency(min_payment)
            ])
        else:
            table_rows.append([
                record_id,
                name,
                format_currency(current_balance),
                'Unknown',
                'N/A',
                f"{interest_rate:.2f}%",
                format_currency(current_balance * 0.02)
            ])
    
    print_table(headers, table_rows)
    
    # Calculate summary
    total_balance = sum(card[8] for card in active_cards)  # current_balance is at index 8
    total_min_payment = sum(card[8] * 0.02 for card in active_cards)
    
    print(f'\nSummary:')
    print(f'  Total current balance across all cards: {format_currency(total_balance)}')
    print(f'  Total estimated minimum payments: {format_currency(total_min_payment)}')


# Main Management Menu

def manage_credit_cards():
    """Main credit card management menu."""
    while True:
           
        print('Credit Card Management')
        print('=' * 60)
        print('1. Add New Credit Card')
        print('2. Update Credit Card Details')
        print('3. Delete Credit Card')
        print('4. View All Credit Cards')
        print('5. View Next Payment Amounts')
        print('6. Make Credit Card Payment')
        print('7. View Credit Card Expenses')
        print('8. Back to Main Menu')
        
        choice = safe_input('Choose an option (1, 2, 3, 4, 5, 6, 7, or 8): ').strip()
        
        if choice == '1':
            add_credit_card()
        elif choice == '2':
            update_credit_card()
        elif choice == '3':
            delete_credit_card()
        elif choice == '4':
            rows = _fetch_credit_cards()
            _display_credit_cards(rows)
        elif choice == '5':
            view_next_credit_card_payments()
        elif choice == '6':
            make_credit_card_payment()
        elif choice == '7':
            view_credit_card_expenses()
        elif choice == '8':
            return
        else:
            print('Invalid choice. Please enter 1, 2, 3, 4, 5, 6, 7, or 8.')
