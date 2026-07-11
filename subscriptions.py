from datetime import date, datetime, timedelta

from shared import (
    EXPENSE_CATEGORIES,
    STORAGE_DB,
    SUBSCRIPTIONS_DB,
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
    init_subscriptions_db,
    parse_date_ddmmyyyy,
    print_table,
    safe_input,
)


def _format_date(value):
    if isinstance(value, date):
        return value.strftime('%d-%m-%Y')
    return value


def _insert_subscription_record(name, amount, frequency, start_date, category, status='active'):
    conn = init_subscriptions_db()
    c = conn.cursor()
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute(
        """
        INSERT INTO subscriptions (name, amount, frequency, start_date, next_due_date, last_processed_at, category, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (name, amount, frequency, start_date, start_date, None, category, status, created_at)
    )
    conn.commit()
    conn.close()


def add_subscription():
    print('\n' + '=' * 60)
    print('Add Subscription')
    print('=' * 60)
    
    while True:
        name = safe_input('Enter subscription name: ').strip()
        if name:
            break
        print('Subscription name cannot be empty.')

    while True:
        amount_input = safe_input('Enter subscription amount: ').strip()
        try:
            amount = float(amount_input)
        except ValueError:
            print('Invalid amount. Please enter a valid number.')
            continue
        if amount <= 0:
            print('Amount must be greater than 0.')
            continue
        break

    frequency_choice = get_choice(
        'Select frequency:\n1. Yearly\n2. Monthly\n3. Weekly\n4. Daily\nEnter frequency code: ',
        ['1', '2', '3', '4'],
        'Invalid choice. Please enter 1, 2, 3, or 4.',
        input_fn=safe_input
    )
    freq_map = {'1': 'yearly', '2': 'monthly', '3': 'weekly', '4': 'daily'}
    frequency = freq_map[frequency_choice]

    while True:
        start_date_input = safe_input('Enter start date (DD-MM-YYYY): ').strip()
        parsed_date = parse_date_ddmmyyyy(start_date_input)
        if parsed_date is not None:
            start_date = parsed_date
            break
        print('Invalid date. Please use DD-MM-YYYY with a valid day, month, and year.')

    print('Select a subscription type:')
    for code, category_name in EXPENSE_CATEGORIES.items():
        print(f'{code}. {category_name}')

    category_choice = get_choice(
        'Enter category code: ',
        list(EXPENSE_CATEGORIES.keys()),
        'Invalid category code. Please enter one of the listed options.',
        input_fn=safe_input
    )
    category = EXPENSE_CATEGORIES[category_choice]

    _insert_subscription_record(name, amount, frequency, start_date.strftime('%d-%m-%Y'), category)
    print('Subscription added successfully.')


def _fetch_subscriptions():
    with db_cursor(SUBSCRIPTIONS_DB) as c:
        c.execute(
            "SELECT id, name, amount, frequency, start_date, next_due_date, last_processed_at, category, status, created_at FROM subscriptions ORDER BY next_due_date"
        )
        return c.fetchall()


def _display_subscriptions(rows):
    if not rows:
        print('No subscriptions found.')
        return False

    headers = ['ID', 'Name', 'Amount', 'Frequency', 'Next Due', 'Category']
    table_rows = []
    for record_id, name, amount, frequency, start_date, next_due_date, last_processed_at, category, status, created_at in rows:
        table_rows.append([
            record_id,
            name,
            format_currency(amount),
            frequency,
            next_due_date,
            category
        ])
    
    print('\nAvailable subscriptions')
    print_table(headers, table_rows)
    return True


def update_subscription():
    print('\n' + '=' * 60)
    print('Update Subscription')
    print('=' * 60)
    
    rows = _fetch_subscriptions()
    if not _display_subscriptions(rows):
        return

    subscription_id = get_int_input(
        'Enter subscription ID to select: ',
        'Invalid ID. Please enter a valid number.',
        lambda sid: any(row[0] == sid for row in rows),
        'No subscription found with that ID.',
        input_fn=safe_input
    )
    selected_subscription = next(row for row in rows if row[0] == subscription_id)

    record_id, existing_name, existing_amount, existing_frequency, existing_start_date, existing_next_due_date, existing_last_processed_at, existing_category, existing_status, existing_created_at = selected_subscription

    while True:
        print('\nLeave a field blank to keep the current value.')

        name_input = safe_input(f'Edit name [{existing_name}]: ').strip()
        new_name = name_input if name_input else existing_name

        new_amount = get_optional_positive_float(
            f'Edit amount [{format_currency(existing_amount)}]: ',
            existing_amount,
            input_fn=safe_input
        )

        new_frequency = get_optional_choice(
            f'Edit frequency [{existing_frequency}]: ',
            {
                '1': 'yearly', 'yearly': 'yearly',
                '2': 'monthly', 'monthly': 'monthly',
                '3': 'weekly', 'weekly': 'weekly',
                '4': 'daily', 'daily': 'daily'
            },
            existing_frequency,
            'Invalid frequency. Please enter yearly, monthly, weekly, daily, or the corresponding number.',
            input_fn=safe_input
        )

        new_start_date = get_optional_date(
            f'Edit start date [{existing_start_date}] (DD-MM-YYYY): ',
            existing_start_date,
            parse_date_ddmmyyyy,
            '%d-%m-%Y',
            'Invalid date. Please use DD-MM-YYYY with a valid day, month, and year.',
            input_fn=safe_input
        )

        print('Select a category:')
        for code, name in EXPENSE_CATEGORIES.items():
            print(f'{code}. {name}')
        new_category = get_optional_choice(
            f'Edit category [{existing_category}]: ',
            EXPENSE_CATEGORIES,
            existing_category,
            'Invalid category code. Please enter one of the listed options.',
            input_fn=safe_input
        )

        if get_confirmation('Confirm this edit? (y/n): ', input_fn=safe_input):
            with db_cursor(SUBSCRIPTIONS_DB, commit=True) as c:
                c.execute(
                    "UPDATE subscriptions SET name=?, amount=?, frequency=?, start_date=?, next_due_date=?, category=? WHERE id=?",
                    (new_name, new_amount, new_frequency, new_start_date, new_start_date, new_category, record_id)
                )
            print('Subscription updated successfully.')
            return
        else:
            print('Edit cancelled. You can modify the subscription again.')
            continue


def discontinue_subscription():
    print('\n' + '=' * 60)
    print('Discontinue Subscription')
    print('=' * 60)
    
    rows = _fetch_subscriptions()
    if not _display_subscriptions(rows):
        return

    subscription_id = get_int_input(
        'Enter subscription ID to discontinue: ',
        'Invalid ID. Please enter a valid number.',
        lambda sid: any(row[0] == sid for row in rows),
        'No subscription found with that ID.',
        input_fn=safe_input
    )

    confirmation = safe_input('Type y to confirm discontinuation: ').strip().lower()
    if confirmation in {'y', 'yes'}:
        with db_cursor(SUBSCRIPTIONS_DB, commit=True) as c:
            c.execute("UPDATE subscriptions SET status='discontinued' WHERE id=?", (subscription_id,))
        print('Subscription discontinued successfully.')
    else:
        print('Discontinuation cancelled.')


def manage_subscriptions():
    while True:
        print('\n' + '=' * 60)
        print('Manage Subscriptions')
        print('=' * 60)
        print('1. Add New Subscription')
        print('2. Update Existing Subscription')
        print('3. Discontinue Subscription')
        print('4. Back to Main Menu')
        choice = safe_input('Choose an option (1, 2, 3, or 4): ').strip()
        if choice == '1':
            add_subscription()
        elif choice == '2':
            update_subscription()
        elif choice == '3':
            discontinue_subscription()
        elif choice == '4':
            return
        else:
            print('Invalid choice. Please enter 1, 2, 3, or 4.')


def should_prompt_for_due_subscription(due_date, created_at, today=None, pending_due_dates=None):
    if today is None:
        today = date.today()

    if pending_due_dates is None:
        pending_due_dates = [due_date]

    if len(pending_due_dates) > 1:
        return True

    try:
        created_dt = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
    except (TypeError, ValueError):
        return False

    if due_date.year != today.year or due_date.month != today.month:
        return False

    if due_date < created_dt.date():
        return True

    return False


def collect_pending_due_dates(current_due_date, today, frequency):
    if not isinstance(current_due_date, date) or not isinstance(today, date):
        return []

    if current_due_date > today:
        return []

    pending = []
    cursor = current_due_date
    while cursor <= today:
        pending.append(cursor)
        cursor = calculate_next_due_date(cursor, frequency)
    return pending


def process_due_subscriptions():
    with db_cursor(SUBSCRIPTIONS_DB, commit=True) as c:
        c.execute(
            "SELECT id, name, amount, frequency, start_date, next_due_date, category, created_at FROM subscriptions WHERE status = 'active'"
        )
        rows = c.fetchall()

        if not rows:
            return

        today = date.today()
        storage_expenses = []
        subscription_updates = []
        subscription_inserts = []

        for record_id, name, amount, frequency, start_date, next_due_date, category, created_at_value in rows:
            try:
                due_date = date.fromisoformat(next_due_date)
            except (TypeError, ValueError):
                try:
                    due_date = datetime.strptime(next_due_date, '%d-%m-%Y').date()
                except ValueError:
                    continue

            if due_date > today:
                continue

            pending_due_dates = collect_pending_due_dates(due_date, today, frequency)
            if pending_due_dates:
                prompt_for_transaction = should_prompt_for_due_subscription(
                    due_date,
                    created_at_value,
                    today=today,
                    pending_due_dates=pending_due_dates
                )
                if prompt_for_transaction:
                    should_add = safe_input(f"Subscription '{name}' has {len(pending_due_dates)} pending debit(s). Add all pending expenses at once? (y/n): ").strip().lower()
                    should_add_expense = should_add in {'y', 'yes'}
                else:
                    should_add_expense = True

                processing_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if should_add_expense:
                    for pending_due in pending_due_dates:
                        storage_expenses.append((-abs(amount), category, 'expense', processing_time))

                    print(f"Added {len(pending_due_dates)} due expense(s) for subscription '{name}'.")

                    next_due_date_obj = calculate_next_due_date(pending_due_dates[-1], frequency)
                    if next_due_date_obj is None:
                        continue

                    subscription_updates.append((processing_time, record_id))
                    subscription_inserts.append((
                        name, amount, frequency, start_date,
                        next_due_date_obj.strftime('%Y-%m-%d'), None, category, 'active', processing_time
                    ))
                else:
                    subscription_updates.append((processing_time, record_id))
                    print('Subscription skipped. No expense was added.')

        if storage_expenses:
            with db_cursor(STORAGE_DB, commit=True) as storage_c:
                storage_c.executemany(
                    "INSERT INTO storage (amount, category, type, created_at) VALUES (?, ?, ?, ?)",
                    storage_expenses
                )

        for last_processed_at, record_id in subscription_updates:
            c.execute(
                "UPDATE subscriptions SET status='processed', last_processed_at=? WHERE id=?",
                (last_processed_at, record_id)
            )

        if subscription_inserts:
            c.executemany(
                """
                INSERT INTO subscriptions (name, amount, frequency, start_date, next_due_date, last_processed_at, category, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                subscription_inserts
            )
